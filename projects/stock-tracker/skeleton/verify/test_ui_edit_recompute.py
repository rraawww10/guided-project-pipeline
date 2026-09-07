import os
import re
import httpx
from playwright.sync_api import sync_playwright


def _base_url() -> str:
    url = os.environ.get("BASE_URL")
    assert url, "BASE_URL is not set"
    return url.rstrip("/")


def _row_numbers(text: str) -> list[int]:
    """Every integer in a plan row, in order.

    The row renders symbol, shares, side, price and cost, and only
    plan-row-<SYMBOL> is a spec'd testid - there is no shares cell to target.
    Reading the FIRST integer picked up whatever column happened to come
    first, which is how this test compared -1 against -1 and called the plan
    unchanged. Comparing the whole set is what c-4-4 already does.
    """
    return [int(m) for m in re.findall(r"-?\d+", text)]


essentially_zero = 1e-9


def test_c_4_3_edit_target_and_save_updates_shares_for_that_symbol():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        # Pick a symbol that already appears in the plan table
        page.wait_for_selector('[data-testid^="plan-row-"]', timeout=5000)
        plan_row = page.locator('[data-testid^="plan-row-"]').first
        testid = plan_row.get_attribute("data-testid")
        assert testid and testid.startswith("plan-row-"), "missing plan row testid"
        symbol = testid.split("plan-row-")[-1]
        before_text = plan_row.inner_text()
        before_numbers = _row_numbers(before_text)
        assert before_numbers, f"no numbers in plan row: {before_text!r}"
        # Inputs must be pre-filled from the current targets so the user can edit them.
        input_sel = f'[data-testid="target-input-{symbol}"]'
        page.wait_for_selector(input_sel, timeout=5000)
        # Wait until the input is populated (cut-ui-target-inputs initialises it).
        page.wait_for_function(
            "sel => document.querySelector(sel)?.value !== ''",
            arg=input_sel,
            timeout=5000,
        )
        inp = page.locator(input_sel)
        # Also sanity-check against the API's targetWeight for this symbol.
        with httpx.Client(base_url=base, timeout=10.0) as client:
            alloc = client.get("/api/allocation").json()
        api_tw = next((float(it.get("targetWeight", 0)) for it in alloc if it.get("symbol") == symbol), None)
        assert api_tw is not None, f"no allocation row for {symbol}"
        current_val = inp.input_value()
        try:
            current = float(current_val)
        except ValueError:
            current = 0.0
        # The UI value should reflect the API value (within float wiggle).
        assert abs(current - api_tw) <= 1e-6, (
            f"input for {symbol} not initialised from targets: ui={current_val!r}, api={api_tw}")
        # Move the target in whichever direction makes this symbol MORE
        # drifted, so it cannot fall out of the plan table and take the row
        # this test re-reads with it. Lowering an overweight symbol's target
        # widens the gap; raising an underweight one's does the same.
        badge = page.locator(f'[data-testid="drift-{symbol}"]')
        page.wait_for_selector(f'[data-testid="drift-{symbol}"]', timeout=5000)
        overweight = badge.inner_text().strip().upper() == "OVER"
        delta = -0.08 if overweight else 0.08
        new_val = str(round(min(0.98, max(0.02, current + delta)), 4))
        assert float(new_val) != current, (
            f"target weight for {symbol} could not be moved from {current}")
        inp.fill(new_val)
        # Click save and wait for applied notice
        page.locator('[data-testid="save-settings"]').click()
        page.wait_for_selector('[data-testid="applied"]', timeout=5000)
        # Re-read the plan row and confirm the recomputed shares moved
        page.wait_for_selector(f'[data-testid="plan-row-{symbol}"]', timeout=5000)
        after_text = page.locator(f'[data-testid="plan-row-{symbol}"]').inner_text()
        after_numbers = _row_numbers(after_text)
        assert after_numbers != before_numbers, (
            f"plan row for {symbol} did not change after saving target "
            f"{current} -> {new_val}: {before_text!r} vs {after_text!r}")
        browser.close()


def test_c_4_4_save_without_changes_shows_saved_notice_and_plan_unchanged():
    base = _base_url()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        # Snapshot current plan rows content
        page.wait_for_selector('[data-testid^="plan-row-"]', timeout=5000)
        rows = page.locator('[data-testid^="plan-row-"]').all()
        before = [r.inner_text() for r in rows]
        # Click save without edits
        page.locator('[data-testid="save-settings"]').click()
        page.wait_for_selector('[data-testid="applied"]', timeout=5000)
        # Rows should be the same as before
        rows_after = page.locator('[data-testid^="plan-row-"]').all()
        after = [r.inner_text() for r in rows_after]
        assert before == after
        browser.close()
