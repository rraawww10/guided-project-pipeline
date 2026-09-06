import os
from playwright.sync_api import expect

BASE_URL = os.environ["BASE_URL"].rstrip("/")


def test_c_3_1_money_sample_shows_negative_format(page):
    page.goto(BASE_URL + "/")
    sample = page.locator('[data-testid="money-sample"]')
    expect(sample).to_be_visible()
    expect(sample).to_have_text("-$6.15")


def test_c_3_2_minimal_on_orders_transfers_by_amount_then_payer_payee(page):
    page.goto(BASE_URL + "/")
    toggle = page.locator('[data-testid="toggle-minimal"]')
    # Turn minimal mode ON by clicking once
    toggle.click()
    rows = page.locator('[data-testid="transfer-row"]')
    expect(rows).to_have_count(4)
    texts = [t.strip() for t in rows.all_inner_texts()]
    expected = [
        "Eve pays Alice $13.00",
        "Dan pays Alice $11.00",
        "Bob pays Cara $4.00",
        "Bob pays Alice $2.00",
    ]
    assert texts == expected


def test_c_3_3_unchecking_eve_excludes_from_balances_and_transfers(page):
    page.goto(BASE_URL + "/")
    eve_box = page.locator('[data-testid="include-Eve"]')
    # Ensure unchecked: click if it's checked or just click once (idempotent UI should handle)
    eve_box.click()
    # No balance row with Eve
    balance_rows = page.locator('[data-testid="balance-row"]')
    all_balance_text = "\n".join([t.strip() for t in balance_rows.all_inner_texts()])
    assert "Eve" not in all_balance_text
    # No transfer row mentions Eve
    transfer_rows = page.locator('[data-testid="transfer-row"]')
    all_transfer_text = "\n".join([t.strip() for t in transfer_rows.all_inner_texts()])
    assert "Eve" not in all_transfer_text


def test_c_3_4_minimal_on_renders_4_transfer_rows(page):
    page.goto(BASE_URL + "/")
    toggle = page.locator('[data-testid="toggle-minimal"]')
    toggle.click()  # turn ON
    rows = page.locator('[data-testid="transfer-row"]')
    expect(rows).to_have_count(4)


def test_c_3_5_minimal_off_last_item_is_bob_pays_cara(page):
    page.goto(BASE_URL + "/")
    toggle = page.locator('[data-testid="toggle-minimal"]')
    # Ensure we end in OFF: click twice
    toggle.click()
    toggle.click()
    rows = page.locator('[data-testid="transfer-row"]')
    expect(rows).to_have_count(4)
    last_text = rows.nth(3).inner_text().strip()
    assert last_text == "Bob pays Cara $4.00"
