"""sc-puzzle at /puzzles/[id]. One test per screen criterion, asserting only it.

Every element is read through the data-testid the spec pins. CSS Modules hash
the class names, so nothing here matches on a class or on styling.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    CHECK_TIMEOUT,
    COL_CLUES,
    LOAD_TIMEOUT,
    ROW_CLUES,
    all_cells,
    cell,
    clue_text,
    col_clue,
    filled_coords,
    is_check_response,
    open_puzzle,
    row_clue,
    text_of,
)


def test_c_1_4_blanks_board_draws_25_empty_cells_and_open_clue_strips(page):
    """c-1-4: /puzzles/blanks renders 25 elements with data-testid cell-0-0
    through cell-4-4 each carrying data-state empty, renders row-clue-0 with
    text 0, row-clue-1 with text 5 and col-clue-2 with text 1 2, gives each of
    row-clue-0 through row-clue-4 data-status open, and renders no solved-banner
    element."""
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
    # column 2's [1,2] reads its numbers joined by one space
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
    and no element with data-testid puzzle-title."""
    open_puzzle(page, "nope")

    missing = page.get_by_test_id("puzzle-missing")
    expect(missing).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(missing) == "Puzzle not found", (
        f"puzzle-missing reads {text_of(missing)!r}"
    )

    expect(page.get_by_test_id("cell-0-0")).to_have_count(0)
    expect(page.get_by_test_id("puzzle-title")).to_have_count(0)


def test_c_2_5_clicking_one_cell_cycles_empty_filled_crossed_empty(page):
    """c-2-5: on /puzzles/boat a first click on cell-0-2 updates its data-state
    to filled, a second click updates it to crossed and a third click updates it
    to empty, while cell-0-0 stays at data-state empty across all three
    clicks."""
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

    ambiguity.md B3 says the spec does not say which check response wins when
    two are in flight. The spec's own wording is "the value from the last check
    response", so this test takes the reading that the response to the last
    click is the one on screen, and reaches it the way that reading is true
    under either policy: it waits for each click's POST to be answered before
    sending the next, so no two are ever in flight. It therefore grades the
    board, not the Builder's ordering policy - which B3 leaves open."""
    open_puzzle(page, "blanks")
    expect(all_cells(page)).to_have_count(25, timeout=LOAD_TIMEOUT)

    coords = filled_coords("blanks")
    assert len(coords) == 13, f"the blanks solution fills {len(coords)} cells"

    for r, c in coords:
        with page.expect_response(
            lambda response: is_check_response(response, "blanks"),
            timeout=CHECK_TIMEOUT,
        ):
            cell(page, r, c).click()
        expect(cell(page, r, c)).to_have_attribute(
            "data-state", "filled", timeout=LOAD_TIMEOUT
        )

    banner = page.get_by_test_id("solved-banner")
    expect(banner).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(banner) == "Solved", f"solved-banner reads {text_of(banner)!r}"

    for r in range(5):
        expect(row_clue(page, r)).to_have_attribute(
            "data-status", "satisfied", timeout=LOAD_TIMEOUT
        )
    for c in range(5):
        expect(col_clue(page, c)).to_have_attribute(
            "data-status", "satisfied", timeout=LOAD_TIMEOUT
        )
