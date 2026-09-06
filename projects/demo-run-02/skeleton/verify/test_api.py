import os
import json
import httpx
import pytest


BASE_URL = os.environ["BASE_URL"]


@pytest.mark.parametrize("path,expected_len", [
    ("/api/expenses", 4),
])
def test_c_1_1_get_expenses_returns_4_items(path, expected_len):
    url = BASE_URL.rstrip("/") + path
    resp = httpx.get(url, timeout=10.0)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert isinstance(data, list), f"expected a JSON array, got {type(data)!r}"
    assert len(data) == expected_len, f"expected {expected_len} expenses, got {len(data)}"


def test_c_2_4_naive_settlement_api_first_item():
    url = BASE_URL.rstrip("/") + "/api/settlement/naive"
    resp = httpx.get(url, timeout=10.0)
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert isinstance(data, list), "expected a JSON array"
    assert len(data) == 4, f"expected 4 transfers, got {len(data)}"
    first = data[0]
    assert isinstance(first, dict), "first transfer must be an object"
    assert first == {"from": "Eve", "to": "Alice", "amountCents": 1300}
