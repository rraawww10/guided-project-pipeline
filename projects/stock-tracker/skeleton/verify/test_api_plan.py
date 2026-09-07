import os
import httpx


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


BUDGET = 100_000  # cents


def test_c_3_1_post_trade_plan_returns_items_with_symbol_and_integer_shares():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        resp = client.post("/api/trade-plan", json={"budgetCents": BUDGET})
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert len(items) > 0
    first = items[0]
    assert "symbol" in first and "shares" in first
    assert isinstance(first["shares"], int)


def test_c_3_2_post_trade_plan_respects_budget():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        resp = client.post("/api/trade-plan", json={"budgetCents": BUDGET})
    assert resp.status_code == 200
    items = resp.json()
    buy_cost = sum(int(it.get("costCents", 0)) for it in items if it.get("side") == "BUY")
    assert buy_cost <= BUDGET


def test_c_3_3_first_plan_item_is_largest_positive_drift():
    """c-3-3: plan[0] is the candidate with the largest absolute POSITIVE drift.

    Both reads come from the same live state, and conftest.py reseeds first, so
    this no longer depends on what an earlier test file did to the database -
    which is why it once compared MSFT against a GOOGL computed from mutated
    holdings.

    One row is enough to grade cut-plan-rank here: the seed lists AAPL first
    but the expected leader is GOOGL, so an unranked plan does not start with
    GOOGL. lessons.md's rule is that seed order must differ from the order the
    spec asks for, and it does.
    """
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        alloc = client.get("/api/allocation").json()
        plan = client.post("/api/trade-plan", json={"budgetCents": BUDGET}).json()
    assert isinstance(plan, list) and len(plan) > 0
    positives = [it for it in alloc if float(it.get("driftPercent", 0)) > 0]
    assert positives, "expected at least one overweight symbol in the seed"
    top = max(positives, key=lambda it: float(it["driftPercent"]))
    assert plan[0]["symbol"] == top["symbol"], (
        f"largest positive drift is {top['symbol']} at "
        f"{float(top['driftPercent']):.4f}% but the plan starts with "
        f"{plan[0]['symbol']}; plan order was "
        + repr([it["symbol"] for it in plan]))
