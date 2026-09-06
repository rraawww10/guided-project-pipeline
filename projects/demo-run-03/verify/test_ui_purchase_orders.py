from urllib.parse import urlparse, parse_qs
from playwright.sync_api import expect


def _parse_int(text: str) -> int:
    text = (text or "").strip()
    if "." in text:
        text = text.split(".", 1)[0]
    return int(text)


def test_c_3_2_sc_suggestions_button_counts_checked(base_url, page):
    page.goto("/suggestions")
    page.wait_for_selector('[data-testid="suggestion-row"]', timeout=10000)
    rows = page.locator('[data-testid="suggestion-row"]')
    assert rows.count() >= 2, "need at least two suggestions to test selection"
    # Check the first two checkboxes
    rows.nth(0).locator('input[type="checkbox"]').check()
    rows.nth(1).locator('input[type="checkbox"]').check()
    btn = page.locator('[data-testid="po-submit"]')
    expect(btn).to_be_visible()
    text = btn.inner_text()
    assert "(2)" in text, f"button text should include '(2)' after two selections, got: {text!r}"


essential_wait = 15000


def test_c_3_3_sc_suggestions_navigates_to_created_with_counts(base_url, page):
    page.goto("/suggestions")
    page.wait_for_selector('[data-testid="suggestion-row"]', timeout=essential_wait)
    rows = page.locator('[data-testid="suggestion-row"]')
    assert rows.count() >= 2
    # Read the qty_to_order of first two rows so we know the expected total
    q1 = _parse_int(rows.nth(0).locator('[data-testid="qty-to-order"]').inner_text())
    q2 = _parse_int(rows.nth(1).locator('[data-testid="qty-to-order"]').inner_text())
    expected_items = 2
    expected_total = q1 + q2
    # Select them and submit
    rows.nth(0).locator('input[type="checkbox"]').check()
    rows.nth(1).locator('input[type="checkbox"]').check()
    page.locator('[data-testid="po-submit"]').click()
    # Wait for navigation and assert URL params
    page.wait_for_url("**/purchase-orders/created**", timeout=essential_wait)
    parsed = urlparse(page.url)
    qs = parse_qs(parsed.query)
    assert qs.get("items", [None])[0] == str(expected_items)
    assert qs.get("total", [None])[0] == str(expected_total)


def test_c_3_4_sc_po_created_renders_numbers_from_url(base_url, page):
    items = 4
    total = 11
    page.goto(f"/purchase-orders/created?items={items}&total={total}")
    items_el = page.locator('[data-testid="po-created-items"]')
    total_el = page.locator('[data-testid="po-created-total"]')
    expect(items_el).to_be_visible()
    expect(total_el).to_be_visible()
    assert items_el.inner_text().strip() == str(items)
    assert total_el.inner_text().strip() == str(total)


def test_c_4_2_sc_po_history_renders_rows_with_counts(base_url, page, http_client):
    # Create a PO we can assert against
    skus = http_client.get("/api/skus").json()
    assert len(skus) >= 2
    lines = [{"sku_id": skus[0]["id"], "qty": 2}, {"sku_id": skus[1]["id"], "qty": 3}]
    created = http_client.post("/api/purchase-orders", json={"lines": lines}).json()

    page.goto("/purchase-orders")
    page.wait_for_selector('[data-testid="po-row"]', timeout=essential_wait)
    rows = page.locator('[data-testid="po-row"]')
    assert rows.count() >= 1

    want_items = created["itemsCount"]
    want_total = created["totalQty"]
    # Look for a row that shows both numbers
    saw = False
    for i in range(rows.count()):
        txt = rows.nth(i).inner_text()
        if str(want_items) in txt and str(want_total) in txt:
            saw = True
            break
    assert saw, f"no history row showed items={want_items} and total={want_total}"


def test_c_4_4_sc_po_detail_renders_lines(base_url, page, http_client):
    # Create a PO with two known lines (ids and names from /api/skus)
    skus = http_client.get("/api/skus").json()
    assert len(skus) >= 2
    id1, name1 = skus[0]["id"], skus[0]["name"]
    id2, name2 = skus[1]["id"], skus[1]["name"]
    lines = [{"sku_id": id1, "qty": 1}, {"sku_id": id2, "qty": 3}]
    created = http_client.post("/api/purchase-orders", json={"lines": lines}).json()

    page.goto(f"/purchase-orders/{created['id']}")
    page.wait_for_selector('[data-testid="po-line"]', timeout=essential_wait)
    rows = page.locator('[data-testid="po-line"]')
    assert rows.count() == 2

    # Each line should show the SKU name and the qty
    row_texts = [rows.nth(i).inner_text() for i in range(2)]
    assert any(name1 in t and "1" in t for t in row_texts), f"missing line for {name1} qty 1"
    assert any(name2 in t and "3" in t for t in row_texts), f"missing line for {name2} qty 3"
