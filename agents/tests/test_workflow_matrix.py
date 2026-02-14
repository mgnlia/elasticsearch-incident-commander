from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_medium_incident_uses_capacity_playbook_and_mitigates() -> None:
    payload = {
        "service": "search-api",
        "severity": "medium",
        "summary": "Latency regression under traffic surge",
        "signals": ["p95 latency > 1.8s", "queue depth rising"],
        "recent_deploy_sha": None,
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "mitigated"

    triage_step = body["timeline"][0]
    diagnosis_step = body["timeline"][1]
    remediation_step = body["timeline"][2]

    assert triage_step["output"]["suspects"] == ["traffic_spike"]
    assert diagnosis_step["output"]["hypothesis"] == "Capacity saturation due to abnormal traffic"
    assert remediation_step["output"]["runbook_action"] == "scale_service_replicas"
    assert remediation_step["output"]["risk"] == "low"


def test_high_incident_with_recent_deploy_prefers_rollback_hypothesis() -> None:
    payload = {
        "service": "payments-api",
        "severity": "high",
        "summary": "Error rate spike after release",
        "signals": ["5xx > 8%", "checkout failures"],
        "recent_deploy_sha": "d34db33f",
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    body = response.json()
    diagnosis_step = body["timeline"][1]
    remediation_step = body["timeline"][2]

    assert diagnosis_step["output"]["hypothesis"] == "Regression introduced in recent deploy"
    assert remediation_step["output"]["runbook_action"] == "rollback_latest_deploy"
    assert "rollback_latest_deploy" in body["recommendation"]
