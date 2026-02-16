from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    elastic_cloud_id: str | None
    elastic_api_key: str | None
    elastic_url: str | None
    incidents_index: str
    logs_index_pattern: str
    metrics_index_pattern: str
    agent_builder_base_url: str | None
    agent_builder_api_key: str | None
    agent_builder_route: str
    request_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            elastic_cloud_id=os.getenv("ELASTIC_CLOUD_ID"),
            elastic_api_key=os.getenv("ELASTIC_API_KEY"),
            elastic_url=os.getenv("ELASTIC_URL"),
            incidents_index=os.getenv("ELASTIC_INCIDENTS_INDEX", "incidents-logs"),
            logs_index_pattern=os.getenv("ELASTIC_LOGS_PATTERN", "logs-*"),
            metrics_index_pattern=os.getenv("ELASTIC_METRICS_PATTERN", "metrics-*"),
            agent_builder_base_url=os.getenv("AGENT_BUILDER_BASE_URL"),
            agent_builder_api_key=os.getenv("AGENT_BUILDER_API_KEY"),
            agent_builder_route=os.getenv("AGENT_BUILDER_ROUTE", "/api/incident/execute"),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10")),
        )

    @property
    def elastic_enabled(self) -> bool:
        return bool(self.elastic_api_key and (self.elastic_cloud_id or self.elastic_url))

    @property
    def agent_builder_enabled(self) -> bool:
        return bool(self.agent_builder_base_url and self.agent_builder_api_key)
