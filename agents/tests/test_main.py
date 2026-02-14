import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_incident_workflow_contract() -> None:
    payload = {
        "service": "checkout-api",
        "severity": "high",
        "summary": "Latency spikes after deploy",
        "signals": ["p95 latency > 2.5s", "error rate 7%"],
        "recent_deploy_sha": "abc1234",
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    body = response.json()
    uuid.UUID(body["incident_id"])
    assert body["service"] == payload["service"]
    assert body["severity"] == payload["severity"]
    assert body["status"] == "investigating"
    assert len(body["timeline"]) == 4
    assert [step["agent"] for step in body["timeline"]] == [
        "triage",
        "diagnosis",
        "remediation",
        "communication",
    ]


def test_critical_incident_triggers_rollback_action() -> None:
    payload = {
        "service": "inventory-api",
        "severity": "critical",
        "summary": "Error budget burn accelerating",
        "signals": ["error rate 15%", "p99 latency > 4s"],
        "recent_deploy_sha": "def5678",
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    remediation_step = response.json()["timeline"][2]
    assert remediation_step["agent"] == "remediation"
    assert remediation_step["output"]["runbook_action"] == "rollback_latest_deploy"
    assert remediation_step["output"]["risk"] == "medium"


def test_invalid_incident_payload_rejected() -> None:
    invalid_payload = {
        "service": "x",
        "severity": "high",
        "summary": "bad",
        "signals": [],
    }

    response = client.post("/incidents/run", json=invalid_payload)
    assert response.status_code == 422
