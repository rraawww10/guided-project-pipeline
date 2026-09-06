import json
from typing import Any, Dict, List


def test_c_1_1_ep_skus_list_returns_8(http_client):
    resp = http_client.get("/api/skus")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list), f"expected list, got {type(data)}"
    assert len(data) == 8, f"expected 8 SKUs, got {len(data)}"
    for i, sku in enumerate(data):
        assert isinstance(sku, dict), f"SKU[{i}] not an object"
        for key in ("id", "name", "on_hand", "reorder_point"):
            assert key in sku, f"SKU[{i}] missing key {key}"
        assert isinstance(sku["id"], int)
        assert isinstance(sku["name"], str)
        assert isinstance(sku["on_hand"], int)
        assert isinstance(sku["reorder_point"], int)
