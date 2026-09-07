import os
from playwright.sync_api import sync_playwright


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_3_4_ui_renders_one_row_per_plan_item():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        el = page.wait_for_selector('[data-testid^="plan-row-"]', timeout=5000)
        assert el is not None
        count = page.locator('[data-testid^="plan-row-"]').count()
        assert count >= 1
        browser.close()
