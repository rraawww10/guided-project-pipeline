"""sc-play at /boards/[id] - the playable board.

Every selector is one the spec pins: data-testid board-grid, cell, flag-mode,
mines-left, game-status and board-missing, and the data-index, data-revealed and
data-flagged attributes. Class names are hashed by CSS Modules and are never
read.

Two readings taken from ambiguity.md, both stated where they bite:

* A2 - "updates data-revealed to true on exactly N cells" is read as the total
  number of cells on the page carrying data-revealed="true" after the step, not
  as the number that changed in that step. That is the reading the board data
  supports: on intro, a click on 3 opens {3} and a following click on 20 opens
  {15,16,17,20,21,22}, which is 7 in total and 6 changed, and the spec asks for
  7. The delta reading is red against a correct build.
* A1 - c-2-4 counts 64 cells on a board whose counts array may be empty, so the
  grid must be one cell per index of the range 0 .. width * height - 1. The test
  asserts the count the criterion states; the finding is for Gate 1.

One test per criterion, each asserting only its own criterion.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    attr_by_index,
    board_missing,
    cell,
    cells,
    flag_mode,
    game_status,
    grid,
    mines_left,
    open_play,
    revealed_cells,
    text_by_index,
)


def test_c_2_4_field_opens_face_down_and_an_unknown_board_draws_nothing(page):
    """c-2-4: /boards/field draws 64 cells, all data-revealed false, all
    data-flagged false and all blank, board-grid carries data-width 8 and
    data-height 8 and flag-mode reads Flag mode: off; /boards/no-such-board
    draws board-missing reading exactly Board not found and 0 cells, 0
    board-grid, 0 flag-mode, 0 mines-left and 0 game-status."""
    open_play(page, "field")
    expect(cells(page)).to_have_count(64, timeout=LOAD_TIMEOUT)

    expect(grid(page)).to_have_attribute("data-width", "8", timeout=LOAD_TIMEOUT)
    expect(grid(page)).to_have_attribute("data-height", "8", timeout=LOAD_TIMEOUT)
    expect(flag_mode(page)).to_have_text("Flag mode: off", timeout=LOAD_TIMEOUT)

    assert attr_by_index(page, "data-revealed") == {i: "false" for i in range(64)}
    assert attr_by_index(page, "data-flagged") == {i: "false" for i in range(64)}
    assert text_by_index(page) == {i: "" for i in range(64)}

    # board-missing is waited for first: it is only drawn once the fetch has
    # answered 404, so the five 0-counts below are read after the response
    # rather than before it, when they would be 0 whatever the app does.
    open_play(page, "no-such-board")
    expect(board_missing(page)).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(board_missing(page)).to_have_text("Board not found", timeout=LOAD_TIMEOUT)
    expect(cells(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(grid(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(flag_mode(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(mines_left(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(game_status(page)).to_have_count(0, timeout=LOAD_TIMEOUT)


def test_c_2_5_one_click_on_field_index_zero_opens_fourteen_cells_on_screen(page):
    """c-2-5: clicking the cell at data-index 0 on /boards/field leaves exactly
    14 cells at data-revealed true, leaves the cell at 7 at data-revealed false,
    and shows 1 in the cell at 6 and empty text in the cell at 0. Index 7
    touches only numbers and a mine, never a zero, so it stays shut - a fill
    that walks through numbers opens 54 cells here."""
    open_play(page, "field")
    expect(cells(page)).to_have_count(64, timeout=LOAD_TIMEOUT)

    cell(page, 0).click()

    expect(revealed_cells(page)).to_have_count(14, timeout=LOAD_TIMEOUT)
    expect(cell(page, 7)).to_have_attribute(
        "data-revealed", "false", timeout=LOAD_TIMEOUT
    )
    expect(cell(page, 6)).to_have_text("1", timeout=LOAD_TIMEOUT)
    expect(cell(page, 0)).to_have_text("", timeout=LOAD_TIMEOUT)


def test_c_2_6_a_second_click_on_an_open_cell_changes_nothing_on_intro(page):
    """c-2-6: on /boards/intro a click on the cell at data-index 3 leaves
    exactly 1 cell at data-revealed true, a following click on 20 leaves exactly
    7, and a second click on 3 still leaves exactly 7 - which is what separates
    a union from an append.

    Totals, not deltas: see A2 at the top of this file."""
    open_play(page, "intro")
    expect(cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    cell(page, 3).click()
    expect(revealed_cells(page)).to_have_count(1, timeout=LOAD_TIMEOUT)

    cell(page, 20).click()
    expect(revealed_cells(page)).to_have_count(7, timeout=LOAD_TIMEOUT)

    cell(page, 3).click()
    expect(revealed_cells(page)).to_have_count(7, timeout=LOAD_TIMEOUT)
    # the same 7 indices, so a re-click that dropped or moved the open set is
    # red here even though the count would survive it
    revealed = sorted(
        index
        for index, value in attr_by_index(page, "data-revealed").items()
        if value == "true"
    )
    assert revealed == [3, 15, 16, 17, 20, 21, 22]


def test_c_3_5_flag_mode_plants_removes_and_guards_while_mines_left_tracks(page):
    """c-3-5: the whole flag sequence on /boards/corner - toggle on, flag 15
    (Mines left: 2), flag 14 (1), unflag 15 (2), flag 15, 11 and 0 (-1), toggle
    off, a reveal click on the flagged cell 0 that opens nothing and moves
    nothing, a reveal click on 6 that opens exactly 1 cell, then toggle on and a
    flag click on the open cell 6 that leaves it unflagged and the counter
    unmoved.

    corner has 3 mines, so a counter clamped at 0 is red at the fourth flag, and
    a fallback that starts at -1 is red at the first assertion of Mines left: 2.
    """
    open_play(page, "corner")
    expect(cells(page)).to_have_count(16, timeout=LOAD_TIMEOUT)

    flag_mode(page).click()
    expect(flag_mode(page)).to_have_text("Flag mode: on", timeout=LOAD_TIMEOUT)

    cell(page, 15).click()
    expect(cell(page, 15)).to_have_attribute(
        "data-flagged", "true", timeout=LOAD_TIMEOUT
    )
    expect(cell(page, 15)).to_have_attribute(
        "data-revealed", "false", timeout=LOAD_TIMEOUT
    )
    expect(cell(page, 15)).to_have_text("F", timeout=LOAD_TIMEOUT)
    expect(mines_left(page)).to_have_text("Mines left: 2", timeout=LOAD_TIMEOUT)

    cell(page, 14).click()
    expect(mines_left(page)).to_have_text("Mines left: 1", timeout=LOAD_TIMEOUT)

    cell(page, 15).click()
    expect(cell(page, 15)).to_have_attribute(
        "data-flagged", "false", timeout=LOAD_TIMEOUT
    )
    expect(mines_left(page)).to_have_text("Mines left: 2", timeout=LOAD_TIMEOUT)

    cell(page, 15).click()
    cell(page, 11).click()
    cell(page, 0).click()
    expect(mines_left(page)).to_have_text("Mines left: -1", timeout=LOAD_TIMEOUT)

    flag_mode(page).click()
    expect(flag_mode(page)).to_have_text("Flag mode: off", timeout=LOAD_TIMEOUT)

    # a flag protects its cell: index 0 is a zero-count cell that would open all
    # 13 safe cells if the reveal branch were unguarded
    cell(page, 0).click()
    expect(revealed_cells(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(mines_left(page)).to_have_text("Mines left: -1", timeout=LOAD_TIMEOUT)

    cell(page, 6).click()
    expect(revealed_cells(page)).to_have_count(1, timeout=LOAD_TIMEOUT)

    # an open cell cannot be flagged
    flag_mode(page).click()
    expect(flag_mode(page)).to_have_text("Flag mode: on", timeout=LOAD_TIMEOUT)
    cell(page, 6).click()
    expect(cell(page, 6)).to_have_attribute(
        "data-flagged", "false", timeout=LOAD_TIMEOUT
    )
    expect(mines_left(page)).to_have_text("Mines left: -1", timeout=LOAD_TIMEOUT)


def test_c_3_6_the_status_line_reads_won_then_lost_and_stays_lost(page):
    """c-3-6: clicking the cell at data-index 0 on /boards/corner leaves exactly
    13 cells at data-revealed true and game-status reading Won; clicking the
    cell at 9 on /boards/intro leaves exactly 1 cell at data-revealed true,
    shows * in it and game-status reading Lost; and a following click on 3
    leaves exactly 2 cells at data-revealed true with game-status still Lost -
    a terminal status locks nothing.

    Totals, not deltas: see A2 at the top of this file."""
    open_play(page, "corner")
    expect(cells(page)).to_have_count(16, timeout=LOAD_TIMEOUT)

    cell(page, 0).click()
    expect(revealed_cells(page)).to_have_count(13, timeout=LOAD_TIMEOUT)
    expect(game_status(page)).to_have_text("Won", timeout=LOAD_TIMEOUT)

    open_play(page, "intro")
    expect(cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    cell(page, 9).click()
    expect(revealed_cells(page)).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(cell(page, 9)).to_have_text("*", timeout=LOAD_TIMEOUT)
    expect(game_status(page)).to_have_text("Lost", timeout=LOAD_TIMEOUT)

    cell(page, 3).click()
    expect(revealed_cells(page)).to_have_count(2, timeout=LOAD_TIMEOUT)
    expect(game_status(page)).to_have_text("Lost", timeout=LOAD_TIMEOUT)
