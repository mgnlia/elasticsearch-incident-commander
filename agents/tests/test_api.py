from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_run_incident_workflow() -> None:
    payload = {
        "service": "checkout-api",
        "severity": "high",
        "summary": "Latency spikes after deploy",
        "signals": ["p95 latency > 2.5s", "error rate 7%"],
        "recent_deploy_sha": "abc1234",
    }

    r = client.post("/incidents/run", json=payload)
    assert r.status_code == 200
    body = r.json()

    assert body["service"] == "checkout-api"
    assert body["status"] in {"investigating", "mitigated"}
    assert len(body["timeline"]) == 4
    assert body["timeline"][0]["agent"] == "triage"
    assert "rollback" in body["recommendation"]

    # Default CI/runtime expectation without secrets.
    assert body["elastic"]["status"] == "skipped"
    assert body["agent_builder"]["status"] == "skipped"


def test_run_incident_rejects_invalid_payload() -> None:
    payload = {
        "service": "a",
        "severity": "urgent",  # invalid enum
        "summary": "bad",
        "signals": [],
    }

    r = client.post("/incidents/run", json=payload)
    assert r.status_code == 422
