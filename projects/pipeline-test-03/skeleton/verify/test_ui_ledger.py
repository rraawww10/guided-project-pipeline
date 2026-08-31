"""sc-ledger at `/` - the table of accepted entries above the complaints panel.

One test per criterion, asserting only it. Every element is found through the
data-testid the spec pins, and every wait is a retrying Playwright wait, never a
sleep - `/` is a client component that renders from GET /api/ledger, so the
counts are waited for rather than read off a page that has not fetched yet.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    ENTRY_LINE_NOS,
    LOAD_TIMEOUT,
    REASONS,
    by_testid,
    family,
    line_nos,
    open_ledger,
    text_of,
)


def test_c_1_4_ledger_page_draws_21_rows_above_6_numbered_complaints(page):
    """c-1-4: `/` renders an element with data-testid entry-count and text 21,
    renders 21 elements with data-testid entry-row-<lineNo> whose lineNo values
    in document order are 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 21,
    23, 24, 26, 27, 29 and 30, renders entry-account-4 with text salary,
    entry-amount-4 with text 45000.00 and entry-amount-8 with text -250.05,
    renders an element with data-testid reject-count and text 6, and renders
    reject-row-17 with text `line 17: expected 4 fields, found 3`.

    The row list is compared as a whole ordered list, which is how the criterion
    grades that lines 1 to 3 are skipped before parsing: none of entry-row-1,
    entry-row-2 or entry-row-3 is in the expected list, so one appearing fails.
    Reading these off the `entry-row-` family and comparing the full list also
    keeps the match exact rather than by prefix - entry-row-1 is a string prefix
    of entry-row-16, so an equality test on the list is the only safe read.

    entry-amount-8 is the -250.05 cell, so this criterion carries the paise
    conversion onto the screen as well; the unwritten blocks cannot produce any
    of these values, because with cut-parse-line empty every line is rejected
    and entry-count reads 0 against reject-count 27.
    """
    open_ledger(page)

    count = by_testid(page, "entry-count")
    expect(count).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(count).to_have_text("21", timeout=LOAD_TIMEOUT)

    rows = family(page, "entry-row-")
    expect(rows).to_have_count(len(ENTRY_LINE_NOS), timeout=LOAD_TIMEOUT)
    assert line_nos(rows, "entry-row-") == ENTRY_LINE_NOS, (
        f"entry rows are {line_nos(rows, 'entry-row-')} in document order, "
        f"expected {ENTRY_LINE_NOS}"
    )

    assert text_of(by_testid(page, "entry-account-4")) == "salary", (
        f"entry-account-4 reads {text_of(by_testid(page, 'entry-account-4'))!r}, "
        f"expected 'salary'"
    )
    assert text_of(by_testid(page, "entry-amount-4")) == "45000.00", (
        f"entry-amount-4 reads {text_of(by_testid(page, 'entry-amount-4'))!r}, "
        f"expected '45000.00'"
    )
    assert text_of(by_testid(page, "entry-amount-8")) == "-250.05", (
        f"entry-amount-8 reads {text_of(by_testid(page, 'entry-amount-8'))!r}, "
        f"expected '-250.05'"
    )

    rejects = by_testid(page, "reject-count")
    expect(rejects).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(rejects).to_have_text("6", timeout=LOAD_TIMEOUT)

    expected_17 = f"line 17: {REASONS[17]}"
    assert text_of(by_testid(page, "reject-row-17")) == expected_17, (
        f"reject-row-17 reads {text_of(by_testid(page, 'reject-row-17'))!r}, "
        f"expected {expected_17!r}"
    )
