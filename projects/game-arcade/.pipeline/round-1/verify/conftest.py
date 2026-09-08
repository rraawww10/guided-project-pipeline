# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Iterator

import pytest
import httpx

try:
    # Playwright is provided by the runner; use the sync API to avoid extra plugins
    from playwright.sync_api import sync_playwright, Page
except Exception:  # pragma: no cover - collected environment guarantees playwright
    sync_playwright = None  # type: ignore
    Page = object  # type: ignore


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set; the test runner must start the app and set it"
    return url.rstrip("/")


@pytest.fixture(scope="session")
def app_dir() -> Path:
    # APP_DIR is set by the runner for its two runs; when a student runs pytest by hand,
    # it is absent, so fall back to the cwd which will be the skeleton root.
    return Path(os.environ.get("APP_DIR", os.getcwd()))


@pytest.fixture()
def client(base_url: str) -> Iterator[httpx.Client]:
    c = httpx.Client(base_url=base_url, timeout=10.0)
    try:
        yield c
    finally:
        c.close()


@pytest.fixture()
def page(base_url: str) -> Iterator[Page]:
    # Fresh browser context per test; database state is NOT reset here.
    assert sync_playwright is not None, "playwright is required for UI tests"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(base_url=base_url)
        try:
            page = context.new_page()
            yield page
        finally:
            context.close()
            browser.close()
