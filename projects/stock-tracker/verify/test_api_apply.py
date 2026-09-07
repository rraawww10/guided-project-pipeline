import os
import statistics
import httpx


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def _avg_abs_drift(client: httpx.Client) -> float:
    alloc = client.get("/api/allocation").json()
    vals = [abs(float(it.get("driftPercent", 0))) for it in alloc]
    return float(sum(vals) / len(vals)) if vals else 0.0


def test_c_5_1_post_apply_plan_returns_applied_greater_than_zero():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=15.0) as client:
        # Ensure there is something to apply: tweak a target slightly
        alloc = client.get("/api/allocation").json()
        sym = alloc[0]["symbol"]
        tw = float(alloc[0].get("targetWeight", 0.1))
        new_tw = max(0.0, min(1.0, tw + (0.03 if tw <= 0.9 else -0.03)))
        client.put("/api/targets", json=[{"symbol": sym, "weight": new_tw}])
        resp = client.post("/api/apply-plan")
    assert resp.status_code == 200
    body = resp.json()
    assert int(body.get("applied", 0)) > 0


def test_c_5_3_get_trades_returns_trade_objects_after_apply():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=15.0) as client:
        # Read current trades (should be 0 after reseed/clear, but do not rely on it)
        before_resp = client.get("/api/trades")
        assert before_resp.status_code == 200
        before_items = before_resp.json()
        before_len = len(before_items) if isinstance(before_items, list) else 0
        # Apply the plan to create trades, then verify listing returns Trade objects
        client.post("/api/apply-plan")
        resp = client.get("/api/trades")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list) and len(items) > before_len
    first = items[0]
    for key in ("symbol", "shares"):
        assert key in first


def test_c_5_4_apply_reduces_average_abs_drift():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=15.0) as client:
        # conftest.py reseeds first, so `before` is the seeded 4.78% and the
        # comparison is against a known state. The original snapshotted before
        # its own nudge, so the nudge's drift sat outside the comparison and an
        # apply that merely undid it read as no improvement.
        before = _avg_abs_drift(client)
        applied = client.post("/api/apply-plan").json()
        assert int(applied.get("applied", 0)) > 0, (
            "apply recorded nothing, so drift cannot move")
        after = _avg_abs_drift(client)
    assert after < before, f"average absolute drift did not fall: {before} -> {after}"


def test_c_5_5_apply_returns_updated_holdings_length_equals_assets_count():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=15.0) as client:
        positions = client.get("/api/positions").json()
        n_assets = len(positions)
        # Ensure a plan exists, then apply
        alloc = client.get("/api/allocation").json()
        sym = alloc[0]["symbol"]
        tw = float(alloc[0].get("targetWeight", 0.1))
        new_tw = max(0.0, min(1.0, tw + (0.01 if tw <= 0.9 else -0.01)))
        client.put("/api/targets", json=[{"symbol": sym, "weight": new_tw}])
        resp = client.post("/api/apply-plan")
    assert resp.status_code == 200
    body = resp.json()
    updated = body.get("updatedHoldings")
    assert isinstance(updated, list)
    assert len(updated) == n_assets
