"""Fixtures: one browser for the session, a fresh context per test, and an
httpx client pointed at the running app.

The app is already running when this suite runs; its URL arrives in BASE_URL.
Nothing here boots, builds, installs or migrates anything.

**There is no world to reset, and nothing here reads APP_DIR.** spec.md, "Out of
scope": "`data/ledger.txt` ships in the repository, is read on every request, and
is never modified - so ... the suite has no world to reset, and every test may
run in any order any number of times and get the same answer." So there is no
store fixture: the tenth run in a working copy answers exactly as the first,
which is what the nightly watchdog replays.
"""
from __future__ import annotations

import httpx
import pytest
from playwright.sync_api import sync_playwright

from helpers import base_url as read_base_url


@pytest.fixture(scope="session")
def base_url() -> str:
    return read_base_url()


@pytest.fixture(scope="session")
def _playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(_playwright):
    browser = _playwright.chromium.launch()
    yield browser
    browser.close()


@pytest.fixture
def page(browser):
    """A fresh context per test, so no test inherits another test's page."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def api(base_url: str):
    """Plain HTTP against the running app - used for both JSON endpoints and
    for the HTTP status of a page route, which is what c-2-3 and c-2-4 pin."""
    with httpx.Client(base_url=base_url, timeout=30.0,
                      follow_redirects=False) as client:
        yield client
