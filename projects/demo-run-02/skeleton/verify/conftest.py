import os
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def _playwright():
    p = sync_playwright().start()
    try:
        yield p
    finally:
        p.stop()


@pytest.fixture()
def page(_playwright):
    # Launch a fresh browser per test to isolate UI state
    browser = _playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    try:
        base_url = os.environ.get("BASE_URL")
        if not base_url:
            raise RuntimeError("BASE_URL is not set in the environment")
        page.goto(base_url.rstrip("/") + "/")
        yield page
    finally:
        context.close()
        browser.close()
