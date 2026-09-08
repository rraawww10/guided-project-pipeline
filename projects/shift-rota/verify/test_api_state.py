import json


def test_c_2_6_post_state_alerting_round_trips(http_client):
    payload = {
        "contacts": ["Alex", "Beth", "Chen"],
        "mode": "alerting",
        "currentIndex": 0,
        "log": [],
    }
    resp = http_client.post("/api/state", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "alerting"


def test_c_3_6_get_state_seed_is_idle_and_contacts(http_client):
    resp = http_client.get("/api/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("contacts") == ["Alex", "Beth", "Chen"]
    assert data.get("mode") == "idle"
    assert data.get("log") == []
