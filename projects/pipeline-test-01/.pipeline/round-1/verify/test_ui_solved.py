"""sc-solved at /boards/[id]/solved - the face-up view.

Every hook is a data-testid or a data-* attribute the spec pins; class names are
hashed by CSS Modules and nothing here reads one. One test per criterion.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    CORNER_CELLS,
    INTRO_CELLS,
    INTRO_MINES,
    LOAD_TIMEOUT,
    board_missing,
    cell,
    cell_attr_map,
    cell_text_map,
    cells,
    open_solved,
)


def test_c_1_4_intro_solved_marks_its_four_mines_and_carries_the_counts(page):
    """c-1-4: screen /boards/intro/solved renders 25 elements with data-testid
    cell, the cells with data-index 9, 11, 18 and 23 carry data-mine true while
    the other 21 carry data-mine false, and the cells with data-index 0, 3, 12,
    17 and 24 carry data-count 0, 1, 2, 3 and 2.
    """
    open_solved(page, "intro")
    expect(cells(page)).to_have_count(INTRO_CELLS, timeout=LOAD_TIMEOUT)

    mine_attr = cell_attr_map(page, "data-mine")
    expected_mine = {
        str(i): ("true" if i in INTRO_MINES else "false") for i in range(INTRO_CELLS)
    }
    assert mine_attr == expected_mine, f"data-mine read {mine_attr!r}"

    count_attr = cell_attr_map(page, "data-count")
    expected_count = {"0": "0", "3": "1", "12": "2", "17": "3", "24": "2"}
    actual_count = {i: count_attr.get(i) for i in expected_count}
    assert actual_count == expected_count, (
        f"data-count at those indices read {actual_count!r}")


def test_c_1_5_corner_solved_shows_a_three_a_mine_glyph_and_three_blanks(page):
    """c-1-5: screen /boards/corner/solved renders 16 elements with data-testid
    cell, the cell with data-index 10 displays the text 3, the cell with
    data-index 15 displays the text *, and the cells with data-index 0, 1 and 4
    display empty text and carry data-count 0.
    """
    open_solved(page, "corner")
    expect(cells(page)).to_have_count(CORNER_CELLS, timeout=LOAD_TIMEOUT)

    expect(cell(page, 10)).to_have_text("3", timeout=LOAD_TIMEOUT)
    expect(cell(page, 15)).to_have_text("*", timeout=LOAD_TIMEOUT)

    text = cell_text_map(page)
    blanks = {i: text.get(str(i)) for i in (0, 1, 4)}
    assert blanks == {0: "", 1: "", 4: ""}, f"those cells read {blanks!r}"

    count_attr = cell_attr_map(page, "data-count")
    zero_counts = {i: count_attr.get(str(i)) for i in (0, 1, 4)}
    assert zero_counts == {0: "0", 1: "0", 4: "0"}, (
        f"data-count on those cells read {zero_counts!r}")


def test_c_1_6_solved_says_board_not_found_and_draws_no_cells(page):
    """c-1-6: screen /boards/no-such-board/solved displays an element with
    data-testid board-missing whose text is exactly Board not found and renders 0
    elements with data-testid cell.
    """
    open_solved(page, "no-such-board")

    expect(board_missing(page)).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(board_missing(page)).to_have_text("Board not found", timeout=LOAD_TIMEOUT)
    expect(cells(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
