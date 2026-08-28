"""Fixtures: one browser for the session, a fresh context per test, one httpx
client per test.

The app is already running. BASE_URL is read from the environment and nothing in
this suite boots, builds, installs or picks a port.

There is no store-reset fixture, and that is deliberate. spec.md, "Data model":
"Nothing is written to disk. The boards are a `const` in `lib/boards.ts`, every
endpoint is a pure function of that constant plus its request, and both screens
hold their own state in React." So there is no file the app owns, nothing for a
test to reset, and nothing a test can leave behind for the next one. Every test
below starts from the same seeded world on its first run and its hundredth, in
any order. APP_DIR is never read for the same reason - this suite owns no path
into the running app's directory.
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
    """A fresh context per test, so no test inherits another test's React state."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def api(base_url: str):
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client
