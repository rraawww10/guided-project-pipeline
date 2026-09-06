import re
from playwright.sync_api import expect


def get_summary_row(page, category: str):
    return page.locator('[data-testid="summary-row"]').filter(
        has=page.get_by_test_id('summary-cat').filter(has_text=category)
    )


def parse_number(text: str) -> float:
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    assert m, f"No number found in '{text}'"
    return float(m.group(0))


def set_budget(page, category: str, value: str):
    inp = page.get_by_test_id(f"budget-{category}")
    expect(inp).to_have_count(1)
    inp.fill("")
    inp.type(value)
    inp.blur()


def test_c_3_1_delta_updates_after_setting_transport_budget_30(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="summary"]')
    set_budget(page, "Transport", "30")
    row = get_summary_row(page, "Transport")
    expect(row).to_have_count(1)
    delta_text = row.get_by_test_id('summary-delta').inner_text()
    assert parse_number(delta_text) == -10


def read_deltas(page) -> list[float]:
    return [parse_number(t) for t in
            page.locator('[data-testid="summary-delta"]').all_inner_texts()]


def test_c_3_2_sort_by_delta_places_expense_first_after_budget(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="summary"]')
    set_budget(page, "Transport", "30")
    # summarizeByCategory already orders by category name, and "Expense" is both
    # alphabetically first and largest by delta - so asserting only the first row
    # passes whether the sort ran or not. Check the deltas themselves, in DOM
    # order, and refuse to run at all against fixtures that start sorted.
    before = read_deltas(page)
    assert before != sorted(before, reverse=True), (
        f"the fixtures start in delta order ({before}), so this test could not "
        f"tell a working sort from a missing one")
    sort_btn = page.get_by_test_id('sort-delta')
    expect(sort_btn).to_have_count(1)
    sort_btn.click()
    after = read_deltas(page)
    assert after == sorted(after, reverse=True), (
        f"rows are not sorted by delta descending: {after}")
    first_row = page.locator('[data-testid="summary-row"]').first
    first_cat = first_row.get_by_test_id('summary-cat').inner_text().strip()
    assert first_cat == "Expense"


def test_c_3_3_toggle_overbudget_hides_transport_and_keeps_expense(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="summary"]')
    set_budget(page, "Transport", "30")
    toggle = page.get_by_test_id('toggle-over')
    expect(toggle).to_have_count(1)
    toggle.check()
    # Transport has delta -10 after budget 30 -> should disappear
    expect(get_summary_row(page, "Transport")).to_have_count(0)
    # Expense remains (delta positive)
    expect(get_summary_row(page, "Expense")).to_have_count(1)


def test_c_3_4_percent_shows_one_decimal_transport_66_7(page, base_url):
    page.goto(base_url)
    page.wait_for_selector('[data-testid="summary"]')
    set_budget(page, "Transport", "30")
    row = get_summary_row(page, "Transport")
    expect(row).to_have_count(1)
    pct_text = row.get_by_test_id('summary-pct').inner_text().strip()
    assert pct_text == "66.7%"


def test_c_3_5_delta_header_visible_once(page, base_url):
    page.goto(base_url)
    # Exact-case "Delta" should match the header, not the "Sort by delta" button.
    loc = page.get_by_text("Delta", exact=True)
    expect(loc).to_have_count(1)
    assert loc.nth(0).is_visible()
