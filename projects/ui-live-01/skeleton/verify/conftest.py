import os
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def base_url() -> str:
    # The harness sets BASE_URL when running tests.
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL must be set by the test runner"
    return url.rstrip("/")


@pytest.fixture(scope="function")
def page(base_url):
    # Spin up a fresh browser context per test to avoid cross-test state.
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        pg = context.new_page()
        # Keep timeouts tight so missing UI/endpoint fails fast during red-first.
        pg.set_default_timeout(5000)
        yield pg
        context.close()
        browser.close()
