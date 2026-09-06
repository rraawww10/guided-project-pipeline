import httpx


def test_c_1_1_get_transactions_returns_array_with_required_fields(base_url):
    url = f"{base_url}/api/transactions"
    resp = httpx.get(url, timeout=10)
    assert resp.status_code == 200, f"Expected 200 from {url}, got {resp.status_code}"
    data = resp.json()
    assert isinstance(data, list), "Response must be a JSON array"
    # Each item must have the required fields with appropriate types
    for i, item in enumerate(data):
        assert isinstance(item, dict), f"Item {i} must be an object"
        for key in ["id", "memo", "merchant", "amount"]:
            assert key in item, f"Item {i} missing field '{key}'"
        assert isinstance(item["id"], str), "id must be a string"
        assert isinstance(item["memo"], str), "memo must be a string"
        assert isinstance(item["merchant"], str), "merchant must be a string"
        assert isinstance(item["amount"], (int, float)), "amount must be a number"
