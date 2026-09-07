import os
from playwright.sync_api import sync_playwright


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_5_2_click_apply_shows_applied_notice():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_selector('[data-testid="apply-plan"]', timeout=5000)
        page.locator('[data-testid="apply-plan"]').click()
        el = page.wait_for_selector('[data-testid="applied"]', timeout=5000)
        assert el is not None
        browser.close()
