"""sc-account at `/accounts/[name]` - the sidebar, the total and the running column.

One test per criterion, asserting only it. This screen is a server component
that reads data/ledger.txt through parseLedger and makes no fetch, so its HTTP
status is part of what a criterion reads: every test navigates through
`open_account`, which hands back the main response.

ambiguity.md B1 records two readings of the miss case - a `notFound()` throw
with a not-found boundary rendering `account-missing` (404 and the element), or
the page rendering the miss markup itself (200 and the element). c-2-4 pins
*both* the 404 and the element, and spec.md says "the route answers 404 and
renders one element with data-testid account-missing", so this suite takes that
reading: status and element together, asserted as the criterion words them.
Which file renders it is the Builder's to decide; the suite reads the route.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    ACCOUNT_NAMES,
    FOOD_TOTAL_TEXT,
    LOAD_TIMEOUT,
    RENT_ROW_LINE_NOS,
    RENT_RUNNING_TEXT,
    RENT_TOTAL_TEXT,
    SALARY_RUNNING_TEXT,
    SALARY_TOTAL_TEXT,
    by_testid,
    family,
    line_nos,
    open_account,
    suffixes,
    text_of,
)


def test_c_2_3_rent_page_walks_three_rows_down_to_the_account_total(page):
    """c-2-3: /accounts/rent responds 200 and renders account-title with text
    rent, account-total with text -37200.00, exactly 3 elements with data-testid
    account-txn-<lineNo> whose lineNo values in document order are 5, 11 and 20,
    and txn-running-5, txn-running-11 and txn-running-20 with texts -18000.00,
    -19200.00 and -37200.00.

    The three row wrappers are enumerated on `account-txn-`, which spec.md
    states is the prefix of no other data-testid on the page (the cells inside
    each row are `txn-*`), and the list is compared whole so an extra row fails
    as loudly as a missing one.

    None of the three running texts is a value an unwritten block produces: with
    cut-running-balance empty every txn-running cell renders the single
    character `-`, and the running column is a real scan rather than a repeated
    total, because -18000.00, -19200.00 and -37200.00 are three different
    strings and only the last equals account-total.
    """
    response = open_account(page, "rent")
    assert response is not None and response.status == 200, (
        f"/accounts/rent answered "
        f"{response.status if response else 'no response'}, expected 200"
    )

    title = by_testid(page, "account-title")
    expect(title).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(title) == "rent", f"account-title reads {text_of(title)!r}"

    total = by_testid(page, "account-total")
    expect(total).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(total) == RENT_TOTAL_TEXT, (
        f"account-total reads {text_of(total)!r}, expected {RENT_TOTAL_TEXT!r}"
    )

    rows = family(page, "account-txn-")
    expect(rows).to_have_count(len(RENT_ROW_LINE_NOS), timeout=LOAD_TIMEOUT)
    assert line_nos(rows, "account-txn-") == RENT_ROW_LINE_NOS, (
        f"rent rows are {line_nos(rows, 'account-txn-')} in document order, "
        f"expected {RENT_ROW_LINE_NOS}"
    )

    for line_no, expected in RENT_RUNNING_TEXT.items():
        cell = by_testid(page, f"txn-running-{line_no}")
        assert text_of(cell) == expected, (
            f"txn-running-{line_no} reads {text_of(cell)!r}, expected {expected!r}"
        )


def test_c_2_4_an_unknown_account_is_a_404_and_a_known_one_is_a_200(page):
    """c-2-4: /accounts/nope responds 404 and renders an element with data-testid
    account-missing and text `Account not found`, /accounts/utilities responds
    404, /accounts/Rent responds 404, and /accounts/salary responds 200 and
    renders account-title with text salary and account-total with text
    62000.00.

    utilities is named only by the rejected line 25, so a parser that accepted
    that line would answer 200 here. Rent is the case-sensitivity fixture: the
    match is exact, so /accounts/Rent misses while /accounts/rent hits.

    The 404s alone would be green on an unwritten build - with cut-account-rows
    empty every account page 404s - so the salary half is what makes this
    criterion bite, and its account-total is what ties it to
    cut-account-totals. ambiguity.md W3 notes the total's source is not
    otherwise observable; c-2-5 reads the sidebar total, which can only come
    from accountTotals.
    """
    missing_response = open_account(page, "nope")
    assert missing_response is not None and missing_response.status == 404, (
        f"/accounts/nope answered "
        f"{missing_response.status if missing_response else 'no response'}, "
        f"expected 404"
    )
    missing = by_testid(page, "account-missing")
    expect(missing).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(missing) == "Account not found", (
        f"account-missing reads {text_of(missing)!r}, expected 'Account not found'"
    )

    for name in ("utilities", "Rent"):
        response = open_account(page, name)
        assert response is not None and response.status == 404, (
            f"/accounts/{name} answered "
            f"{response.status if response else 'no response'}, expected 404"
        )

    salary_response = open_account(page, "salary")
    assert salary_response is not None and salary_response.status == 200, (
        f"/accounts/salary answered "
        f"{salary_response.status if salary_response else 'no response'}, "
        f"expected 200"
    )
    title = by_testid(page, "account-title")
    expect(title).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(title) == "salary", f"account-title reads {text_of(title)!r}"
    total = by_testid(page, "account-total")
    assert text_of(total) == SALARY_TOTAL_TEXT, (
        f"account-total reads {text_of(total)!r}, expected {SALARY_TOTAL_TEXT!r}"
    )


def test_c_2_5_salary_running_column_and_the_sidebar_of_four_linked_accounts(page):
    """c-2-5: /accounts/salary renders txn-running-4, txn-running-16 and
    txn-running-23 with texts 45000.00, 57000.00 and 62000.00, renders exactly 4
    elements with data-testid account-link-<name> whose names in document order
    are food, rent, salary and travel, renders account-link-food with href
    /accounts/food, and renders account-list-total-food with text -5425.55.

    This is the second running-balance fixture and it is an all-positive
    account, so the scan is graded on a shape c-2-3's all-negative rent column
    does not reach - a sign error or a subtraction passes neither. Nor does a
    constant: the three texts differ from each other and from rent's three.

    The sidebar is enumerated on `account-link-`, a prefix of no other testid
    (`account-list-total-` diverges at the third character), and the names are
    compared as a whole ordered list, so the count and the ascending order are
    one assertion. Reading taken: "whose names in document order" is read off
    the `<name>` in each data-testid, the same way c-2-3 reads "whose lineNo
    values in document order" off `account-txn-<lineNo>`. The href is read as an
    attribute, so the sidebar is real navigation and not four spans with the
    right testids.
    """
    response = open_account(page, "salary")
    assert response is not None and response.status == 200, (
        f"/accounts/salary answered "
        f"{response.status if response else 'no response'}, expected 200"
    )

    for line_no, expected in SALARY_RUNNING_TEXT.items():
        cell = by_testid(page, f"txn-running-{line_no}")
        assert text_of(cell) == expected, (
            f"txn-running-{line_no} reads {text_of(cell)!r}, expected {expected!r}"
        )

    links = family(page, "account-link-")
    expect(links).to_have_count(len(ACCOUNT_NAMES), timeout=LOAD_TIMEOUT)
    assert suffixes(links, "account-link-") == ACCOUNT_NAMES, (
        f"sidebar links are {suffixes(links, 'account-link-')} in document "
        f"order, expected {ACCOUNT_NAMES}"
    )

    food_link = by_testid(page, "account-link-food")
    assert food_link.get_attribute("href") == "/accounts/food", (
        f"account-link-food has href {food_link.get_attribute('href')!r}, "
        f"expected '/accounts/food'"
    )

    food_total = by_testid(page, "account-list-total-food")
    assert text_of(food_total) == FOOD_TOTAL_TEXT, (
        f"account-list-total-food reads {text_of(food_total)!r}, "
        f"expected {FOOD_TOTAL_TEXT!r}"
    )
