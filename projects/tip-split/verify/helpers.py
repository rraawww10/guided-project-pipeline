"""Shared constants and waits for the tip-split verification suite.

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, and every wait is a Playwright retrying wait, never a sleep.
"""
from __future__ import annotations

import os

from playwright.sync_api import Locator, Page, expect

BASE_URL = os.environ["BASE_URL"].rstrip("/")

# a screen has to load, fetch and render before anything can be read
LOAD_TIMEOUT = 20_000

BILL_FIELDS = {
    "id": str,
    "place": str,
    "date": str,
    "totalPaise": int,
    "tipPercent": int,
    "people": int,
}

# data/bills.json, in the order the file stores it
SEED_BILLS = [
    {"id": "anand-bhavan", "place": "Anand Bhavan", "date": "2026-03-14",
     "totalPaise": 124000, "tipPercent": 10, "people": 4},
    {"id": "kabab-junction", "place": "Kabab Junction", "date": "2026-02-28",
     "totalPaise": 87550, "tipPercent": 7, "people": 3},
    {"id": "the-filter-room", "place": "The Filter Room", "date": "2026-02-09",
     "totalPaise": 45000, "tipPercent": 5, "people": 2},
    {"id": "paradise-biryani", "place": "Paradise Biryani", "date": "2026-01-26",
     "totalPaise": 233375, "tipPercent": 12, "people": 6},
    {"id": "chai-point-mg", "place": "Chai Point MG Road", "date": "2026-01-05",
     "totalPaise": 19900, "tipPercent": 15, "people": 2},
    {"id": "kurry-kulture", "place": "Kurry Kulture", "date": "2025-12-19",
     "totalPaise": 310000, "tipPercent": 8, "people": 5},
]


def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


def open_list(page: Page) -> None:
    """Open sc-list and wait until it has left its loading state."""
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
    expect(page.get_by_test_id("bill-card").first).to_be_attached(timeout=LOAD_TIMEOUT)


def open_bill(page: Page, bill_id: str) -> None:
    """Open sc-bill for a bill the store holds and wait for its loaded state."""
    page.goto(f"{BASE_URL}/bills/{bill_id}", wait_until="domcontentloaded")
    expect(page.get_by_test_id("bill-place")).to_be_attached(timeout=LOAD_TIMEOUT)


def open_bill_raw(page: Page, bill_id: str) -> None:
    """Open sc-bill without assuming which state it settles in."""
    page.goto(f"{BASE_URL}/bills/{bill_id}", wait_until="domcontentloaded")


def people_count(page: Page) -> Locator:
    return page.get_by_test_id("people-count")


def share_rows(page: Page) -> Locator:
    return page.get_by_test_id("share-row")


def row_texts(page: Page, expected_rows: int) -> list[str]:
    """Wait for exactly `expected_rows` share-row elements, then read them."""
    rows = share_rows(page)
    expect(rows).to_have_count(expected_rows, timeout=LOAD_TIMEOUT)
    return [normalize(t) for t in rows.all_text_contents()]


def flush_render(page: Page) -> None:
    """Let the page paint twice, so a click that should change nothing has still
    been through React before the assertion reads the DOM."""
    page.evaluate(
        "() => new Promise((done) =>"
        " requestAnimationFrame(() => requestAnimationFrame(() => done(null))))"
    )


def step_people(page: Page, label: str, counts: list[int]) -> None:
    """Click the stepper button named `label` once per entry of `counts`,
    waiting for people-count to read each entry before the next click.

    The wait is synchronisation, not an extra assertion: it stops a later click
    from landing on a render that has not happened yet.
    """
    button = page.get_by_role("button", name=label, exact=True)
    expect(button).to_be_enabled(timeout=LOAD_TIMEOUT)
    for value in counts:
        button.click()
        expect(people_count(page)).to_have_text(str(value), timeout=LOAD_TIMEOUT)
    # a clamped click leaves the count where it was, so waiting for a value is
    # not enough on its own to know the click has been rendered
    flush_render(page)
