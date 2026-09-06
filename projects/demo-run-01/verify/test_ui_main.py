import os

import pytest
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_URL = os.environ["BASE_URL"]


@pytest.mark.sync
def test_c_1_2_renders_10_cards():
    """
    c-1-2: sc-main renders 10 elements with data-testid="card" on "/"
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(BASE_URL + "/", wait_until="load")
            # Expect exactly 10 candidate cards rendered
            locator = page.get_by_test_id("card")
            # give the UI a short time to load
            locator.first.wait_for(timeout=5000)
            count = locator.count()
            assert count == 10, f"expected 10 cards, got {count}"
        finally:
            browser.close()


@pytest.mark.sync
def test_c_1_3_renders_both_toggles():
    """
    c-1-3: sc-main renders checkboxes with data-testids "toggle-years" and "toggle-tag"
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(BASE_URL + "/", wait_until="load")
            years = page.get_by_test_id("toggle-years")
            tag = page.get_by_test_id("toggle-tag")
            years.wait_for(timeout=5000)
            tag.wait_for(timeout=5000)
            assert years.is_visible()
            assert tag.is_visible()
            # Also assert they are rendered as unchecked inputs on first load
            # (initial state: no active tokens). This remains an assertion on what the user sees.
            assert years.is_checked() is False
            assert tag.is_checked() is False
        finally:
            browser.close()