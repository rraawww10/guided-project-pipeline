"""Fixtures: an httpx client on the running app, one browser for the session and
a fresh browser context per test.

The app is already running. BASE_URL is read from the environment and nothing in
this suite boots, builds or installs anything.

There is no store-reset fixture, and that is a decision, not an omission: this
app writes nothing to disk (spec.md, "Data model" and "Repeatability"), so the
world every test starts from is the `const` in `lib/boards.ts` and no test can
leave the next one a different one. What a test *can* leak is browser state -
open cells and flags live in React - so every test gets its own context and its
own page.
"""
from __future__ import annotations

import httpx
import pytest
from playwright.sync_api import sync_playwright

from helpers import base_url as read_base_url


@pytest.fixture(scope="session")
def base_url() -> str:
    return read_base_url()


@pytest.fixture
def api(base_url: str):
    """HTTP client on the running app, for the endpoint criteria."""
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client


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
    """A fresh context per test, so no test inherits another test's React state."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
