"""sc-puzzle at /puzzles/[id], as it is drawn before anything is clicked.

One test per criterion, asserting only it. Every element is read through the
data-testid the spec pins. CSS Modules hash the class names, so nothing here
matches on a class or on styling.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    COL_CLUES,
    LOAD_TIMEOUT,
    ROW_CLUES,
    all_cells,
    cell,
    clue_text,
    col_clue,
    open_puzzle,
    row_clue,
    text_of,
)


def test_c_1_4_blanks_board_draws_25_empty_cells_and_open_clue_strips(page):
    """c-1-4: /puzzles/blanks renders 25 elements with data-testid cell-0-0
    through cell-4-4 each carrying data-state empty, renders row-clue-0 with
    text 0, row-clue-1 with text 5 and col-clue-2 with text 1 2, gives each of
    row-clue-0 through row-clue-4 data-status open, and renders no solved-banner
    element.

    The clue strings are what goes red while cut-runs-of is open (every clue
    derives to the empty list, so a strip reads nothing) and while cut-transpose
    is open (colClues is [] and col-clue-2 is not rendered at all).
    """
    open_puzzle(page, "blanks")
    expect(all_cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    expected_ids = {f"cell-{r}-{c}" for r in range(5) for c in range(5)}
    rendered_ids = {
        node.get_attribute("data-testid") for node in all_cells(page).all()
    }
    assert rendered_ids == expected_ids, (
        f"missing {sorted(expected_ids - rendered_ids)}, "
        f"unexpected {sorted(rendered_ids - expected_ids)}"
    )

    states = {
        f"cell-{r}-{c}": cell(page, r, c).get_attribute("data-state")
        for r in range(5)
        for c in range(5)
    }
    assert states == {testid: "empty" for testid in expected_ids}, states

    # the three clue strings the criterion pins: [0] reads 0, [5] reads 5, and
    # column 2 of blanks is [1,2], which reads its numbers joined by one space
    expect(col_clue(page, 2)).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(row_clue(page, 0)) == clue_text(ROW_CLUES["blanks"][0]) == "0"
    assert text_of(row_clue(page, 1)) == clue_text(ROW_CLUES["blanks"][1]) == "5"
    assert text_of(col_clue(page, 2)) == clue_text(COL_CLUES["blanks"][2]) == "1 2"

    # no check runs on mount, so every row strip reads open - including row 0,
    # whose [0] clue an empty board already satisfies
    row_statuses = {
        f"row-clue-{r}": row_clue(page, r).get_attribute("data-status")
        for r in range(5)
    }
    assert row_statuses == {f"row-clue-{r}": "open" for r in range(5)}, row_statuses

    expect(page.get_by_test_id("solved-banner")).to_have_count(0)


def test_c_1_5_unknown_puzzle_id_shows_puzzle_not_found_and_no_board(page):
    """c-1-5: /puzzles/nope renders an element with data-testid puzzle-missing
    and text Puzzle not found, and renders no element with data-testid cell-0-0
    and no element with data-testid puzzle-title.
    """
    open_puzzle(page, "nope")

    missing = page.get_by_test_id("puzzle-missing")
    expect(missing).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(missing) == "Puzzle not found", (
        f"puzzle-missing reads {text_of(missing)!r}"
    )

    expect(page.get_by_test_id("cell-0-0")).to_have_count(0)
    expect(page.get_by_test_id("puzzle-title")).to_have_count(0)
