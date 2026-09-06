import os
import re

import pytest
from playwright.sync_api import sync_playwright


BASE_URL = os.environ["BASE_URL"]


@pytest.mark.sync
def test_c_2_3_years_toggle_shows_two_decimal_scores():
    """
    c-2-3: On "/" with years toggle on, each card renders a score text data-testid="score" formatted to two decimals
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(BASE_URL + "/", wait_until="load")
            # Turn on the years toggle
            page.get_by_test_id("toggle-years").check()
            # Wait for scores to render
            page.get_by_test_id("score").first.wait_for(timeout=5000)
            scores = page.get_by_test_id("score").all_text_contents()
            assert len(scores) > 0
            # Each score reads like 0.60, 1.00, 1.75 etc.
            for txt in scores:
                assert re.fullmatch(r"-?\d+(?:\.\d{2})", txt.strip()), f"bad score format: {txt!r}"
        finally:
            browser.close()


@pytest.mark.sync
def test_c_2_4_years_toggle_reasons_contains_years():
    """
    c-2-4: On "/" with years toggle on, at least one card's data-testid="reasons" contains the word "years"
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(BASE_URL + "/", wait_until="load")
            # Turn on the years toggle so the scorer includes the years signal
            page.get_by_test_id("toggle-years").check()
            # Wait for reasons to appear
            page.get_by_test_id("reasons").first.wait_for(timeout=5000)
            reasons_texts = [el.inner_text().lower() for el in page.get_by_test_id("reasons").all()]
            assert any("years" in t for t in reasons_texts), "expected at least one reasons summary to mention 'years'"
        finally:
            browser.close()