"""Shared fixture data and screen helpers for the Ledger suite.

The app is already running; its URL arrives in `BASE_URL`. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**There is no world to reset.** spec.md, Out of scope: there is no POST, PUT,
PATCH or DELETE, and `data/ledger.txt` "ships in the repository, is read on every
request, and is never modified - so `app/.gitignore` needs no store entry, the
suite has no world to reset, and every test may run in any order any number of
times and get the same answer." So no test writes a file the app owns, and
nothing here reads `APP_DIR` - there is nothing under it this suite needs. The
tenth run in a working copy answers as the first, which is what the nightly
watchdog replays.

Every number and every string below is copied from spec.md - the seed block, the
broken-lines table, the account totals table and the running-balance table. They
are this suite's own fixture data: no test asks the app what the answer is, and
no test re-derives an answer with the logic the app is being graded on.

Every lookup goes through a `data-testid` the spec pins. spec.md, Screens:
"Every element a criterion reads is pinned to a `data-testid`, so styling is
free and the same selector reads in the skeleton. Every `data-testid` a
criterion names is matched exactly, never as a prefix." `get_by_test_id` matches
the attribute exactly; the `^=` locators below are only ever used to enumerate a
family whose prefix belongs to no other testid in the spec, and the ids they
find are then compared as one ordered list.
"""
from __future__ import annotations

import os

from playwright.sync_api import Locator, Page

# a screen has to load - and on `/`, fetch and render - before anything reads
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the seed file, as spec.md pins it
# --------------------------------------------------------------------------
# spec.md, "The seed file": 30 lines, lines 1 and 2 comments, line 3 empty, so
# 21 accepted entries and 6 diagnostics. The lineNo values are 1-based over that
# block and are what a Diagnostic and an entry-row-<lineNo> carry.
ENTRY_LINE_NOS: list[int] = [
    4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 21, 23, 24, 26, 27, 29, 30,
]
DIAGNOSTIC_LINE_NOS: list[int] = [9, 13, 17, 22, 25, 28]

# spec.md, "The four reason strings, and their order", plus the table of the six
# lines broken on purpose. Line 17 reads the field-count message and not a date
# complaint, which is the rule order c-1-2 grades.
BAD_DATE = "date must be YYYY-MM-DD"
NO_ACCOUNT = "account must not be empty"
BAD_AMOUNT = "amount must be a rupee amount like -250.00"
REASONS: dict[int, str] = {
    9: BAD_DATE,
    13: NO_ACCOUNT,
    17: "expected 4 fields, found 3",
    22: BAD_DATE,
    25: BAD_AMOUNT,
    28: BAD_AMOUNT,
}

# c-1-1's two pinned entries.
FIRST_ENTRY = {
    "lineNo": 4,
    "date": "2026-01-01",
    "account": "salary",
    "description": "january pay",
    "paise": 4500000,
}
LAST_ENTRY = {
    "lineNo": 30,
    "date": "2026-01-27",
    "account": "food",
    "description": "lunch",
    "paise": -18000,
}
# Line 20 is `2026-02-30`: a calendar-checking parser rejects it, this one keeps
# the string it was given.
ROLLOVER_LINE_NO = 20
ROLLOVER_DATE = "2026-02-30"

# c-1-3: five paise values, four of them with non-zero paise digits.
PAISE_BY_LINE: dict[int, int] = {
    8: -25005,
    6: -245075,
    19: -110550,
    10: -12050,
    16: 1200000,
}

# spec.md, "The four accounts, their totals in paise": sorted by account
# ascending, which is the order GET /api/accounts answers in.
ACCOUNT_NAMES: list[str] = ["food", "rent", "salary", "travel"]
ACCOUNT_PAISE: list[int] = [-542555, -3720000, 6200000, -455550]
FOOD_TOTAL_TEXT = "-5425.55"
RENT_TOTAL_PAISE = -3720000
RENT_TOTAL_TEXT = "-37200.00"
SALARY_TOTAL_TEXT = "62000.00"

# spec.md, "Running balances, which c-2-3 and c-2-5 pin".
RENT_ROW_LINE_NOS: list[int] = [5, 11, 20]
RENT_RUNNING_TEXT: dict[int, str] = {
    5: "-18000.00",
    11: "-19200.00",
    20: "-37200.00",
}
SALARY_ROW_LINE_NOS: list[int] = [4, 16, 23]
SALARY_RUNNING_TEXT: dict[int, str] = {
    4: "45000.00",
    16: "57000.00",
    23: "62000.00",
}


# --------------------------------------------------------------------------
# the endpoints
# --------------------------------------------------------------------------
def get_ledger(api) -> dict:
    """GET /api/ledger, checked down to the two arrays every criterion reads."""
    response = api.get("/api/ledger")
    assert response.status_code == 200, (
        f"GET /api/ledger answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, dict), f"body is {type(body).__name__}, not a JSON object"
    for key in ("entries", "diagnostics"):
        assert key in body, f"body has no {key} key: {body}"
        assert isinstance(body[key], list), (
            f"{key} is {type(body[key]).__name__}, not a JSON array"
        )
    return body


def get_accounts(api) -> list[dict]:
    """GET /api/accounts, checked down to the array every criterion reads."""
    response = api.get("/api/accounts")
    assert response.status_code == 200, (
        f"GET /api/accounts answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, not a JSON array"
    for item in body:
        assert isinstance(item, dict), f"entry is {item!r}, not an object"
    return body


def one_by_line_no(items: list[dict], line_no: int, what: str) -> dict:
    """The single object carrying this lineNo, found by lineNo and never by index.

    c-1-2 and c-1-3 each read specific file lines, so this is the lookup they
    use; a duplicate or a miss fails here rather than reading a wrong object.
    """
    found = [i for i in items if i.get("lineNo") == line_no]
    assert len(found) == 1, (
        f"expected exactly 1 {what} with lineNo {line_no}, "
        f"found {len(found)}: {found}"
    )
    return found[0]


# --------------------------------------------------------------------------
# the screens
# --------------------------------------------------------------------------
def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


def open_ledger(page: Page):
    """Open `/` - sc-ledger, the client component that fetches GET /api/ledger."""
    return page.goto(f"{base_url()}/", wait_until="domcontentloaded")


def open_account(page: Page, name: str):
    """Open `/accounts/<name>` and hand back the main response, so a test reads
    the HTTP status the route answered as well as what it rendered."""
    return page.goto(f"{base_url()}/accounts/{name}", wait_until="domcontentloaded")


def by_testid(page: Page, value: str) -> Locator:
    """One exact data-testid match - never a prefix match."""
    return page.get_by_test_id(value)


def family(page: Page, prefix: str) -> Locator:
    """Every element whose data-testid starts with `prefix`.

    Used only with a prefix that is the prefix of no other testid in the spec:
    `entry-row-`, `reject-row-`, `account-txn-` and `account-link-`. What it
    finds is compared as one ordered list, so an extra member fails too.
    """
    return page.locator(f'[data-testid^="{prefix}"]')


def suffixes(locator: Locator, prefix: str) -> list[str]:
    """The tail of each data-testid the locator finds, in document order."""
    return [
        (el.get_attribute("data-testid") or "")[len(prefix):]
        for el in locator.all()
    ]


def line_nos(locator: Locator, prefix: str) -> list[int]:
    """The <lineNo> of each data-testid the locator finds, in document order."""
    tails = suffixes(locator, prefix)
    for tail in tails:
        assert tail.isdigit(), f"{prefix}{tail} does not end in a line number"
    return [int(t) for t in tails]


def text_of(locator: Locator) -> str:
    """The element's text, whitespace-collapsed, waited for with LOAD_TIMEOUT.

    `text_content()` retries until the element exists. The timeout is passed
    explicitly so a missing element - which is what the skeleton renders where
    a cut is still open - fails on this suite's own 20s budget rather than on
    Playwright's hidden 30s default.
    """
    return normalize(locator.text_content(timeout=LOAD_TIMEOUT))
