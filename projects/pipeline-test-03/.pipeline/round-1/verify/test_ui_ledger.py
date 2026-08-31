"""sc-ledger - route /, the table of accepted entries above the complaints panel.

One test per criterion. Every element is found through the data-testid the spec
pins; nothing here reads a class name or any styling, and every wait is a
retrying Playwright wait rather than a sleep.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    ACCEPTED_LINE_NOS,
    LOAD_TIMEOUT,
    bad_fields,
    numbered_testids,
    open_path,
    text_of,
)


def test_c_1_4_ledger_page_draws_21_rows_above_6_numbered_complaints(page):
    """c-1-4: / renders an element with data-testid entry-count and text 21,
    renders 21 elements with data-testid entry-row-<lineNo> whose lineNo values
    in document order are 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 21,
    23, 24, 26, 27, 29 and 30, renders entry-account-4 with text salary and
    entry-amount-4 with text 45000.00, renders an element with data-testid
    reject-count and text 6, and renders reject-row-17 with text
    line 17: expected 4 fields, found 3.

    entry-count is waited for first, so everything after it is read off a page
    whose GET /api/ledger has already answered. The row ids are read exactly -
    entry-row- is a prefix of no child testid on this screen, but the same exact
    match is used here as on the account page so the two read alike.

    Nothing in this test asserts a value an unwritten block also produces: with
    cut-parse-line open every line is rejected, so entry-count reads 0 and
    reject-count reads 27.
    """
    open_path(page, "/")

    expect(page.get_by_test_id("entry-count")).to_have_text(
        "21", timeout=LOAD_TIMEOUT)

    rows = numbered_testids(page, "entry-row-")
    assert len(rows) == 21, f"the page draws {len(rows)} entry rows, expected 21"
    assert rows == ACCEPTED_LINE_NOS, (
        f"entry-row lineNo values in document order are {rows!r}"
    )

    assert text_of(page.get_by_test_id("entry-account-4")) == "salary", (
        f"entry-account-4 reads {text_of(page.get_by_test_id('entry-account-4'))!r}"
    )
    assert text_of(page.get_by_test_id("entry-amount-4")) == "45000.00", (
        f"entry-amount-4 reads {text_of(page.get_by_test_id('entry-amount-4'))!r}, "
        f"expected formatPaise(4500000)"
    )

    expect(page.get_by_test_id("reject-count")).to_have_text("6")

    expected_17 = f"line 17: {bad_fields(3)}"
    assert text_of(page.get_by_test_id("reject-row-17")) == expected_17, (
        f"reject-row-17 reads {text_of(page.get_by_test_id('reject-row-17'))!r}, "
        f"expected {expected_17!r}"
    )
