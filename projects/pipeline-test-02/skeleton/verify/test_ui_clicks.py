"""sc-puzzle at /puzzles/[id], driven by clicks.

One test per criterion, asserting only it. Every element is found through the
data-testid the spec pins and every wait is a retrying Playwright wait, never a
sleep.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    BLANKS_FILLED,
    CHECK_TIMEOUT,
    LOAD_TIMEOUT,
    all_cells,
    all_col_clues,
    all_row_clues,
    cell,
    col_clue,
    is_check_response,
    open_puzzle,
    row_clue,
    solved_banner,
)


def test_c_2_5_clicking_one_cell_cycles_empty_filled_crossed_empty(page):
    """c-2-5: on /puzzles/boat a first click on cell-0-2 updates its data-state
    to filled, a second click updates it to crossed and a third click updates it
    to empty, while cell-0-0 stays at data-state empty across all three clicks.

    filled and crossed are what go red against the cut-cell-cycle fallback,
    where `updated` starts as `grid` and a click changes nothing.
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
            f"cell-0-0 reads {neighbour.get_attribute('data-state')!r} while "
            f"cell-0-2 was cycled to {step}"
        )


def test_c_2_6_clicking_the_blanks_solution_satisfies_every_clue_and_solves(page):
    """c-2-6: on /puzzles/blanks, one click on each of the 13 cells filled in
    the blanks solution - the 5 cells of row 1, columns 0 and 4 of row 2,
    columns 1, 2 and 3 of row 3, and columns 0, 2 and 4 of row 4, leaving row 0
    untouched - renders exactly 5 row-clue elements, row-clue-0 through
    row-clue-4, and exactly 5 col-clue elements, col-clue-0 through col-clue-4,
    each of those 10 elements carrying data-status satisfied, and renders a
    solved-banner element with text Solved.

    Two readings this handles rather than picks:

    * ambiguity.md W1 leaves the in-flight window - what a strip shows between a
      click and its response - open. Nothing here observes that window: each
      click waits for its own check response before the next click is sent, so
      the board is never mid-flight when it is read, and the final assertions
      are retrying waits on the settled state either way.
    * reading a strip as "whatever col-clue elements happen to be there" passes
      vacuously when colClues is [], which is exactly what an open cut-transpose
      serves. The criterion says exactly 5 and names col-clue-0 through
      col-clue-4, so the count is asserted first and each element is then looked
      up by its own testid - absence fails instead of being skipped.
    """
    open_puzzle(page, "blanks")
    expect(all_cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    for r, c in BLANKS_FILLED:
        with page.expect_response(
            lambda response: is_check_response(response, "blanks"),
            timeout=CHECK_TIMEOUT,
        ):
            cell(page, r, c).click()

    expect(all_row_clues(page)).to_have_count(5, timeout=CHECK_TIMEOUT)
    expect(all_col_clues(page)).to_have_count(5, timeout=CHECK_TIMEOUT)

    for i in range(5):
        expect(row_clue(page, i)).to_have_attribute(
            "data-status", "satisfied", timeout=CHECK_TIMEOUT
        )
        expect(col_clue(page, i)).to_have_attribute(
            "data-status", "satisfied", timeout=CHECK_TIMEOUT
        )

    banner = solved_banner(page)
    expect(banner).to_have_count(1, timeout=CHECK_TIMEOUT)
    expect(banner).to_have_text("Solved", timeout=CHECK_TIMEOUT)
