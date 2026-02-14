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
    assert body["service"] == payload["service"]
    assert body["severity"] == payload["severity"]
    assert body["status"] in {"open", "investigating", "mitigated"}
    assert len(body["timeline"]) == 4
    assert body["timeline"][0]["agent"] == "triage"
    assert body["timeline"][1]["agent"] == "diagnosis"
    assert body["timeline"][2]["agent"] == "remediation"
    assert body["timeline"][3]["agent"] == "communication"
