def test_c_2_1_ep_reorder_suggestions_qty_formula(http_client):
    resp = http_client.get("/api/reorder-suggestions")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list), f"expected list, got {type(data)}"
    # Must shape one suggestion per SKU
    assert len(data) == 8, f"expected 8 suggestions (one per SKU), got {len(data)}"

    saw_pos = False
    saw_zero = False
    for i, s in enumerate(data):
        for k in ("sku_id", "name", "on_hand", "reorder_point", "qty_to_order"):
            assert k in s, f"Suggestion[{i}] missing key {k}"
        oh = s["on_hand"]
        rp = s["reorder_point"]
        q = s["qty_to_order"]
        expected = max(0, rp - oh)
        assert q == expected, f"Suggestion[{i}] expected qty_to_order {expected}, got {q}"
        if q > 0:
            saw_pos = True
        if q == 0:
            saw_zero = True
    # Seed guarantees at least one positive and one zero qty
    assert saw_pos, "expected at least one positive qty_to_order from seed"
    assert saw_zero, "expected at least one zero qty_to_order from seed"
