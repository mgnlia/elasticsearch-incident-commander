from pydantic import BaseModel, Field
from typing import Literal

Severity = Literal["low", "medium", "high", "critical"]


class IncidentInput(BaseModel):
    service: str = Field(min_length=2, max_length=80)
    severity: Severity
    summary: str = Field(min_length=5, max_length=240)
    signals: list[str] = Field(default_factory=list)
    recent_deploy_sha: str | None = Field(default=None, max_length=40)


class AgentStep(BaseModel):
    agent: str
    action: str
    output: dict


class IncidentRunResult(BaseModel):
    incident_id: str
    service: str
    severity: Severity
    status: Literal["open", "investigating", "mitigated"]
    timeline: list[AgentStep]
    recommendation: str
    stakeholder_update: str
