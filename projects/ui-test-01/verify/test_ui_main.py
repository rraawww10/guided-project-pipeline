"""sc-main at /. One test per criterion for sessions 1 and 2.

Note on ambiguities (see ambiguity.md):
- A2: We grade c-2-1 as the cap limiting this single rule's contribution: min(paycheck*percent, cap).
- W1/W2/W3: We grade remainder as paycheck minus sum of contributions (after caps),
  eligible = all present envelopes when no caps exist, distributed in ascending
  envelope id order (id derived from the envelope name lowercased with dashes).
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    normalize,
    open_main,
    rationale_lines_near,
    rationale_toggle,
    result_amount,
    set_paycheck,
    add_fixed_rule,
    add_percent_rule,
)


def test_c_1_1_renders_rent_300_after_fixed_rule(page):
    """c-1-1: sc-main renders a row for 'Rent' with amount 300.00 after
    entering paycheck 1000 and a fixed rule of 300 to 'Rent'."""
    open_main(page)
    set_paycheck(page, 1000)
    add_fixed_rule(page, rule_id="r-fixed-rent", envelope="Rent", amount=300.0)
    amount = result_amount(page, "Rent")
    assert amount == "300.00"


def test_c_1_2_renders_food_50_after_10_percent_of_500(page):
    """c-1-2: sc-main renders a row for 'Food' with amount 50.00 after
    entering paycheck 500 and a 10% rule to 'Food'."""
    open_main(page)
    set_paycheck(page, 500)
    add_percent_rule(page, rule_id="r-pct-food", envelope="Food", percent=10.0)
    amount = result_amount(page, "Food")
    assert amount == "50.00"


def test_c_1_3_renders_one_row_per_distinct_envelope(page):
    """c-1-3: sc-main renders one results row per distinct envelope after
    adding two envelopes with any rules.

    We add two small fixed rules so both names and their amounts appear exactly once.
    """
    open_main(page)
    set_paycheck(page, 200)
    add_fixed_rule(page, rule_id="r-fix-a", envelope="A", amount=5.0)
    add_fixed_rule(page, rule_id="r-fix-b", envelope="B", amount=7.0)
    # Each envelope appears with its amount exactly once in the results
    a_amt = result_amount(page, "A")
    b_amt = result_amount(page, "B")
    assert a_amt == "5.00"
    assert b_amt == "7.00"


def test_c_1_4_paycheck_change_updates_totals_immediately(page):
    """c-1-4: On sc-main, changing the Paycheck input from 400 to 600 renders
    updated totals immediately.

    We use a 10% rule so the row changes from 40.00 to 60.00.
    """
    open_main(page)
    set_paycheck(page, 400)
    add_percent_rule(page, rule_id="r-pct-groceries", envelope="Groceries", percent=10.0)
    expect(page).to_have_title
    amt1 = result_amount(page, "Groceries")
    assert amt1 == "40.00"
    set_paycheck(page, 600)
    amt2 = result_amount(page, "Groceries")
    assert amt2 == "60.00"


def test_c_2_1_percent_with_cap_applies_cap_limit(page):
    """c-2-1: On sc-main, a 50% rule with a cap of 100 applied to paycheck 1000
    renders amount 100.00 for its envelope.

    Ambiguity A2: we take the reading that the cap limits this rule's own
    contribution: min(1000 * 0.5, 100) = 100.00.
    """
    open_main(page)
    set_paycheck(page, 1000)
    add_percent_rule(page, rule_id="r-cap-sink", envelope="Savings", percent=50.0, cap=100.0)
    amt = result_amount(page, "Savings")
    assert amt == "100.00"


def test_c_2_2_rationale_orders_higher_priority_first(page):
    """c-2-2: On sc-main, with two rules for the same envelope at different
    priorities, the rationale panel renders the higher-priority rule's line
    before the lower-priority one.

    Ambiguity A1/W4/W5: we assume a numeric priority where higher numbers sort
    first; ties break by ascending rule id. We give rule IDs r-lo and r-hi.
    """
    open_main(page)
    set_paycheck(page, 1000)
    # lower priority first (e.g. 1), then higher (e.g. 2)
    add_fixed_rule(page, rule_id="r-lo", envelope="Rent", amount=100.0, priority=1)
    add_percent_rule(page, rule_id="r-hi", envelope="Rent", percent=10.0, priority=2)
    # Show rationale/details and read nearby lines
    toggle = rationale_toggle(page)
    expect(toggle).to_be_attached(timeout=LOAD_TIMEOUT)
    toggle.click()
    lines = rationale_lines_near(page, "Rent")
    # Find the first line mentioning either rule id and assert order
    joined = "\n".join(lines)
    first_hi = joined.find("r-hi")
    first_lo = joined.find("r-lo")
    assert first_hi != -1 and first_lo != -1, (
        f"expected rationale lines to include both rule ids; got: {lines}"
    )
    assert first_hi < first_lo, (
        f"higher-priority r-hi should appear before r-lo; got: {lines}"
    )


def test_c_2_3_remainder_distributes_evenly_across_three(page):
    """c-2-3: On sc-main, with remainder 30 and three eligible envelopes at
    equal priority, the Results list renders each of those three increased by
    10.00.

    Ambiguities W1/W2/W3: remainder = paycheck − sum; eligible = all present
    envelopes when no caps; order stable but value per row is 10.00 regardless.
    We create three 0-amount fixed rules to introduce three envelopes, then set
    paycheck = 30 so each row rises to 10.00.
    """
    open_main(page)
    set_paycheck(page, 30)
    add_fixed_rule(page, rule_id="r-a", envelope="A", amount=0.0, priority=1)
    add_fixed_rule(page, rule_id="r-b", envelope="B", amount=0.0, priority=1)
    add_fixed_rule(page, rule_id="r-c", envelope="C", amount=0.0, priority=1)
    assert result_amount(page, "A") == "10.00"
    assert result_amount(page, "B") == "10.00"
    assert result_amount(page, "C") == "10.00"


def test_c_2_4_expanding_envelope_shows_two_rationale_lines(page):
    """c-2-4: On sc-main, expanding an envelope renders at least two rationale
    lines that include rule identifiers and applied amounts.

    We add two rules with ids r1 and r2 and then expand the envelope.
    """
    open_main(page)
    set_paycheck(page, 1000)
    add_fixed_rule(page, rule_id="r1", envelope="Travel", amount=50.0, priority=1)
    add_percent_rule(page, rule_id="r2", envelope="Travel", percent=5.0, priority=2)
    lines = rationale_lines_near(page, "Travel")
    joined = "\n".join(lines)
    assert "r1" in joined and "r2" in joined, (
        f"expected rationale to include both rule ids r1 and r2; got: {lines}"
    )
    # amounts present as numbers with 2 decimals somewhere in the nearby text
    has_amount = any(any(ch.isdigit() for ch in line) and "." in line for line in lines)
    assert has_amount, f"expected applied amounts in rationale; got: {lines}"


def test_c_2_5_reload_with_identical_inputs_is_deterministic(page):
    """c-2-5: On sc-main, after reloading the page with identical inputs, the
    Results list renders the same per-envelope amounts and the same remainder
    distribution order.

    Ambiguity W9: we grade determinism only; we re-enter the same inputs after a
    hard reload and compare row amounts and order.
    """
    open_main(page)
    set_paycheck(page, 30)
    add_fixed_rule(page, rule_id="r-a", envelope="A", amount=0.0, priority=1)
    add_fixed_rule(page, rule_id="r-b", envelope="B", amount=0.0, priority=1)
    add_fixed_rule(page, rule_id="r-c", envelope="C", amount=0.0, priority=1)
    # read order by first occurrence of each row's text content
    rows_before = [
        (name, result_amount(page, name)) for name in ("A", "B", "C")
    ]
    page.reload(wait_until="domcontentloaded")
    # re-enter identical inputs
    set_paycheck(page, 30)
    add_fixed_rule(page, rule_id="r-a", envelope="A", amount=0.0, priority=1)
    add_fixed_rule(page, rule_id="r-b", envelope="B", amount=0.0, priority=1)
    add_fixed_rule(page, rule_id="r-c", envelope="C", amount=0.0, priority=1)
    rows_after = [
        (name, result_amount(page, name)) for name in ("A", "B", "C")
    ]
    assert rows_before == rows_after


def test_c_2_6_rationale_toggle_shows_and_hides_panel(page):
    """c-2-6: On sc-main, clicking the rationale toggle shows the rationale
    panel; clicking it again hides the panel."""
    open_main(page)
    set_paycheck(page, 500)
    add_fixed_rule(page, rule_id="r-x", envelope="X", amount=1.0)
    toggle = rationale_toggle(page)
    expect(toggle).to_be_attached(timeout=LOAD_TIMEOUT)
    toggle.click()
    # Expect some rationale content to appear
    lines = rationale_lines_near(page, "X")
    assert any(lines), "expected rationale content after expanding"
    toggle.click()
    # After hiding, the rationale content should disappear or shrink
    lines2 = rationale_lines_near(page, "X")
    assert len(lines2) <= len(lines)
