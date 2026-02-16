from __future__ import annotations

from typing import Any
from urllib import error, parse, request

from .config import Settings
from .models import IncidentInput, IncidentRunResult


class AgentBuilderService:
    """Sends incident context to an external Agent Builder endpoint when configured."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def dispatch_incident(
        self,
        incident: IncidentInput,
        result: IncidentRunResult,
    ) -> dict[str, Any]:
        if not self.settings.agent_builder_enabled:
            return {
                "enabled": False,
                "status": "skipped",
                "reason": "agent_builder_not_configured",
                "integration_path": self.settings.agent_builder_route,
            }

        base = self.settings.agent_builder_base_url.rstrip("/")
        route = self.settings.agent_builder_route
        if not route.startswith("/"):
            route = f"/{route}"
        endpoint = f"{base}{route}"

        payload = {
            "incident": incident.model_dump(),
            "workflow": result.model_dump(exclude={"elastic", "agent_builder"}),
        }

        req = request.Request(
            endpoint,
            data=parse.urlencode({"payload": str(payload)}).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.settings.agent_builder_api_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        try:
            with request.urlopen(req, timeout=self.settings.request_timeout_seconds) as resp:
                return {
                    "enabled": True,
                    "status": "ok",
                    "endpoint": endpoint,
                    "response_status": resp.status,
                    "integration_path": self.settings.agent_builder_route,
                }
        except error.HTTPError as exc:
            return {
                "enabled": True,
                "status": "error",
                "endpoint": endpoint,
                "response_status": exc.code,
                "error": exc.reason,
                "integration_path": self.settings.agent_builder_route,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return {
                "enabled": True,
                "status": "error",
                "endpoint": endpoint,
                "error": str(exc),
                "integration_path": self.settings.agent_builder_route,
            }
