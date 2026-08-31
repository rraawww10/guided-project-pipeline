"""Shared fixture data and screen helpers for the Ledger suite.

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, picks a port or installs anything, and every wait is a retrying
Playwright wait, never a sleep.

**Nothing here reads APP_DIR and no test touches a file the app owns.** spec.md,
"Out of scope": the seed file ships read-only, nothing is written at runtime, so
there is no world to reset and every test may run any number of times in the same
working copy and get the same answer.

Everything below is copied from spec.md - the seed-file block, the four reason
constants, the account table and the two running-balance tables. It is this
suite's own fixture data: the tests never ask the app what the answer is.
"""
from __future__ import annotations

import os
import re

from playwright.sync_api import Locator, Page

# a screen has to load (and, on `/`, fetch) before anything can be read
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the four reason strings, exactly as spec.md pins them in lib/ledger.ts
# --------------------------------------------------------------------------
BAD_DATE = "date must be YYYY-MM-DD"
NO_ACCOUNT = "account must not be empty"
BAD_AMOUNT = "amount must be a rupee amount like -250.00"


def bad_fields(n: int) -> str:
    return f"expected 4 fields, found {n}"


# --------------------------------------------------------------------------
# the seed file's answer, from spec.md "The seed file"
# --------------------------------------------------------------------------
# 21 accepted entries; lines 1-3 are skipped, the other six are diagnostics
ACCEPTED_LINE_NOS = [4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20, 21,
                     23, 24, 26, 27, 29, 30]

# the six broken lines, in ascending lineNo order, with their one reason each
DIAGNOSTICS = [
    {"lineNo": 9, "reason": BAD_DATE},
    {"lineNo": 13, "reason": NO_ACCOUNT},
    {"lineNo": 17, "reason": bad_fields(3)},
    {"lineNo": 22, "reason": BAD_DATE},
    {"lineNo": 25, "reason": BAD_AMOUNT},
    {"lineNo": 28, "reason": BAD_AMOUNT},
]

ENTRY_FIRST = {"lineNo": 4, "date": "2026-01-01", "account": "salary",
               "description": "january pay", "paise": 4500000}
ENTRY_LAST = {"lineNo": 30, "date": "2026-01-27", "account": "food",
              "description": "lunch", "paise": -18000}

# c-1-3's five amount fixtures: lineNo -> paise. Four have non-zero paise
# digits and line 8 is the one a float multiply gets wrong (250.05 * 100).
PAISE_FIXTURES = {8: -25005, 6: -245075, 19: -110550, 10: -12050, 16: 1200000}

# spec.md, the account table - already in ascending account order
ACCOUNT_TOTALS = [
    {"account": "food", "paise": -542555},
    {"account": "rent", "paise": -3720000},
    {"account": "salary", "paise": 6200000},
    {"account": "travel", "paise": -455550},
]
ACCOUNT_NAMES = [t["account"] for t in ACCOUNT_TOTALS]

# spec.md, the two running-balance tables: lineNo -> formatPaise(running)
RENT_ROWS = [5, 11, 20]
RENT_RUNNING = {5: "-18000.00", 11: "-19200.00", 20: "-37200.00"}
SALARY_ROWS = [4, 16, 23]
SALARY_RUNNING = {4: "45000.00", 16: "57000.00", 23: "62000.00"}


def format_paise(paise: int) -> str:
    """formatPaise as spec.md defines it: sign, floor(abs/100), '.', remainder
    as two digits. -542555 reads -5425.55 and 4500000 reads 45000.00.

    Used only to state an expectation the spec already prints as a literal, so
    the criterion's quoted string and this suite cannot drift apart.
    """
    sign = "-" if paise < 0 else ""
    whole, rest = divmod(abs(paise), 100)
    return f"{sign}{whole}.{rest:02d}"


# The two running tables are keyed by the same lineNos, in the same order, as the
# row lists the criteria pin; if they ever disagree the suite says so at import.
assert list(RENT_RUNNING) == RENT_ROWS
assert list(SALARY_RUNNING) == SALARY_ROWS

# The literals the criteria quote must equal formatPaise of the pinned paise;
# if the two ever disagree the suite says so at import time.
assert format_paise(-542555) == "-5425.55"
assert format_paise(4500000) == "45000.00"
assert format_paise(-3720000) == "-37200.00"
assert format_paise(6200000) == "62000.00"


# --------------------------------------------------------------------------
# the screens - every lookup goes through a data-testid the spec pins.
# Nothing here reads a class name or any styling.
# --------------------------------------------------------------------------
def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


def open_path(page: Page, path: str) -> None:
    page.goto(f"{base_url()}{path}", wait_until="domcontentloaded")


def text_of(locator: Locator) -> str:
    return normalize(locator.text_content())


def prefixed(page: Page, prefix: str) -> Locator:
    """Every element whose data-testid starts with `prefix`, in document order."""
    return page.locator(f'[data-testid^="{prefix}"]')


def testids(locator: Locator) -> list[str]:
    return [(el.get_attribute("data-testid") or "") for el in locator.all()]


def numbered_testids(page: Page, prefix: str) -> list[int]:
    """The <lineNo> of every element whose data-testid is EXACTLY prefix+digits,
    in document order.

    Exact, not prefix. ambiguity.md W3 reports that `account-entry-` is also a
    prefix of `account-entry-date-5`, `-desc-5`, `-amount-5` and `-running-5`, so
    a prefix locator counts 15 elements where c-2-3 pins 3. The reading taken
    here is the one the criterion's own words support - "3 elements with
    data-testid account-entry-<lineNo>", i.e. the three row wrappers - so the
    prefix locator is filtered down to testids that are the prefix and a number
    and nothing else.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    out: list[int] = []
    for tid in testids(prefixed(page, prefix)):
        m = pattern.match(tid)
        if m:
            out.append(int(m.group(1)))
    return out


def named_testids(page: Page, prefix: str) -> list[str]:
    """The <name> of every element whose data-testid is EXACTLY prefix+name,
    in document order. Account names are lowercase ascii letters only (spec.md,
    "Out of scope"), so the name part is matched as [a-z]+ and nothing else.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}([a-z]+)$")
    out: list[str] = []
    for tid in testids(prefixed(page, prefix)):
        m = pattern.match(tid)
        if m:
            out.append(m.group(1))
    return out
