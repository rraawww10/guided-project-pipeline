import time
from typing import Any, Dict, List

import httpx
from playwright.sync_api import Page

from conftest import (
    parse_cents_from_text,
    format_money,
    testid_selector,
)


def _wait_for_count(page: Page, selector: str, expected: int, timeout_ms: int = 5000) -> None:
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    last = -1
    while time.monotonic() < deadline:
        els = page.query_selector_all(selector)
        last = len(els)
        if last == expected:
            return
        time.sleep(0.05)
    assert last == expected, f"Timed out waiting for {expected} elements matching {selector}, last={last}"


# Session 1 UI

def test_c_1_2_ui_renders_one_row_per_expense(page: Page, http_client: httpx.Client, base_url: str):
    exps = http_client.get("/api/expenses").json()
    expected = len(exps)

    page.goto(base_url + "/", wait_until="domcontentloaded")
    # Rows carry data-testid="expense-row"
    _wait_for_count(page, '[data-testid="expense-row"]', expected)
    # Explicit assertion so static redfirst sees one in the test body
    count = len(page.query_selector_all('[data-testid="expense-row"]'))
    assert count == expected


def test_c_1_3_ui_renders_per_payer_totals_equal_sum_paid(page: Page, http_client: httpx.Client, base_url: str):
    exps = http_client.get("/api/expenses").json()
    totals: Dict[str, int] = {}
    for e in exps:
        payer = str(e.get("paidBy"))
        amt = int(e.get("amountCents", 0))
        totals[payer] = totals.get(payer, 0) + amt

    page.goto(base_url + "/", wait_until="domcontentloaded")

    for name, cents in totals.items():
        sel = testid_selector("payer-total-", name)
        el = page.wait_for_selector(sel, timeout=5000)
        text = el.inner_text().strip()
        got = parse_cents_from_text(text)
        assert got == int(cents), f"Total for {name} should be {cents} cents, got '{text}' -> {got}"


# Session 2 UI

def test_c_2_4_ui_shows_proposed_transfers_title_when_loaded(page: Page, base_url: str):
    page.goto(base_url + "/", wait_until="domcontentloaded")
    # Ambiguity W4: We wait for successful load and title presence.
    el = page.wait_for_selector("text=Proposed transfers", timeout=5000)
    assert el is not None


# Session 3 UI

def test_c_3_3_ui_toggle_include_recomputes_transfers(page: Page, http_client: httpx.Client, base_url: str):
    # Drive the toggle for some person and ensure their transfers are removed
    people = set()
    payload = http_client.get("/api/settlement").json()
    for t in payload.get("transfers", []):
        people.add(str(t.get("from")))
        people.add(str(t.get("to")))
    if not people:
        # Fallback to any names we can find from expenses
        exps = http_client.get("/api/expenses").json()
        for e in exps:
            people.add(str(e.get("paidBy")))
            for p in e.get("participants", []):
                people.add(str(p.get("person")))
    assert people, "No names available to toggle"

    name = sorted(people)[0]

    page.goto(base_url + "/", wait_until="domcontentloaded")

    # Ensure transfers are initially rendered
    page.wait_for_selector('[data-testid="transfer-row"]', timeout=5000)

    # Click the toggle for this person
    toggle_sel = testid_selector("toggle-", name)
    toggle = page.wait_for_selector(toggle_sel, timeout=5000)
    toggle.click()

    # After toggling off, no transfer row should mention this name
    def rows_text() -> List[str]:
        return [el.inner_text() for el in page.query_selector_all('[data-testid="transfer-row"]')]

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        texts = rows_text()
        if all(name not in t for t in texts):
            break
        time.sleep(0.05)
    # Verify condition
    texts = rows_text()
    assert all(name not in t for t in texts), f"Transfers should not include toggled-off person {name}"


def test_c_3_4_ui_transfer_amount_text_matches_currency(page: Page, http_client: httpx.Client, base_url: str):
    # Compare the first row's displayed amount to the formatted integer cents from the API.
    payload = http_client.get("/api/settlement").json()
    transfers: List[Dict[str, Any]] = payload.get("transfers", [])

    page.goto(base_url + "/", wait_until="domcontentloaded")

    rows = page.query_selector_all('[data-testid="transfer-row"]')
    if not transfers:
        # If there are no transfers, the UI should also render zero rows.
        assert len(rows) == 0
        return

    # Take the first transfer
    t0 = transfers[0]
    expected = format_money(int(t0.get("amountCents", 0)))

    # Find the first row's amount element
    amount_el = page.wait_for_selector('[data-testid="transfer-amount"]', timeout=5000)
    got = amount_el.inner_text().strip()
    assert got == expected, f"First transfer amount text should be {expected}, got {got}"


def test_c_3_5_ui_renders_one_row_per_transfer(page: Page, http_client: httpx.Client, base_url: str):
    payload = http_client.get("/api/settlement").json()
    transfers: List[Dict[str, Any]] = payload.get("transfers", [])
    expected = len(transfers)

    page.goto(base_url + "/", wait_until="domcontentloaded")
    _wait_for_count(page, '[data-testid="transfer-row"]', expected)
    # Explicit assertion so static redfirst sees one in the test body
    count = len(page.query_selector_all('[data-testid="transfer-row"]'))
    assert count == expected
