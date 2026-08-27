import os
import httpx

BASE = os.environ["BASE_URL"]


def test_health_returns_ok():
    r = httpx.get(f"{BASE}/api/health", timeout=30)
    assert r.status_code == 200
    assert r.json()["ok"] is True
