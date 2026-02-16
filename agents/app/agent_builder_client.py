from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from .config import Settings
from .models import IncidentInput, IncidentRunResult

MAX_ERROR_BODY_CHARS = 500


class AgentBuilderService:
    """Sends incident context to an external Agent Builder endpoint when configured."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def _truncate(value: str, max_chars: int = MAX_ERROR_BODY_CHARS) -> str:
        if len(value) <= max_chars:
            return value
        return f"{value[:max_chars]}..."

    def _build_endpoint(self) -> tuple[str | None, str | None]:
        base_url = (self.settings.agent_builder_base_url or "").strip()
        if not base_url:
            return None, "agent_builder_not_configured"

        parsed = parse.urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None, "invalid_agent_builder_base_url"

        route = self.settings.agent_builder_route.strip() or "/"
        if not route.startswith("/"):
            route = f"/{route}"

        return f"{base_url.rstrip('/')}{route}", None

    def dispatch_incident(
        self,
        incident: IncidentInput,
        result: IncidentRunResult,
    ) -> dict[str, Any]:
        endpoint, endpoint_error = self._build_endpoint()

        if not self.settings.agent_builder_enabled:
            return {
                "enabled": False,
                "status": "skipped",
                "reason": "agent_builder_not_configured",
                "integration_path": self.settings.agent_builder_route,
            }

        if endpoint_error or not endpoint:
            return {
                "enabled": True,
                "status": "error",
                "reason": endpoint_error or "invalid_agent_builder_endpoint",
                "integration_path": self.settings.agent_builder_route,
            }

        payload = {
            "incident": incident.model_dump(),
            "workflow": result.model_dump(exclude={"elastic", "agent_builder"}),
        }
        payload_bytes = json.dumps(payload).encode("utf-8")

        req = request.Request(
            endpoint,
            data=payload_bytes,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.settings.agent_builder_api_key}",
                "Content-Type": "application/json",
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
                    "timeout_seconds": self.settings.request_timeout_seconds,
                    "payload_bytes": len(payload_bytes),
                }
        except error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                error_body = ""

            response: dict[str, Any] = {
                "enabled": True,
                "status": "error",
                "endpoint": endpoint,
                "response_status": exc.code,
                "error": str(exc.reason),
                "integration_path": self.settings.agent_builder_route,
                "timeout_seconds": self.settings.request_timeout_seconds,
            }
            if error_body:
                response["error_body"] = self._truncate(error_body)
            return response
        except error.URLError as exc:
            return {
                "enabled": True,
                "status": "error",
                "endpoint": endpoint,
                "error": f"connection_error: {exc.reason}",
                "integration_path": self.settings.agent_builder_route,
                "timeout_seconds": self.settings.request_timeout_seconds,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return {
                "enabled": True,
                "status": "error",
                "endpoint": endpoint,
                "error": str(exc),
                "integration_path": self.settings.agent_builder_route,
                "timeout_seconds": self.settings.request_timeout_seconds,
            }
