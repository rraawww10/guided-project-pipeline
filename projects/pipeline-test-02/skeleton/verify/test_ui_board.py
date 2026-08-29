"""sc-puzzle at /puzzles/[id], as it is drawn before anything is clicked.

One test per criterion, asserting only it. Every element is found through the
data-testid the spec pins - CSS Modules hash the class names, so nothing here
reads a class or any styling - and every wait is a retrying Playwright wait.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    COL_CLUES,
    LOAD_TIMEOUT,
    ROW_CLUES,
    all_cells,
    all_col_clues,
    all_row_clues,
    attr_map,
    cell,
    clue_text,
    col_clue,
    open_puzzle,
    puzzle_missing,
    puzzle_title,
    row_clue,
    solved_banner,
    text_of,
)


def test_c_1_4_blanks_board_draws_25_empty_cells_and_two_open_clue_strips(page):
    """c-1-4: /puzzles/blanks renders 25 elements with data-testid cell-0-0
    through cell-4-4 each carrying data-state empty, renders exactly 5 row-clue
    elements and exactly 5 col-clue elements, renders row-clue-0 with text 0,
    row-clue-1 with text 5 and col-clue-2 with text 1 2, gives each of
    row-clue-0 through row-clue-4 data-status open, and renders no solved-banner
    element.

    The two counts are what make an absent strip fail rather than pass
    vacuously: with cut-transpose open colClues serves as [], so the board draws
    no col-clue element at all and "exactly 5" goes red.
    """
    open_puzzle(page, "blanks")
    expect(all_cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    expected_cells = {
        f"cell-{r}-{c}": "empty" for r in range(5) for c in range(5)
    }
    assert attr_map(all_cells(page), "data-state") == expected_cells

    expect(all_row_clues(page)).to_have_count(5, timeout=LOAD_TIMEOUT)
    expect(all_col_clues(page)).to_have_count(5, timeout=LOAD_TIMEOUT)

    assert text_of(row_clue(page, 0)) == clue_text(ROW_CLUES["blanks"][0]), (
        f"row-clue-0 reads {text_of(row_clue(page, 0))!r}, expected '0'"
    )
    assert text_of(row_clue(page, 1)) == clue_text(ROW_CLUES["blanks"][1]), (
        f"row-clue-1 reads {text_of(row_clue(page, 1))!r}, expected '5'"
    )
    assert text_of(col_clue(page, 2)) == clue_text(COL_CLUES["blanks"][2]), (
        f"col-clue-2 reads {text_of(col_clue(page, 2))!r}, expected '1 2'"
    )

    expected_status = {f"row-clue-{r}": "open" for r in range(5)}
    assert attr_map(all_row_clues(page), "data-status") == expected_status

    expect(solved_banner(page)).to_have_count(0)


def test_c_1_5_unknown_puzzle_id_shows_puzzle_not_found_and_no_board(page):
    """c-1-5: /puzzles/nope renders an element with data-testid puzzle-missing
    and text Puzzle not found, and renders no element with data-testid cell-0-0
    and no element with data-testid puzzle-title.

    The not-found message is waited for first, so the two absences are read off
    a screen that has finished loading rather than off one that has not started.
    """
    open_puzzle(page, "nope")

    missing = puzzle_missing(page)
    expect(missing).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(missing).to_have_text("Puzzle not found", timeout=LOAD_TIMEOUT)

    expect(cell(page, 0, 0)).to_have_count(0)
    expect(puzzle_title(page)).to_have_count(0)
