from __future__ import annotations

from io import BytesIO
from urllib import error

import app.agent_builder_client as agent_builder_module
from app.agent_builder_client import AgentBuilderService
from app.agents import IncidentWorkflow
from app.config import Settings
from app.models import IncidentInput


def make_settings(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    route: str = "/api/incident/execute",
) -> Settings:
    return Settings(
        elastic_cloud_id=None,
        elastic_api_key=None,
        elastic_url=None,
        incidents_index="incidents-logs",
        logs_index_pattern="logs-*",
        metrics_index_pattern="metrics-*",
        agent_builder_base_url=base_url,
        agent_builder_api_key=api_key,
        agent_builder_route=route,
        request_timeout_seconds=3,
    )


def make_incident_and_result() -> tuple[IncidentInput, object]:
    incident = IncidentInput(
        service="checkout-api",
        severity="high",
        summary="Latency spikes after deploy",
        signals=["p95 latency > 2.5s"],
        recent_deploy_sha="abc1234",
    )
    result = IncidentWorkflow().run(incident)
    return incident, result


def test_dispatch_skips_when_not_configured() -> None:
    service = AgentBuilderService(make_settings())
    incident, result = make_incident_and_result()

    response = service.dispatch_incident(incident, result)

    assert response["enabled"] is False
    assert response["status"] == "skipped"
    assert response["reason"] == "agent_builder_not_configured"


def test_dispatch_returns_error_for_invalid_base_url() -> None:
    service = AgentBuilderService(make_settings(base_url="not-a-url", api_key="secret"))
    incident, result = make_incident_and_result()

    response = service.dispatch_incident(incident, result)

    assert response["enabled"] is True
    assert response["status"] == "error"
    assert response["reason"] == "invalid_agent_builder_base_url"


def test_dispatch_success_reports_payload_size(monkeypatch) -> None:
    service = AgentBuilderService(make_settings(base_url="https://agent-builder.local", api_key="secret"))
    incident, result = make_incident_and_result()

    class DummyResponse:
        status = 202

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(agent_builder_module.request, "urlopen", lambda req, timeout: DummyResponse())

    response = service.dispatch_incident(incident, result)

    assert response["status"] == "ok"
    assert response["response_status"] == 202
    assert response["timeout_seconds"] == 3
    assert response["payload_bytes"] > 0


def test_dispatch_http_error_includes_truncated_body(monkeypatch) -> None:
    service = AgentBuilderService(make_settings(base_url="https://agent-builder.local", api_key="secret"))
    incident, result = make_incident_and_result()

    long_body = ("x" * 650).encode("utf-8")

    def raise_http_error(req, timeout):
        raise error.HTTPError(
            url="https://agent-builder.local/api/incident/execute",
            code=502,
            msg="Bad Gateway",
            hdrs=None,
            fp=BytesIO(long_body),
        )

    monkeypatch.setattr(agent_builder_module.request, "urlopen", raise_http_error)

    response = service.dispatch_incident(incident, result)

    assert response["status"] == "error"
    assert response["response_status"] == 502
    assert response["error"] == "Bad Gateway"
    assert response["error_body"].endswith("...")
    assert len(response["error_body"]) <= 503


def test_dispatch_url_error_is_reported(monkeypatch) -> None:
    service = AgentBuilderService(make_settings(base_url="https://agent-builder.local", api_key="secret"))
    incident, result = make_incident_and_result()

    def raise_url_error(req, timeout):
        raise error.URLError("connection refused")

    monkeypatch.setattr(agent_builder_module.request, "urlopen", raise_url_error)

    response = service.dispatch_incident(incident, result)

    assert response["status"] == "error"
    assert "connection_error" in response["error"]
