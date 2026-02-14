from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_diagnosis_query_plan_contract_for_recent_deploy_incident() -> None:
    payload = {
        "service": "checkout-api",
        "severity": "high",
        "summary": "Latency and errors increased after deploy",
        "signals": ["p95 latency > 2.5s", "5xx > 6%"],
        "recent_deploy_sha": "abc1234",
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    diagnosis_step = response.json()["timeline"][1]
    assert diagnosis_step["agent"] == "diagnosis"
    assert diagnosis_step["action"] == "generate_root_cause_hypothesis"
    assert diagnosis_step["output"]["hypothesis"] == "Regression introduced in recent deploy"

    query_plan = diagnosis_step["output"]["query_plan"]
    assert len(query_plan) == 2
    assert query_plan[0].startswith("FROM logs-*")
    assert "service == ?" in query_plan[0]
    assert "NOW()-15m" in query_plan[0]
    assert query_plan[1].startswith("FROM metrics-*")
    assert "percentile(latency_ms,95)" in query_plan[1]
    assert diagnosis_step["output"]["signals_seen"] == payload["signals"]


def test_diagnosis_hypothesis_contract_without_recent_deploy() -> None:
    payload = {
        "service": "search-api",
        "severity": "medium",
        "summary": "Traffic surge increased response time",
        "signals": ["queue depth rising", "cpu 85%"],
        "recent_deploy_sha": None,
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    diagnosis_step = response.json()["timeline"][1]
    assert diagnosis_step["output"]["hypothesis"] == "Capacity saturation due to abnormal traffic"
