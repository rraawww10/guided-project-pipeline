"""Fixtures: one browser for the session, a fresh context per test, and an
httpx client pointed at the running app.

The app is already running. BASE_URL is read from the environment and nothing
in this suite boots, builds or installs anything.

There is no `clean_store` fixture here and that is deliberate. spec.md's Data
model says the project writes no file at runtime - the three puzzles are
compiled in and the board lives in React state - so there is no world for a
test to reset and no APP_DIR to resolve. Isolation comes from the fresh browser
context per test, which gives every test an empty board, and from the API tests
being pure requests.
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
    """A fresh context per test, so no test inherits another test's board."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def api(base_url: str):
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client
