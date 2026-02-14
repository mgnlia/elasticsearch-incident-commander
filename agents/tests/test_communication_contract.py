from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_stakeholder_update_contract_fields_and_channel() -> None:
    payload = {
        "service": "catalog-api",
        "severity": "high",
        "summary": "Sustained 5xx increase",
        "signals": ["5xx > 6%", "latency p95 > 2.2s"],
        "recent_deploy_sha": "a1b2c3d",
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    body = response.json()
    communication_step = body["timeline"][3]

    assert communication_step["agent"] == "communication"
    assert communication_step["action"] == "compose_stakeholder_update"
    assert communication_step["output"]["channel"] == "#incidents"
    assert communication_step["output"]["next_update_eta_min"] == 15

    message = communication_step["output"]["message"]
    assert payload["service"] in message
    assert "Applied action:" in message
    assert body["stakeholder_update"] == message


def test_stakeholder_update_contains_selected_runbook_action() -> None:
    payload = {
        "service": "search-api",
        "severity": "medium",
        "summary": "Latency drift from demand spike",
        "signals": ["queue depth +40%", "cpu at 82%"],
        "recent_deploy_sha": None,
    }

    response = client.post("/incidents/run", json=payload)
    assert response.status_code == 200

    body = response.json()
    remediation_action = body["timeline"][2]["output"]["runbook_action"]
    stakeholder_update = body["stakeholder_update"]

    assert remediation_action in stakeholder_update
    assert stakeholder_update.startswith("Investigating")
