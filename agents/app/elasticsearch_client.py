from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from elasticsearch import Elasticsearch

from .config import Settings
from .models import IncidentInput, IncidentRunResult


class ElasticsearchService:
    """Handles Elastic Cloud indexing, search, and ES|QL execution for incidents."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = self._build_client() if settings.elastic_enabled else None

    def _build_client(self) -> Elasticsearch:
        if self.settings.elastic_cloud_id:
            return Elasticsearch(
                cloud_id=self.settings.elastic_cloud_id,
                api_key=self.settings.elastic_api_key,
                request_timeout=self.settings.request_timeout_seconds,
            )

        return Elasticsearch(
            hosts=[self.settings.elastic_url],
            api_key=self.settings.elastic_api_key,
            request_timeout=self.settings.request_timeout_seconds,
        )

    @staticmethod
    def _body(response: Any) -> dict[str, Any]:
        if isinstance(response, dict):
            return response
        body = getattr(response, "body", None)
        return body if isinstance(body, dict) else {}

    @staticmethod
    def _error_response(started: float, phase: str, exc: Exception | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "enabled": True,
            "status": "error",
            "phase": phase,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }
        if exc is not None:
            payload["error"] = str(exc)
        return payload

    def _ensure_index(self) -> dict[str, Any]:
        assert self.client is not None
        response = self.client.options(ignore_status=400).indices.create(
            index=self.settings.incidents_index,
            mappings={
                "properties": {
                    "incident_id": {"type": "keyword"},
                    "service": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "summary": {"type": "text"},
                    "status": {"type": "keyword"},
                    "signals": {"type": "keyword"},
                    "recommendation": {"type": "text"},
                    "stakeholder_update": {"type": "text"},
                    "created_at": {"type": "date"},
                }
            },
        )
        return self._body(response)

    def _index_incident(
        self,
        incident: IncidentInput,
        result: IncidentRunResult,
    ) -> dict[str, Any]:
        assert self.client is not None

        document = {
            "incident_id": result.incident_id,
            "service": incident.service,
            "severity": incident.severity,
            "summary": incident.summary,
            "status": result.status,
            "signals": incident.signals,
            "recommendation": result.recommendation,
            "stakeholder_update": result.stakeholder_update,
            "created_at": datetime.now(UTC).isoformat(),
        }

        response = self.client.index(
            index=self.settings.incidents_index,
            id=result.incident_id,
            document=document,
            refresh="wait_for",
        )
        return self._body(response)

    def _search_recent(self, service: str) -> dict[str, Any]:
        assert self.client is not None
        response = self.client.search(
            index=self.settings.incidents_index,
            size=5,
            query={"term": {"service": {"value": service}}},
            sort=[{"created_at": {"order": "desc"}}],
        )
        return self._body(response)

    def _run_esql(self, service: str, severity: str) -> dict[str, Any]:
        assert self.client is not None
        response = self.client.esql.query(
            query=(
                f"FROM {self.settings.incidents_index} "
                "| WHERE service == ? AND severity == ? "
                "| STATS incident_count = COUNT(*)"
            ),
            params=[service, severity],
        )
        return self._body(response)

    def record_incident_and_analyze(
        self,
        incident: IncidentInput,
        result: IncidentRunResult,
    ) -> dict[str, Any]:
        if not self.client:
            return {
                "enabled": False,
                "status": "skipped",
                "reason": "elastic_not_configured",
            }

        started = perf_counter()

        try:
            ping_ok = self.client.ping()
        except Exception as exc:  # pragma: no cover - defensive path
            return self._error_response(started, "ping", exc)

        if not ping_ok:
            return self._error_response(started, "ping", Exception("elastic_ping_failed"))

        try:
            create_result = self._ensure_index()
        except Exception as exc:
            return self._error_response(started, "create_index", exc)

        try:
            index_result = self._index_incident(incident, result)
        except Exception as exc:
            return self._error_response(started, "index_document", exc)

        try:
            search_result = self._search_recent(incident.service)
        except Exception as exc:
            return self._error_response(started, "search_recent", exc)

        try:
            esql_result = self._run_esql(incident.service, incident.severity)
        except Exception as exc:
            return self._error_response(started, "esql_query", exc)

        hits = search_result.get("hits", {}).get("hits", [])
        latest_incident_ids = [
            hit.get("_source", {}).get("incident_id")
            for hit in hits
            if hit.get("_source", {}).get("incident_id")
        ]

        return {
            "enabled": True,
            "status": "ok",
            "index": self.settings.incidents_index,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "create_result": {
                "acknowledged": create_result.get("acknowledged"),
                "index": create_result.get("index", self.settings.incidents_index),
            },
            "index_result": {
                "result": index_result.get("result"),
                "_id": index_result.get("_id"),
            },
            "search": {
                "hit_count": len(hits),
                "latest_incident_ids": latest_incident_ids,
            },
            "esql": {
                "query": (
                    f"FROM {self.settings.incidents_index} "
                    "| WHERE service == ? AND severity == ? "
                    "| STATS incident_count = COUNT(*)"
                ),
                "columns": esql_result.get("columns", []),
                "values": esql_result.get("values", []),
            },
        }
