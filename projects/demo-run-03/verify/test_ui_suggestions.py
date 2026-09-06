from urllib.parse import urlparse, parse_qs
from playwright.sync_api import expect


def _parse_int(text: str) -> int:
    text = (text or "").strip()
    # allow values like "5" or "5.0" but we expect integers
    if "." in text:
        text = text.split(".", 1)[0]
    return int(text)


def test_c_2_2_sc_suggestions_renders_only_positive(base_url, page):
    page.goto("/suggestions")
    # Ensure at least one suggestion is rendered (seed guarantees > 0)
    page.wait_for_selector('[data-testid="suggestion-row"]', timeout=10000)
    rows = page.locator('[data-testid="suggestion-row"]')
    count = rows.count()
    assert count >= 1, "expected at least one positive suggestion to render"
    # Every rendered row must have qty_to_order > 0
    for i in range(count):
        cell = rows.nth(i).locator('[data-testid="qty-to-order"]')
        expect(cell).to_be_visible()
        qty_text = cell.inner_text().strip()
        qty = _parse_int(qty_text)
        assert qty > 0, f"row {i} shows non-positive qty_to_order: {qty}"


def test_c_2_3_sc_suggestions_shows_qty_in_cell(base_url, page):
    page.goto("/suggestions")
    page.wait_for_selector('[data-testid="suggestion-row"]', timeout=10000)
    rows = page.locator('[data-testid="suggestion-row"]')
    count = rows.count()
    assert count >= 1, "expected some rendered suggestions"
    for i in range(count):
        cell = rows.nth(i).locator('[data-testid="qty-to-order"]')
        expect(cell).to_be_visible()
        txt = cell.inner_text().strip()
        # Must be an integer string (e.g., "3")
        assert txt.isdigit(), f"row {i} qty-to-order cell not an integer: {txt!r}"
