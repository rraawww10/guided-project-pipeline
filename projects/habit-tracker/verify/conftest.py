"""Fixtures: one browser for the session, a fresh context per test, and a
store reset around every single test.

The app is already running. BASE_URL is read from the environment and nothing
in this suite boots, builds or installs anything.
"""
from __future__ import annotations

import httpx
import pytest
from playwright.sync_api import sync_playwright

from helpers import base_url as read_base_url
from helpers import reset_store


@pytest.fixture(scope="session")
def base_url() -> str:
    return read_base_url()


@pytest.fixture(autouse=True)
def clean_store():
    """Delete the app's live store before and after every test.

    The app rebuilds `data/habits.json` from the seed on the next request, so
    each test starts from the seeded world whatever the test before it wrote,
    and the suite leaves nothing behind for the next run.
    """
    reset_store()
    yield
    reset_store()


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
    """A fresh context per test, so no test inherits another test's state."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def api(base_url: str):
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client
