"""sc-account - route /accounts/[name], the per-account page and its sidebar.

One test per criterion. The page is a server component, so its HTTP status is
part of what the criteria pin: the status is read with the plain HTTP client and
the markup with Playwright, both against the same running app.

Every element is found through the data-testid the spec pins - nothing here reads
a class name or any styling. Row wrappers are matched exactly and never by
prefix: ambiguity.md W3 records that `account-entry-` is also a prefix of
`account-entry-date-5`, `-desc-5`, `-amount-5` and `-running-5`, so a prefix
locator counts 15 where c-2-3 pins 3. The reading taken here is the criterion's
own words - three elements with data-testid `account-entry-<lineNo>`, the three
row wrappers.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    ACCOUNT_NAMES,
    LOAD_TIMEOUT,
    RENT_ROWS,
    RENT_RUNNING,
    SALARY_RUNNING,
    named_testids,
    numbered_testids,
    open_path,
    text_of,
)


def test_c_2_3_rent_page_walks_three_rows_down_to_the_account_total(api, page):
    """c-2-3: /accounts/rent responds 200 and renders account-title with text
    rent, account-total with text -37200.00, exactly 3 elements with data-testid
    account-entry-<lineNo> whose lineNo values in document order are 5, 11 and
    20, and account-entry-running-5, account-entry-running-11 and
    account-entry-running-20 with texts -18000.00, -19200.00 and -37200.00.

    Three running values, not one: -18000.00 is the first row's own amount,
    -19200.00 needs the earlier row added to it, and -37200.00 has to land on the
    account total, so a column that echoes each row's amount and a column that
    repeats the total both fail. The rows are lines 5, 11 and 20 - line 28 is a
    rent line the parser rejects and it must not appear here either.
    """
    r = api.get("/accounts/rent")
    assert r.status_code == 200, (
        f"/accounts/rent answered {r.status_code}, expected 200"
    )

    open_path(page, "/accounts/rent")
    expect(page.get_by_test_id("account-title")).to_have_text(
        "rent", timeout=LOAD_TIMEOUT)
    expect(page.get_by_test_id("account-total")).to_have_text("-37200.00")

    rows = numbered_testids(page, "account-entry-")
    assert len(rows) == 3, (
        f"the page draws {len(rows)} account-entry-<lineNo> rows, expected 3: {rows!r}"
    )
    assert rows == RENT_ROWS, (
        f"account-entry lineNo values in document order are {rows!r}"
    )

    running = {
        n: text_of(page.get_by_test_id(f"account-entry-running-{n}"))
        for n in RENT_ROWS
    }
    assert running == RENT_RUNNING, f"the running column reads {running!r}"


def test_c_2_4_an_account_no_accepted_entry_names_is_a_404(api, page):
    """c-2-4: /accounts/nope responds 404 and renders an element with data-testid
    account-missing and text Account not found, /accounts/utilities responds 404,
    /accounts/Rent responds 404, and /accounts/salary responds 200 and renders
    account-title with text salary.

    utilities is named only by the rejected line 25, so it is not an account;
    Rent is the case-sensitivity case, a name no entry carries. The three 404s
    are all green while cut-account-rows is unwritten - every account page 404s
    then - so the last pair is what makes this test red before the code exists.
    """
    for path in ("/accounts/nope", "/accounts/utilities", "/accounts/Rent"):
        r = api.get(path)
        assert r.status_code == 404, (
            f"{path} answered {r.status_code}, expected 404 - no accepted entry "
            f"names that account"
        )

    open_path(page, "/accounts/nope")
    expect(page.get_by_test_id("account-missing")).to_have_text(
        "Account not found", timeout=LOAD_TIMEOUT)

    salary = api.get("/accounts/salary")
    assert salary.status_code == 200, (
        f"/accounts/salary answered {salary.status_code}, expected 200"
    )
    open_path(page, "/accounts/salary")
    expect(page.get_by_test_id("account-title")).to_have_text(
        "salary", timeout=LOAD_TIMEOUT)


def test_c_2_5_salary_page_scans_an_all_positive_account_beside_the_sidebar(page):
    """c-2-5: /accounts/salary renders account-entry-running-4,
    account-entry-running-16 and account-entry-running-23 with texts 45000.00,
    57000.00 and 62000.00, renders account-total with text 62000.00, renders
    exactly 4 elements with data-testid account-link-<name> whose names in
    document order are food, rent, salary and travel, and renders
    account-list-total-food with text -5425.55.

    The second running-balance fixture, on an all-positive account, so the scan
    is graded on two different shapes: 45000, 57000 and 62000 are three distinct
    partial sums that neither the row amounts nor the total reproduce. The
    sidebar is graded on the same page - four names in ascending order and food's
    total, -5425.55, which is nine rows folded and cannot come from this page's
    own rows.
    """
    open_path(page, "/accounts/salary")
    expect(page.get_by_test_id("account-total")).to_have_text(
        "62000.00", timeout=LOAD_TIMEOUT)

    running = {
        n: text_of(page.get_by_test_id(f"account-entry-running-{n}"))
        for n in SALARY_RUNNING
    }
    assert running == SALARY_RUNNING, f"the running column reads {running!r}"

    links = named_testids(page, "account-link-")
    assert len(links) == 4, (
        f"the sidebar draws {len(links)} account-link-<name> anchors, expected 4: "
        f"{links!r}"
    )
    assert links == ACCOUNT_NAMES, (
        f"account-link names in document order are {links!r}"
    )

    food_total = text_of(page.get_by_test_id("account-list-total-food"))
    assert food_total == "-5425.55", (
        f"account-list-total-food reads {food_total!r}, expected -5425.55"
    )
