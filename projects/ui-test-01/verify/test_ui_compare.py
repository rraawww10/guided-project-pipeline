"""sc-compare at /compare. One test per criterion for session 3.

Ambiguities taken:
- A3: The share URL encodes BOTH scenarios (A and B) and restores both.
- A4: Each column shows Undo and Redo buttons that affect only that column.
- W7: Each column is a full scenario with its own paycheck, envelopes and rules.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    column_scope,
    open_compare,
    result_amount,
    set_paycheck,
    add_fixed_rule,
    add_percent_rule,
    share_url_input,
)


def test_c_3_1_compare_renders_two_columns_with_editors_and_results(page):
    """c-3-1: sc-compare renders headings 'Scenario A' and 'Scenario B' and
    shows one editor and one results list under each heading."""
    open_compare(page)
    # Two headings present
    hA = page.get_by_role("heading", name="Scenario A", exact=True)
    hB = page.get_by_role("heading", name="Scenario B", exact=True)
    expect(hA).to_be_attached(timeout=LOAD_TIMEOUT)
    expect(hB).to_be_attached(timeout=LOAD_TIMEOUT)
    # Each column has its own Paycheck input (the editor) and can render results
    colA = column_scope(page, "Scenario A")
    colB = column_scope(page, "Scenario B")
    expect(colA.get_by_label("Paycheck")).to_be_attached(timeout=LOAD_TIMEOUT)
    expect(colB.get_by_label("Paycheck")).to_be_attached(timeout=LOAD_TIMEOUT)


def test_c_3_2_different_rules_render_different_totals_per_column(page):
    """c-3-2: On sc-compare, after entering different rules into A and B, the
    page renders different totals per column."""
    open_compare(page)
    colA = column_scope(page, "Scenario A")
    colB = column_scope(page, "Scenario B")
    # Same paycheck, different fixed rules to the same envelope name
    set_paycheck(colA, 100)
    set_paycheck(colB, 100)
    add_fixed_rule(colA, rule_id="r-a", envelope="Z", amount=10.0)
    add_fixed_rule(colB, rule_id="r-b", envelope="Z", amount=20.0)
    amtA = result_amount(colA, "Z")
    amtB = result_amount(colB, "Z")
    assert amtA == "10.00" and amtB == "20.00" and amtA != amtB


def test_c_3_3_undo_shows_previous_value_in_active_editor(page):
    """c-3-3: On sc-compare, after pressing Undo, the active editor shows the
    previous value. We use the Paycheck field in Scenario A.

    Ambiguity A4: per-column Undo applies only to that column.
    """
    open_compare(page)
    colA = column_scope(page, "Scenario A")
    set_paycheck(colA, 100)
    set_paycheck(colA, 250)
    # Click Undo in column A
    undoA = colA.get_by_role("button", name="Undo", exact=True)
    expect(undoA).to_be_enabled(timeout=LOAD_TIMEOUT)
    undoA.click()
    # Paycheck should read the previous value 100
    expect(colA.get_by_label("Paycheck")).to_have_value("100")


def test_c_3_4_redo_restores_value_that_was_undone(page):
    """c-3-4: On sc-compare, after pressing Redo, the active editor shows the
    value that was undone. We use the Paycheck field in Scenario A again."""
    open_compare(page)
    colA = column_scope(page, "Scenario A")
    set_paycheck(colA, 100)
    set_paycheck(colA, 250)
    undoA = colA.get_by_role("button", name="Undo", exact=True)
    redoA = colA.get_by_role("button", name="Redo", exact=True)
    expect(undoA).to_be_enabled(timeout=LOAD_TIMEOUT)
    undoA.click()
    expect(redoA).to_be_enabled(timeout=LOAD_TIMEOUT)
    redoA.click()
    expect(colA.get_by_label("Paycheck")).to_have_value("250")


def test_c_3_5_opening_share_url_restores_both_columns(page):
    """c-3-5: On sc-compare, opening a copied share URL displays an identical
    scenario in both the editor and results.

    Ambiguity A3: The URL encodes both Scenario A and Scenario B.
    """
    open_compare(page)
    colA = column_scope(page, "Scenario A")
    colB = column_scope(page, "Scenario B")
    set_paycheck(colA, 400)
    set_paycheck(colB, 500)
    add_percent_rule(colA, rule_id="ra", envelope="A", percent=10.0)
    add_percent_rule(colB, rule_id="rb", envelope="B", percent=20.0)
    # Read column results
    a_amt = result_amount(colA, "A")
    b_amt = result_amount(colB, "B")
    # Copy share URL and open it
    share = share_url_input(page)
    expect(share).to_be_attached(timeout=LOAD_TIMEOUT)
    href = share.input_value()
    page.goto(href, wait_until="domcontentloaded")
    # Columns should restore both editor and results
    colA2 = column_scope(page, "Scenario A")
    colB2 = column_scope(page, "Scenario B")
    expect(colA2.get_by_label("Paycheck")).to_have_value("400")
    expect(colB2.get_by_label("Paycheck")).to_have_value("500")
    assert result_amount(colA2, "A") == a_amt
    assert result_amount(colB2, "B") == b_amt


def test_c_3_6_editing_updates_url_and_share_link(page):
    """c-3-6: On sc-compare, changing any scenario field updates the browser
    URL and the visible share link to show the current state."""
    open_compare(page)
    colA = column_scope(page, "Scenario A")
    set_paycheck(colA, 123)
    before_url = page.url
    # change something
    set_paycheck(colA, 456)
    # The page URL should change and the Share URL input should reflect it
    after_url = page.url
    assert after_url != before_url
    expect(share_url_input(page)).to_have_value(after_url)
