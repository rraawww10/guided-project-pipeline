import os
import httpx


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_4_1_put_targets_returns_200_for_changed_weight():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        # Read current allocation to pick a symbol and target weight
        alloc = client.get("/api/allocation").json()
        assert isinstance(alloc, list) and len(alloc) > 0
        sym = alloc[0]["symbol"]
        current = float(alloc[0]["targetWeight"]) if "targetWeight" in alloc[0] else 0.1
        # shift weight slightly within 0..1
        new_weight = max(0.0, min(1.0, current + (0.05 if current <= 0.9 else -0.05)))
        resp = client.put("/api/targets", json=[{"symbol": sym, "weight": new_weight}])
    assert resp.status_code == 200


def test_c_4_2_put_settings_returns_200_for_changed_budget():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        resp = client.put("/api/settings", json={"budgetCents": 543210})
    assert resp.status_code == 200
