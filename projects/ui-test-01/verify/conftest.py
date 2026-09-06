"""Fixtures: one browser for the session and a fresh context per test.

The app is already running when this suite runs. BASE_URL is read from the
environment and nothing here boots, builds or installs anything.

Every wait is a retrying Playwright wait, never a sleep. Tests target exact
visible strings the spec pins (e.g. labels like "Paycheck", headings like
"Scenario A"/"Scenario B"). Where the spec leaves editor controls unstated,
helpers try a small set of sensible, labelled controls and fail with an
actionable message; see helpers.py for notes. Ambiguities we had to choose are
called out in each test as comments.
"""
from __future__ import annotations

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
