import os
import httpx


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_1_1_get_positions_returns_required_fields():
    base = _base_url()
    with httpx.Client(base_url=base, timeout=10.0) as client:
        resp = client.get("/api/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) and len(data) > 0
    first = data[0]
    # Required fields per criterion
    for key in ("symbol", "shares", "priceCents", "targetWeight"):
        assert key in first, f"missing field: {key}"
