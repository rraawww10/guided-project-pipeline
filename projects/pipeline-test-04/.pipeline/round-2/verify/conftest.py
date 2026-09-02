"""Fixtures: one browser for the session, a fresh context per test, and an
httpx client pointed at the running app.

The app is already running when this suite runs. Its URL arrives in `BASE_URL`
and nothing here boots, builds, installs or sleeps.

There is no store fixture and no `APP_DIR` lookup, because there is nothing to
reset. spec.md, Out of scope: "Saving a scored game back to the store. Scoring
is a pure read; nothing in this project writes a file, so no test has to reset
one and `data/games.json` ships as a tracked seed." So every test may run in any
order any number of times in the same working copy and get the same answer,
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
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client
