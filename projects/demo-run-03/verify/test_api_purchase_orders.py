from typing import List, Tuple


def _two_sku_ids(http_client) -> List[int]:
    skus = http_client.get("/api/skus").json()
    assert isinstance(skus, list) and len(skus) >= 2
    return [skus[0]["id"], skus[1]["id"]]


def test_c_3_1_ep_po_create_returns_summary(http_client):
    sku_ids = _two_sku_ids(http_client)
    lines = [
        {"sku_id": sku_ids[0], "qty": 2},
        {"sku_id": sku_ids[1], "qty": 5},
    ]
    resp = http_client.post("/api/purchase-orders", json={"lines": lines})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, dict)
    for k in ("id", "itemsCount", "totalQty"):
        assert k in data
    assert isinstance(data["id"], int)
    assert data["itemsCount"] == 2
    assert data["totalQty"] == 7


def test_c_4_1_ep_po_list_returns_summaries(http_client):
    # Create a PO first so we can assert against a known id and totals
    sku_ids = _two_sku_ids(http_client)
    lines = [
        {"sku_id": sku_ids[0], "qty": 1},
        {"sku_id": sku_ids[1], "qty": 4},
    ]
    created = http_client.post("/api/purchase-orders", json={"lines": lines}).json()
    created_id = created["id"]
    items = created["itemsCount"]
    total = created["totalQty"]

    resp = http_client.get("/api/purchase-orders")
    assert resp.status_code == 200, resp.text
    arr = resp.json()
    assert isinstance(arr, list)
    # Find our created PO in the list
    match = None
    for po in arr:
        if po.get("id") == created_id:
            match = po
            break
    assert match is not None, f"created PO {created_id} not found in list"
    assert match.get("itemsCount") == items
    assert match.get("totalQty") == total


def test_c_4_3_ep_po_detail_returns_detail(http_client):
    sku_ids = _two_sku_ids(http_client)
    # Distinct quantities to make the totals easy to assert
    lines = [
        {"sku_id": sku_ids[0], "qty": 3},
        {"sku_id": sku_ids[1], "qty": 6},
    ]
    created = http_client.post("/api/purchase-orders", json={"lines": lines}).json()
    created_id = created["id"]

    resp = http_client.get(f"/api/purchase-orders/{created_id}")
    assert resp.status_code == 200, resp.text
    detail = resp.json()
    for k in ("id", "lines", "itemsCount", "totalQty"):
        assert k in detail
    assert detail["id"] == created_id
    assert isinstance(detail["lines"], list)
    assert detail["itemsCount"] == len(detail["lines"]) == 2
    assert sum(line.get("qty", 0) for line in detail["lines"]) == detail["totalQty"] == 9
    # Ensure each line has the required shape
    for i, line in enumerate(detail["lines"]):
        for k in ("sku_id", "name", "qty"):
            assert k in line, f"line[{i}] missing {k}"
