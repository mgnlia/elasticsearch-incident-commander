from __future__ import annotations

import io
from urllib.error import HTTPError

from app.agent_builder_client import AgentBuilderService
from app.config import Settings
from app.elasticsearch_client import ElasticsearchService
from app.models import AgentStep, IncidentInput, IncidentRunResult


def _settings(**overrides) -> Settings:
    base = {
        "elastic_cloud_id": None,
        "elastic_api_key": None,
        "elastic_url": None,
        "incidents_index": "incidents-logs",
        "logs_index_pattern": "logs-*",
        "metrics_index_pattern": "metrics-*",
        "agent_builder_base_url": None,
        "agent_builder_api_key": None,
        "agent_builder_route": "/api/incident/execute",
        "request_timeout_seconds": 10,
    }
    base.update(overrides)
    return Settings(**base)


def _incident() -> IncidentInput:
    return IncidentInput(
        service="checkout-api",
        severity="high",
        summary="Latency spikes after deploy",
        signals=["p95 latency > 2.5s"],
        recent_deploy_sha="abc123",
    )


def _result() -> IncidentRunResult:
    return IncidentRunResult(
        incident_id="incident-1",
        service="checkout-api",
        severity="high",
        status="investigating",
        timeline=[
            AgentStep(agent="triage", action="classify", output={}),
            AgentStep(agent="diagnosis", action="hypothesis", output={}),
            AgentStep(agent="remediation", action="rollback", output={}),
            AgentStep(agent="communication", action="update", output={}),
        ],
        recommendation="Rollback and monitor",
        stakeholder_update="Investigating checkout-api",
    )


def test_elasticsearch_phase_error_create_index(monkeypatch) -> None:
    settings = _settings(elastic_cloud_id="cluster:abc", elastic_api_key="token")
    service = ElasticsearchService(settings)

    class _Client:
        def ping(self) -> bool:
            return True

    service.client = _Client()

    def _raise_create_index():
        raise RuntimeError("create failed")

    monkeypatch.setattr(service, "_ensure_index", _raise_create_index)

    report = service.record_incident_and_analyze(_incident(), _result())

    assert report["status"] == "error"
    assert report["phase"] == "create_index"
    assert "create failed" in report["error"]


def test_elasticsearch_phase_error_esql_query(monkeypatch) -> None:
    settings = _settings(elastic_cloud_id="cluster:abc", elastic_api_key="token")
    service = ElasticsearchService(settings)

    class _Client:
        def ping(self) -> bool:
            return True

    service.client = _Client()
    monkeypatch.setattr(service, "_ensure_index", lambda: {"acknowledged": True})
    monkeypatch.setattr(service, "_index_incident", lambda incident, result: {"result": "created"})
    monkeypatch.setattr(service, "_search_recent", lambda service_name: {"hits": {"hits": []}})

    def _raise_esql(_service_name: str, _severity: str):
        raise RuntimeError("esql failed")

    monkeypatch.setattr(service, "_run_esql", _raise_esql)

    report = service.record_incident_and_analyze(_incident(), _result())

    assert report["status"] == "error"
    assert report["phase"] == "esql_query"
    assert "esql failed" in report["error"]


def test_agent_builder_invalid_base_url_reported() -> None:
    settings = _settings(
        agent_builder_base_url="agent-builder.internal",
        agent_builder_api_key="token",
    )
    service = AgentBuilderService(settings)

    report = service.dispatch_incident(_incident(), _result())

    assert report["enabled"] is True
    assert report["status"] == "error"
    assert report["reason"] == "invalid_agent_builder_base_url"
    assert report["integration_path"] == "/api/incident/execute"


def test_agent_builder_http_error_body_truncated(monkeypatch) -> None:
    settings = _settings(
        agent_builder_base_url="https://agent-builder.example.com",
        agent_builder_api_key="token",
    )
    service = AgentBuilderService(settings)

    long_body = "x" * 700

    def _fake_urlopen(req, timeout):
        raise HTTPError(
            req.full_url,
            502,
            "bad gateway",
            hdrs=None,
            fp=io.BytesIO(long_body.encode("utf-8")),
        )

    monkeypatch.setattr("app.agent_builder_client.request.urlopen", _fake_urlopen)

    report = service.dispatch_incident(_incident(), _result())

    assert report["status"] == "error"
    assert report["response_status"] == 502
    assert report["error"] == "bad gateway"
    assert report["error_body"].endswith("...")
    assert len(report["error_body"]) == 503


def test_agent_builder_success_reports_payload_bytes(monkeypatch) -> None:
    settings = _settings(
        agent_builder_base_url="https://agent-builder.example.com",
        agent_builder_api_key="token",
        request_timeout_seconds=13,
    )
    service = AgentBuilderService(settings)

    class _Response:
        status = 201

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    def _fake_urlopen(req, timeout):
        assert timeout == 13
        return _Response()

    monkeypatch.setattr("app.agent_builder_client.request.urlopen", _fake_urlopen)

    report = service.dispatch_incident(_incident(), _result())

    assert report["status"] == "ok"
    assert report["response_status"] == 201
    assert report["timeout_seconds"] == 13
    assert report["payload_bytes"] > 0
