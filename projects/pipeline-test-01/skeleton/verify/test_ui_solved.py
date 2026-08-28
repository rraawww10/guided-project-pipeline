"""sc-solved at /boards/[id]/solved - the face-up view.

Every selector is one the spec pins: data-testid board-grid, cell and
board-missing, and the data-index, data-count and data-mine attributes. Class
names are hashed by CSS Modules and are never read.

One test per criterion, each asserting only its own criterion.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    INTRO_MINES,
    attr_by_index,
    board_missing,
    cell,
    cells,
    grid,
    open_solved,
    text_by_index,
)


def test_c_1_4_intro_solved_draws_25_cells_with_their_mines_and_counts(page):
    """c-1-4: 25 cell elements, board-grid carrying data-width 5 and data-height
    5, data-mine the string true on 9, 11, 18 and 23 and the string false on the
    other 21, and data-count 0, 1, 2, 3 and 2 on 0, 3, 12, 17 and 24."""
    open_solved(page, "intro")
    expect(cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    expect(grid(page)).to_have_attribute("data-width", "5", timeout=LOAD_TIMEOUT)
    expect(grid(page)).to_have_attribute("data-height", "5", timeout=LOAD_TIMEOUT)

    mine_attr = attr_by_index(page, "data-mine")
    expected_mine = {
        index: ("true" if index in INTRO_MINES else "false") for index in range(25)
    }
    assert mine_attr == expected_mine

    count_attr = attr_by_index(page, "data-count")
    got = {index: count_attr.get(index) for index in (0, 3, 12, 17, 24)}
    assert got == {0: "0", 3: "1", 12: "2", 17: "3", 24: "2"}


def test_c_1_5_corner_solved_shows_a_glyph_a_number_and_three_blank_zeros(page):
    """c-1-5: 16 cell elements, the cell at data-index 10 reads 3, the cell at
    15 reads *, and the cells at 0, 1 and 4 read empty text while carrying
    data-count 0 - so a zero is blank on the page but still counted in the
    attribute."""
    open_solved(page, "corner")
    expect(cells(page)).to_have_count(16, timeout=LOAD_TIMEOUT)

    expect(cell(page, 10)).to_have_text("3", timeout=LOAD_TIMEOUT)
    expect(cell(page, 15)).to_have_text("*", timeout=LOAD_TIMEOUT)

    texts = text_by_index(page)
    assert {index: texts.get(index) for index in (0, 1, 4)} == {0: "", 1: "", 4: ""}

    count_attr = attr_by_index(page, "data-count")
    assert {index: count_attr.get(index) for index in (0, 1, 4)} == {
        0: "0",
        1: "0",
        4: "0",
    }


def test_c_1_6_unknown_board_solved_draws_board_not_found_and_no_cells(page):
    """c-1-6: board-missing with the text exactly Board not found, and 0 cell
    elements.

    board-missing is asserted first on purpose: it is only drawn once
    GET /api/boards/[id] has answered 404, so waiting for it means the 0-cell
    assertion is read after the fetch has resolved rather than before it."""
    open_solved(page, "no-such-board")

    expect(board_missing(page)).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(board_missing(page)).to_have_text("Board not found", timeout=LOAD_TIMEOUT)
    expect(cells(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
