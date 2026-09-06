import re
from playwright.sync_api import expect


def find_row_by_memo(page, memo: str):
    return page.locator('[data-testid="tx-row"]').filter(
        has=page.get_by_test_id('tx-memo').filter(has_text=memo)
    )


def parse_number(text: str) -> float:
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    assert m, f"No number found in '{text}'"
    return float(m.group(0))


def get_summary_row(page, category: str):
    return page.locator('[data-testid="summary-row"]').filter(
        has=page.get_by_test_id('summary-cat').filter(has_text=category)
    )


def test_c_2_1_category_transport_for_uber_trip_downtown(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="tx-row"]')
    row = find_row_by_memo(page, "Uber trip downtown")
    expect(row).to_have_count(1)
    cat = row.get_by_test_id('tx-category')
    expect(cat).to_have_text("Transport")


def test_c_2_2_rule_label_for_uber_trip_downtown(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="tx-row"]')
    row = find_row_by_memo(page, "Uber trip downtown")
    expect(row).to_have_count(1)
    rule = row.get_by_test_id('tx-rule')
    expect(rule).to_have_text("memo contains 'uber'")


def test_c_2_3_summary_has_supplies_total_25(page, base_url):
    page.goto(base_url)
    # Summary is present in session 2
    page.wait_for_selector('[data-testid="summary"]')
    row = get_summary_row(page, "Supplies")
    expect(row).to_have_count(1)
    total_text = row.get_by_test_id('summary-total').inner_text()
    assert parse_number(total_text) == 25


def test_c_2_4_category_transport_for_uber_refund_not_income(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="tx-row"]')
    row = find_row_by_memo(page, "Uber refund")
    expect(row).to_have_count(1)
    cat = row.get_by_test_id('tx-category')
    expect(cat).to_have_text("Transport")
    assert cat.inner_text().strip() != "Income"


def test_c_2_5_summary_heading_visible_once(page, base_url):
    page.goto(base_url)
    locator = page.get_by_text("Summary by category", exact=True)
    expect(locator).to_have_count(1)
    assert locator.nth(0).is_visible()


def test_c_2_6_summary_transport_total_20(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="summary"]')
    row = get_summary_row(page, "Transport")
    expect(row).to_have_count(1)
    total_text = row.get_by_test_id('summary-total').inner_text()
    assert parse_number(total_text) == 20
