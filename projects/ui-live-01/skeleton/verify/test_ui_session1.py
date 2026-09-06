import httpx
from playwright.sync_api import expect


def _get_transactions(base_url):
    resp = httpx.get(f"{base_url}/api/transactions", timeout=10)
    assert resp.status_code == 200
    return resp.json()


def test_c_1_2_ui_renders_one_row_per_transaction(page, base_url):
    # Fetch API length as the source of truth, then compare to rendered row count
    txs = _get_transactions(base_url)
    page.goto(base_url)
    # Wait for at least one row to appear; an empty UI should fail this wait
    page.wait_for_selector('[data-testid="tx-row"]')
    rows = page.locator('[data-testid="tx-row"]').all()
    assert len(rows) == len(txs), f"Expected {len(txs)} rows, saw {len(rows)}"


def test_c_1_3_ui_renders_each_row_memo(page, base_url):
    txs = _get_transactions(base_url)
    page.goto(base_url)
    page.wait_for_selector('[data-testid="tx-row"]')
    for tx in txs:
        memo = tx["memo"]
        # Find a row whose memo cell matches this memo exactly
        row = page.locator('[data-testid="tx-row"]').filter(
            has=page.get_by_test_id('tx-memo').filter(has_text=memo)
        )
        expect(row).to_have_count(1)
        cell = row.get_by_test_id('tx-memo')
        expect(cell).to_have_text(memo)
