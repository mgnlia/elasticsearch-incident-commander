from __future__ import annotations

from urllib.error import HTTPError

from app.agent_builder_client import AgentBuilderService
from app.config import Settings
from app.elasticsearch_client import ElasticsearchService
from app.models import AgentStep, IncidentInput, IncidentRunResult


class _FakeIndices:
    def __init__(self) -> None:
        self.created_with: dict | None = None

    def create(self, **kwargs):
        self.created_with = kwargs
        return {"acknowledged": True, "index": kwargs["index"]}


class _FakeEsql:
    def __init__(self) -> None:
        self.last_query: dict | None = None

    def query(self, **kwargs):
        self.last_query = kwargs
        return {
            "columns": [{"name": "incident_count", "type": "long"}],
            "values": [[1]],
        }


class _FakeElasticClient:
    def __init__(self) -> None:
        self.indices = _FakeIndices()
        self.esql = _FakeEsql()
        self.ignore_status: int | None = None

    def ping(self) -> bool:
        return True

    def options(self, ignore_status: int):
        self.ignore_status = ignore_status
        return self

    def index(self, **kwargs):
        return {"result": "created", "_id": kwargs["id"]}

    def search(self, **kwargs):
        return {
            "hits": {
                "hits": [
                    {"_source": {"incident_id": "incident-1"}},
                ]
            }
        }


def _sample_incident() -> IncidentInput:
    return IncidentInput(
        service="checkout-api",
        severity="high",
        summary="Latency spikes after deploy",
        signals=["p95 latency > 2.5s"],
        recent_deploy_sha="abc123",
    )


def _sample_result() -> IncidentRunResult:
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


def test_elasticsearch_service_runs_create_index_search_esql() -> None:
    settings = Settings(
        elastic_cloud_id="cluster:xxxx",
        elastic_api_key="api-key",
        elastic_url=None,
        incidents_index="incidents-logs",
        logs_index_pattern="logs-*",
        metrics_index_pattern="metrics-*",
        agent_builder_base_url=None,
        agent_builder_api_key=None,
        agent_builder_route="/api/incident/execute",
        request_timeout_seconds=10,
    )

    service = ElasticsearchService(settings)
    fake_client = _FakeElasticClient()
    service.client = fake_client

    report = service.record_incident_and_analyze(_sample_incident(), _sample_result())

    assert report["status"] == "ok"
    assert report["enabled"] is True
    assert report["index"] == "incidents-logs"
    assert fake_client.ignore_status == 400
    assert fake_client.indices.created_with is not None
    assert fake_client.indices.created_with["index"] == "incidents-logs"
    assert report["create_result"]["acknowledged"] is True
    assert report["index_result"]["result"] == "created"
    assert report["search"]["hit_count"] == 1
    assert report["esql"]["values"] == [[1]]
    assert fake_client.esql.last_query is not None
    assert "FROM incidents-logs" in fake_client.esql.last_query["query"]


def test_elasticsearch_service_skips_when_not_configured() -> None:
    settings = Settings(
        elastic_cloud_id=None,
        elastic_api_key=None,
        elastic_url=None,
        incidents_index="incidents-logs",
        logs_index_pattern="logs-*",
        metrics_index_pattern="metrics-*",
        agent_builder_base_url=None,
        agent_builder_api_key=None,
        agent_builder_route="/api/incident/execute",
        request_timeout_seconds=10,
    )
    service = ElasticsearchService(settings)

    report = service.record_incident_and_analyze(_sample_incident(), _sample_result())

    assert report == {
        "enabled": False,
        "status": "skipped",
        "reason": "elastic_not_configured",
    }


def test_agent_builder_dispatch_success(monkeypatch) -> None:
    settings = Settings(
        elastic_cloud_id=None,
        elastic_api_key=None,
        elastic_url=None,
        incidents_index="incidents-logs",
        logs_index_pattern="logs-*",
        metrics_index_pattern="metrics-*",
        agent_builder_base_url="https://agent-builder.example.com",
        agent_builder_api_key="token-123",
        agent_builder_route="/api/incident/execute",
        request_timeout_seconds=10,
    )

    captured: dict = {}

    class _Response:
        status = 202

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

    def _fake_urlopen(req, timeout):
        headers = {k.lower(): v for k, v in req.header_items()}
        captured["full_url"] = req.full_url
        captured["timeout"] = timeout
        captured["auth"] = headers.get("authorization")
        captured["content_type"] = headers.get("content-type")
        return _Response()

    monkeypatch.setattr("app.agent_builder_client.request.urlopen", _fake_urlopen)

    service = AgentBuilderService(settings)
    report = service.dispatch_incident(_sample_incident(), _sample_result())

    assert report["status"] == "ok"
    assert report["enabled"] is True
    assert report["response_status"] == 202
    assert captured["full_url"] == "https://agent-builder.example.com/api/incident/execute"
    assert captured["timeout"] == 10
    assert captured["auth"] == "Bearer token-123"
    assert captured["content_type"] == "application/json"


def test_agent_builder_dispatch_http_error(monkeypatch) -> None:
    settings = Settings(
        elastic_cloud_id=None,
        elastic_api_key=None,
        elastic_url=None,
        incidents_index="incidents-logs",
        logs_index_pattern="logs-*",
        metrics_index_pattern="metrics-*",
        agent_builder_base_url="https://agent-builder.example.com",
        agent_builder_api_key="token-123",
        agent_builder_route="/api/incident/execute",
        request_timeout_seconds=10,
    )

    def _fake_urlopen(req, timeout):
        raise HTTPError(req.full_url, 503, "service unavailable", hdrs=None, fp=None)

    monkeypatch.setattr("app.agent_builder_client.request.urlopen", _fake_urlopen)

    service = AgentBuilderService(settings)
    report = service.dispatch_incident(_sample_incident(), _sample_result())

    assert report["status"] == "error"
    assert report["response_status"] == 503
    assert report["integration_path"] == "/api/incident/execute"
