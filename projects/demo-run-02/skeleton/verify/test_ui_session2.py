import os
from playwright.sync_api import expect

BASE_URL = os.environ["BASE_URL"].rstrip("/")


def test_c_2_1_balances_name_order_and_exact_texts(page):
    page.goto(BASE_URL + "/")
    rows = page.locator('[data-testid="balance-row"]')
    expect(rows).to_have_count(5)
    texts = [t.strip() for t in rows.all_inner_texts()]
    expected = [
        "Alice +$26.00",
        "Bob -$6.00",
        "Cara +$4.00",
        "Dan -$11.00",
        "Eve -$13.00",
    ]
    assert texts == expected


def test_c_2_2_transfers_first_item_text(page):
    page.goto(BASE_URL + "/")
    rows = page.locator('[data-testid="transfer-row"]')
    expect(rows).to_have_count(4)
    first_text = rows.nth(0).inner_text().strip()
    assert first_text == "Eve pays Alice $13.00"


def test_c_2_3_transfers_total_amount(page):
    page.goto(BASE_URL + "/")
    total = page.locator('[data-testid="transfers-total"]')
    expect(total).to_be_visible()
    expect(total).to_have_text("$30.00")
