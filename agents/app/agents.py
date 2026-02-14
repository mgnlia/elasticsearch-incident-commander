from __future__ import annotations

import uuid
from dataclasses import dataclass

from .models import IncidentInput, AgentStep, IncidentRunResult


@dataclass
class TriageAgent:
    name: str = "triage"

    def run(self, incident: IncidentInput) -> AgentStep:
        confidence = "high" if incident.severity in {"high", "critical"} else "medium"
        suspects = ["recent_deploy"] if incident.recent_deploy_sha else ["traffic_spike"]
        return AgentStep(
            agent=self.name,
            action="classify_incident",
            output={
                "confidence": confidence,
                "suspects": suspects,
                "priority": incident.severity,
            },
        )


@dataclass
class DiagnosisAgent:
    name: str = "diagnosis"

    def run(self, incident: IncidentInput, triage: AgentStep) -> AgentStep:
        hypothesis = (
            "Regression introduced in recent deploy"
            if "recent_deploy" in triage.output.get("suspects", [])
            else "Capacity saturation due to abnormal traffic"
        )
        query_plan = [
            "FROM logs-* | WHERE service == ? AND @timestamp > NOW()-15m",
            "FROM metrics-* | STATS p95=percentile(latency_ms,95) BY service",
        ]
        return AgentStep(
            agent=self.name,
            action="generate_root_cause_hypothesis",
            output={
                "hypothesis": hypothesis,
                "query_plan": query_plan,
                "signals_seen": incident.signals,
            },
        )


@dataclass
class RemediationAgent:
    name: str = "remediation"

    def run(self, incident: IncidentInput, diagnosis: AgentStep) -> AgentStep:
        if incident.severity in {"high", "critical"}:
            action = "rollback_latest_deploy"
            risk = "medium"
        else:
            action = "scale_service_replicas"
            risk = "low"

        return AgentStep(
            agent=self.name,
            action="propose_runbook_action",
            output={
                "runbook_action": action,
                "risk": risk,
                "justification": diagnosis.output.get("hypothesis", "insufficient data"),
            },
        )


@dataclass
class CommunicationAgent:
    name: str = "communication"

    def run(self, incident: IncidentInput, remediation: AgentStep) -> AgentStep:
        update = (
            f"Investigating {incident.service}. Applied action: "
            f"{remediation.output.get('runbook_action')}."
        )
        return AgentStep(
            agent=self.name,
            action="compose_stakeholder_update",
            output={
                "channel": "#incidents",
                "message": update,
                "next_update_eta_min": 15,
            },
        )


class IncidentWorkflow:
    def __init__(self) -> None:
        self.triage = TriageAgent()
        self.diagnosis = DiagnosisAgent()
        self.remediation = RemediationAgent()
        self.communication = CommunicationAgent()

    def run(self, incident: IncidentInput) -> IncidentRunResult:
        step_1 = self.triage.run(incident)
        step_2 = self.diagnosis.run(incident, step_1)
        step_3 = self.remediation.run(incident, step_2)
        step_4 = self.communication.run(incident, step_3)

        status = "mitigated" if incident.severity in {"low", "medium"} else "investigating"
        recommendation = (
            f"Execute {step_3.output.get('runbook_action')} and validate latency/error recovery over 10 minutes."
        )

        return IncidentRunResult(
            incident_id=str(uuid.uuid4()),
            service=incident.service,
            severity=incident.severity,
            status=status,
            timeline=[step_1, step_2, step_3, step_4],
            recommendation=recommendation,
            stakeholder_update=step_4.output.get("message", ""),
        )
