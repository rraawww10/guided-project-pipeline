"""sc-play at /boards/[id] - the playable board.

Every hook is a data-testid or a data-* attribute the spec pins. One test per
criterion.

Reading taken on the not-found state (ambiguity.md W3): the spec pins only
"data-testid board-missing with the text Board not found, drawn in place of the
grid ... with 0 cells on the page", and `c-2-4` asserts exactly that. Whether
`flag-mode`, `mines-left` and `game-status` also render on a missing board is
undecided by the spec, so no test here asserts their presence or their absence.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    CORNER_CELLS,
    FIELD_CELLS,
    INTRO_CELLS,
    LOAD_TIMEOUT,
    board_missing,
    cell,
    cell_attr_map,
    cell_text_map,
    cells,
    cells_with,
    flag_mode,
    game_status,
    mines_left,
    open_play,
)


def test_c_2_4_field_draws_sixty_four_blank_face_down_cells_and_a_missing_board(page):
    """c-2-4: screen /boards/field renders 64 elements with data-testid cell, all
    64 carrying data-revealed false and data-flagged false and displaying empty
    text, and screen /boards/no-such-board displays an element with data-testid
    board-missing whose text is exactly Board not found and renders 0 elements
    with data-testid cell.
    """
    open_play(page, "field")
    expect(cells(page)).to_have_count(FIELD_CELLS, timeout=LOAD_TIMEOUT)

    all_false = {str(i): "false" for i in range(FIELD_CELLS)}
    revealed = cell_attr_map(page, "data-revealed")
    assert revealed == all_false, f"data-revealed read {revealed!r}"
    flagged = cell_attr_map(page, "data-flagged")
    assert flagged == all_false, f"data-flagged read {flagged!r}"

    text = cell_text_map(page)
    non_blank = {k: v for k, v in text.items() if v != ""}
    assert text == {str(i): "" for i in range(FIELD_CELLS)}, (
        f"cells were not all blank: {non_blank!r}")

    open_play(page, "no-such-board")
    expect(board_missing(page)).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(board_missing(page)).to_have_text("Board not found", timeout=LOAD_TIMEOUT)
    expect(cells(page)).to_have_count(0, timeout=LOAD_TIMEOUT)


def test_c_2_5_one_click_on_field_index_zero_opens_fourteen_cells_and_stops(page):
    """c-2-5: clicking the cell with data-index 0 on screen /boards/field updates
    data-revealed to true on exactly 14 cells, leaves the cell with data-index 7
    at data-revealed false, and displays the text 1 in the cell with data-index 6
    and empty text in the cell with data-index 0.

    Index 7 touches only numbered cells and a mine, never a zero, so the correct
    fill leaves it shut while a fill that walks through numbers opens it - and
    opens 54 cells instead of 14.
    """
    open_play(page, "field")
    expect(cells(page)).to_have_count(FIELD_CELLS, timeout=LOAD_TIMEOUT)

    cell(page, 0).click()

    expect(cells_with(page, "data-revealed", "true")).to_have_count(
        14, timeout=LOAD_TIMEOUT)
    expect(cell(page, 7)).to_have_attribute(
        "data-revealed", "false", timeout=LOAD_TIMEOUT)
    expect(cell(page, 6)).to_have_text("1", timeout=LOAD_TIMEOUT)
    expect(cell(page, 0)).to_have_text("", timeout=LOAD_TIMEOUT)


def test_c_2_6_a_second_click_on_an_open_cell_opens_nothing_new(page):
    """c-2-6: clicking the cell with data-index 3 on screen /boards/intro updates
    data-revealed to true on exactly 1 cell, a following click on the cell with
    data-index 20 updates data-revealed to true on exactly 7 cells, and a second
    click on the cell with data-index 3 leaves data-revealed true on exactly 7
    cells.

    The 1 -> 7 -> 7 walk is what separates a union from an append.
    """
    open_play(page, "intro")
    expect(cells(page)).to_have_count(INTRO_CELLS, timeout=LOAD_TIMEOUT)
    opened = cells_with(page, "data-revealed", "true")

    cell(page, 3).click()
    expect(opened).to_have_count(1, timeout=LOAD_TIMEOUT)

    cell(page, 20).click()
    expect(opened).to_have_count(7, timeout=LOAD_TIMEOUT)

    cell(page, 3).click()
    expect(opened).to_have_count(7, timeout=LOAD_TIMEOUT)
    expect(cell(page, 3)).to_have_attribute(
        "data-revealed", "true", timeout=LOAD_TIMEOUT)


def test_c_3_5_flag_mode_plants_and_lifts_flags_and_walks_the_counter(page):
    """c-3-5: on screen /boards/corner, clicking the element with data-testid
    flag-mode and then the cell with data-index 15 updates that cell to
    data-flagged true and data-revealed false and updates the data-testid
    mines-left element to the text Mines left: 2, a following click on the cell
    with data-index 14 updates mines-left to the text Mines left: 1, and a second
    click on the cell with data-index 15 updates that cell to data-flagged false
    and mines-left to the text Mines left: 2.

    Plant, plant, lift on a 3-mine board: a handler that only adds and a handler
    that only removes are both red, and so is a constant counter.
    """
    open_play(page, "corner")
    expect(cells(page)).to_have_count(CORNER_CELLS, timeout=LOAD_TIMEOUT)

    flag_mode(page).click()

    cell(page, 15).click()
    expect(cell(page, 15)).to_have_attribute(
        "data-flagged", "true", timeout=LOAD_TIMEOUT)
    expect(cell(page, 15)).to_have_attribute(
        "data-revealed", "false", timeout=LOAD_TIMEOUT)
    expect(mines_left(page)).to_have_text("Mines left: 2", timeout=LOAD_TIMEOUT)

    cell(page, 14).click()
    expect(mines_left(page)).to_have_text("Mines left: 1", timeout=LOAD_TIMEOUT)

    cell(page, 15).click()
    expect(cell(page, 15)).to_have_attribute(
        "data-flagged", "false", timeout=LOAD_TIMEOUT)
    expect(mines_left(page)).to_have_text("Mines left: 2", timeout=LOAD_TIMEOUT)


def test_c_3_6_the_status_line_reads_won_on_corner_and_lost_on_intro(page):
    """c-3-6: clicking the cell with data-index 0 on screen /boards/corner updates
    data-revealed to true on exactly 13 cells and updates the data-testid
    game-status element to the text Won, and clicking the cell with data-index 9
    on screen /boards/intro updates data-revealed to true on exactly 1 cell and
    updates the data-testid game-status element to the text Lost.
    """
    open_play(page, "corner")
    expect(cells(page)).to_have_count(CORNER_CELLS, timeout=LOAD_TIMEOUT)

    cell(page, 0).click()
    expect(cells_with(page, "data-revealed", "true")).to_have_count(
        13, timeout=LOAD_TIMEOUT)
    expect(game_status(page)).to_have_text("Won", timeout=LOAD_TIMEOUT)

    open_play(page, "intro")
    expect(cells(page)).to_have_count(INTRO_CELLS, timeout=LOAD_TIMEOUT)

    cell(page, 9).click()
    expect(cells_with(page, "data-revealed", "true")).to_have_count(
        1, timeout=LOAD_TIMEOUT)
    expect(game_status(page)).to_have_text("Lost", timeout=LOAD_TIMEOUT)
