import os
import math
import httpx


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_2_1_get_allocation_returns_expected_fields():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        resp = client.get("/api/allocation")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list) and len(items) > 0
    first = items[0]
    for key in ("symbol", "currentWeight", "targetWeight", "driftPercent"):
        assert key in first, f"missing field: {key}"
    # Ensure at least one item shows a non-zero drift so a zeroed fallback does not pass
    assert any(abs(float(it.get("driftPercent", 0))) > 1e-6 for it in items)


def test_c_2_5_allocation_weights_sum_to_one_rounded_3dp():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        resp = client.get("/api/allocation")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list) and len(items) > 0
    total = sum(float(it["currentWeight"]) for it in items)
    assert round(total, 3) == 1.0
