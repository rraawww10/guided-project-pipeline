import os
import re
from playwright.sync_api import sync_playwright


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def test_c_1_2_sc_dashboard_renders_one_row_per_position():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_selector('[data-testid^="pos-row-"]', timeout=5000)
        count = page.locator('[data-testid^="pos-row-"]').count()
        assert count >= 1
        browser.close()


def test_c_1_3_sc_dashboard_shows_weight_percentage_cell():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_selector('[data-testid^="pos-weight-"]', timeout=5000)
        texts = page.locator('[data-testid^="pos-weight-"]').all_text_contents()
        assert any(re.fullmatch(r"\d+(?:\.\d)?%", t.strip()) for t in texts)
        browser.close()
