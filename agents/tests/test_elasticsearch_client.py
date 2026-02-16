from __future__ import annotations

from app.config import Settings
from app.elasticsearch_client import ElasticsearchService
from app.models import IncidentInput, IncidentRunResult


class FakeOptionsClient:
    def __init__(self, parent: "FakeElasticsearchClient") -> None:
        self.parent = parent
        self.indices = self

    def create(self, index, mappings):
        self.parent.calls.append("indices.create")
        if self.parent.raise_on == "create_index":
            raise RuntimeError("create failed")
        return {"acknowledged": True, "index": index}


class FakeEsqlClient:
    def __init__(self, parent: "FakeElasticsearchClient") -> None:
        self.parent = parent

    def query(self, query, params):
        self.parent.calls.append("esql.query")
        if self.parent.raise_on == "esql_query":
            raise RuntimeError("esql failed")
        return {
            "columns": [{"name": "incident_count", "type": "long"}],
            "values": [[1]],
        }


class FakeElasticsearchClient:
    def __init__(self, *, ping_ok=True, raise_on: str | None = None) -> None:
        self.ping_ok = ping_ok
        self.raise_on = raise_on
        self.calls: list[str] = []
        self.esql = FakeEsqlClient(self)

    def ping(self):
        self.calls.append("ping")
        if self.raise_on == "ping":
            raise RuntimeError("ping failed")
        return self.ping_ok

    def options(self, ignore_status=()):
        self.calls.append("options")
        return FakeOptionsClient(self)

    def index(self, index, id, document, refresh):
        self.calls.append("index")
        if self.raise_on == "index_document":
            raise RuntimeError("index failed")
        return {"result": "created", "_id": id}

    def search(self, index, size, query, sort):
        self.calls.append("search")
        if self.raise_on == "search_recent":
            raise RuntimeError("search failed")
        return {
            "hits": {
                "hits": [
                    {"_source": {"incident_id": "inc-1"}},
                    {"_source": {"incident_id": None}},
                ]
            }
        }


def make_settings() -> Settings:
    return Settings(
        elastic_cloud_id=None,
        elastic_api_key="secret",
        elastic_url="http://localhost:9200",
        incidents_index="incidents-logs",
        logs_index_pattern="logs-*",
        metrics_index_pattern="metrics-*",
        agent_builder_base_url=None,
        agent_builder_api_key=None,
        agent_builder_route="/api/incident/execute",
        request_timeout_seconds=5,
    )


def make_incident_and_result() -> tuple[IncidentInput, IncidentRunResult]:
    incident = IncidentInput(
        service="checkout-api",
        severity="high",
        summary="Latency spikes after deploy",
        signals=["p95 latency > 2.5s"],
        recent_deploy_sha="abc1234",
    )
    result = IncidentRunResult(
        incident_id="inc-123",
        service="checkout-api",
        severity="high",
        status="investigating",
        timeline=[],
        recommendation="Rollback and verify",
        stakeholder_update="Investigating",
    )
    return incident, result


def test_returns_skipped_when_not_configured() -> None:
    settings = make_settings()
    settings = Settings(
        elastic_cloud_id=None,
        elastic_api_key=None,
        elastic_url=None,
        incidents_index=settings.incidents_index,
        logs_index_pattern=settings.logs_index_pattern,
        metrics_index_pattern=settings.metrics_index_pattern,
        agent_builder_base_url=settings.agent_builder_base_url,
        agent_builder_api_key=settings.agent_builder_api_key,
        agent_builder_route=settings.agent_builder_route,
        request_timeout_seconds=settings.request_timeout_seconds,
    )
    service = ElasticsearchService(settings)
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "skipped"
    assert response["reason"] == "elastic_not_configured"


def test_success_path_includes_integration_artifacts() -> None:
    service = ElasticsearchService(make_settings())
    service.client = FakeElasticsearchClient()
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "ok"
    assert response["create_result"]["acknowledged"] is True
    assert response["index_result"]["_id"] == "inc-123"
    assert response["search"]["latest_incident_ids"] == ["inc-1"]
    assert response["esql"]["values"] == [[1]]


def test_ping_false_reports_phase() -> None:
    service = ElasticsearchService(make_settings())
    service.client = FakeElasticsearchClient(ping_ok=False)
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "error"
    assert response["phase"] == "ping"
    assert "elastic_ping_failed" in response["error"]


def test_create_index_error_reports_phase() -> None:
    service = ElasticsearchService(make_settings())
    service.client = FakeElasticsearchClient(raise_on="create_index")
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "error"
    assert response["phase"] == "create_index"
    assert "create failed" in response["error"]


def test_index_error_reports_phase() -> None:
    service = ElasticsearchService(make_settings())
    service.client = FakeElasticsearchClient(raise_on="index_document")
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "error"
    assert response["phase"] == "index_document"


def test_search_error_reports_phase() -> None:
    service = ElasticsearchService(make_settings())
    service.client = FakeElasticsearchClient(raise_on="search_recent")
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "error"
    assert response["phase"] == "search_recent"


def test_esql_error_reports_phase() -> None:
    service = ElasticsearchService(make_settings())
    service.client = FakeElasticsearchClient(raise_on="esql_query")
    incident, result = make_incident_and_result()

    response = service.record_incident_and_analyze(incident, result)

    assert response["status"] == "error"
    assert response["phase"] == "esql_query"
