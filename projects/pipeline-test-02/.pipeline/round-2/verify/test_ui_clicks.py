"""sc-puzzle at /puzzles/[id], driven by clicks.

One test per criterion, asserting only it. Every element is read through the
data-testid the spec pins, and every wait is a retrying Playwright wait.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    BLANKS_FILLED,
    CHECK_TIMEOUT,
    LOAD_TIMEOUT,
    all_cells,
    all_col_clues,
    cell,
    col_clue,
    is_check_response,
    open_puzzle,
    row_clue,
    text_of,
)


def test_c_2_5_clicking_one_cell_cycles_empty_filled_crossed_empty(page):
    """c-2-5: on /puzzles/boat a first click on cell-0-2 updates its data-state
    to filled, a second click updates it to crossed and a third click updates it
    to empty, while cell-0-0 stays at data-state empty across all three clicks.

    filled and crossed are what goes red against the cut-cell-cycle fallback,
    where updated starts as grid and a click changes nothing.
    """
    open_puzzle(page, "boat")
    expect(all_cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    target = cell(page, 0, 2)
    neighbour = cell(page, 0, 0)
    expect(target).to_have_attribute("data-state", "empty", timeout=LOAD_TIMEOUT)

    for step in ("filled", "crossed", "empty"):
        target.click()
        expect(target).to_have_attribute("data-state", step, timeout=LOAD_TIMEOUT)
        assert neighbour.get_attribute("data-state") == "empty", (
            f"cell-0-0 moved to {neighbour.get_attribute('data-state')!r} "
            f"while cell-0-2 was cycled to {step}"
        )


def test_c_2_6_clicking_the_blanks_solution_solves_the_board(page):
    """c-2-6: on /puzzles/blanks, one click on each of the 13 cells filled in
    the blanks solution renders a solved-banner element with text Solved and
    gives each of row-clue-0 through row-clue-4 and col-clue-0 through
    col-clue-4 data-status satisfied.

    Two readings the spec settles, and one it does not:

    * the screen now pins the ordering - "the value shown is the one from the
      response to the most recent click, and a response arriving after a later
      click has already been sent is discarded". This test waits for each
      click's POST to be answered before sending the next, so it never has two
      in flight and grades the board rather than the discard policy.
    * ambiguity.md W5: reading the col-clue strip as "whatever col-clue elements
      happen to be there" passes vacuously when colClues is [], which is exactly
      the state an open cut-transpose produces. The spec's own wording is
      "col-clue-0 through col-clue-4", so this test asserts the strip holds
      exactly 5 elements and looks each one up by its testid - absence fails.
    """
    open_puzzle(page, "blanks")
    expect(all_cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    for r, c in BLANKS_FILLED:
        with page.expect_response(
            lambda response: is_check_response(response, "blanks"),
            timeout=CHECK_TIMEOUT,
        ):
            cell(page, r, c).click()

    banner = page.get_by_test_id("solved-banner")
    expect(banner).to_have_count(1, timeout=CHECK_TIMEOUT)
    assert text_of(banner) == "Solved", f"solved-banner reads {text_of(banner)!r}"

    expect(all_col_clues(page)).to_have_count(5, timeout=LOAD_TIMEOUT)
    for i in range(5):
        expect(row_clue(page, i)).to_have_attribute(
            "data-status", "satisfied", timeout=CHECK_TIMEOUT
        )
        expect(col_clue(page, i)).to_have_attribute(
            "data-status", "satisfied", timeout=CHECK_TIMEOUT
        )
