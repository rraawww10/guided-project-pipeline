"""Fixtures: one browser for the session, a fresh context per test.

The app is already running. BASE_URL is read from the environment and nothing
in this suite boots, builds or installs anything.
"""
from __future__ import annotations

import os

import httpx
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ["BASE_URL"].rstrip("/")


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
