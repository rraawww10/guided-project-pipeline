import os
import pytest
import httpx
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL must be set by the test runner"
    return url.rstrip("/")


@pytest.fixture()
def http_client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        yield client


@pytest.fixture()
def page(base_url: str):
    # Launch a fresh page per test to keep state isolated
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(base_url=base_url)
        try:
            pg = context.new_page()
            yield pg
        finally:
            context.close()
            browser.close()
