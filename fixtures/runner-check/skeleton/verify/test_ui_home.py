import os
import pytest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ["BASE_URL"]


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page()
        yield pg
        browser.close()


def test_renders_three_items(page):
    page.goto(BASE, wait_until="networkidle")
    expect(page.get_by_test_id("item")).to_have_count(3)


def test_shows_heading(page):
    page.goto(BASE, wait_until="networkidle")
    expect(page.get_by_role("heading", name="Runner Check")).to_be_visible()
