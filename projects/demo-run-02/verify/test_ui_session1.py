import os
import pytest
from playwright.sync_api import expect

BASE_URL = os.environ["BASE_URL"].rstrip("/")


def test_c_1_2_home_renders_4_expense_rows(page):
    page.goto(BASE_URL + "/")
    rows = page.locator('[data-testid="expense-row"]')
    expect(rows).to_have_count(4)


def test_c_1_3_totals_paid_summary_5_rows_with_exact_amounts(page):
    page.goto(BASE_URL + "/")
    # Assert each expected totals-paid line is rendered exactly somewhere on the page
    expected = [
        "Alice $52.00",
        "Bob $30.00",
        "Cara $40.00",
        "Dan $15.00",
        "Eve $0.00",
    ]
    for text in expected:
        loc = page.get_by_text(text, exact=True)
        expect(loc).to_be_visible()
