"""ep-puzzle-check: POST /api/puzzles/[id]/check.

One test per criterion, asserting only it. Every grid posted here is built in
the test from spec.md's seed, never read back from the app, so the endpoint is
graded against the answer rather than against itself.
"""
from __future__ import annotations

from helpers import check, empty_grid, solution_grid


def test_c_2_1_boat_solution_is_solved_and_a_moved_cell_violates_only_a_column(api):
    """c-2-1: POST /api/puzzles/boat/check with the boat solution as the grid
    returns 200 with solved true, 5 entries in rows, 5 entries in cols, and each
    of those 10 entries equal to satisfied; then the same grid with row 0 set to
    filled, empty, empty, empty, empty returns 200 with all 5 entries of rows
    equal to satisfied, cols[0] violated, cols[2] open and solved false.

    The only criterion that pins solved true, so it is the one that grades
    cut-board-solved - whose fallback is false. The second request is the only
    shape that separates a boardSolved reading both axes from one that reads the
    rows and stops: every row still matches its clue while column 0 now holds
    two blocks against a clue of [1].
    """
    response = check(api, "boat", solution_grid("boat"))
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["solved"] is True, f"solved is {body['solved']!r}: {body}"
    assert len(body["rows"]) == 5, f"rows are {body['rows']}"
    assert len(body["cols"]) == 5, f"cols are {body['cols']}"
    assert body["rows"] == ["satisfied"] * 5, f"rows are {body['rows']}"
    assert body["cols"] == ["satisfied"] * 5, f"cols are {body['cols']}"

    # the boat row-0 cell moved from column 2 to column 0: row 0 still reads [1]
    # against its clue [1], column 0 now reads [1,1] against [1], and column 2
    # has lost its top cell so it reads [2] against [3] with empties left in it
    moved = solution_grid("boat")
    moved[0] = ["filled", "empty", "empty", "empty", "empty"]

    second = check(api, "boat", moved)
    assert second.status_code == 200, second.text

    shifted = second.json()
    assert shifted["rows"] == ["satisfied"] * 5, f"rows are {shifted['rows']}"
    assert shifted["cols"][0] == "violated", f"cols are {shifted['cols']}"
    assert shifted["cols"][2] == "open", f"cols are {shifted['cols']}"
    assert shifted["solved"] is False, f"solved is {shifted['solved']!r}: {shifted}"


def test_c_2_2_check_answers_satisfied_open_and_violated_and_reads_crossed(api):
    """c-2-2: POST /api/puzzles/blanks/check with every cell empty returns 200
    with rows[0] satisfied, rows[1] open and solved false; POST
    /api/puzzles/boat/check with row 0 set to filled, empty, filled, empty,
    empty and every other cell empty returns 200 with rows[0] violated and
    rows[1] open; POST /api/puzzles/boat/check with row 1 set to filled, filled,
    crossed, crossed, crossed and row 3 set to filled, crossed, filled, empty,
    empty and every other cell empty returns 200 with rows[1] violated and
    rows[3] satisfied.

    All three answers plus both halves of crossed. rows[0] satisfied, rows[0]
    violated, rows[1] violated and rows[3] satisfied are each red against the
    cut-line-status fallback of open.
    """
    blank_board = check(api, "blanks", empty_grid(5))
    assert blank_board.status_code == 200, blank_board.text
    blanks = blank_board.json()
    assert blanks["rows"][0] == "satisfied", f"rows are {blanks['rows']}"
    assert blanks["rows"][1] == "open", f"rows are {blanks['rows']}"
    assert blanks["solved"] is False, f"solved is {blanks['solved']!r}"

    # two blocks against a one-number clue: violated by condition 1
    two_blocks = empty_grid(5)
    two_blocks[0] = ["filled", "empty", "filled", "empty", "empty"]
    boat_board = check(api, "boat", two_blocks)
    assert boat_board.status_code == 200, boat_board.text
    boat = boat_board.json()
    assert boat["rows"][0] == "violated", f"rows are {boat['rows']}"
    assert boat["rows"][1] == "open", f"rows are {boat['rows']}"

    # row 1: no cell left empty and runsOf [2] against clue [3] - violated by
    # condition 3, which a crossed cell does not hold off
    # row 3: crossed breaks a block exactly as empty does, so [1,1] against
    # clue [1,1] is satisfied
    marked_grid = empty_grid(5)
    marked_grid[1] = ["filled", "filled", "crossed", "crossed", "crossed"]
    marked_grid[3] = ["filled", "crossed", "filled", "empty", "empty"]
    marked_board = check(api, "boat", marked_grid)
    assert marked_board.status_code == 200, marked_board.text
    marked = marked_board.json()
    assert marked["rows"][1] == "violated", f"rows are {marked['rows']}"
    assert marked["rows"][3] == "satisfied", f"rows are {marked['rows']}"


def test_c_2_3_house_row_three_filled_grades_both_axes_of_an_eight_by_eight(api):
    """c-2-3: POST /api/puzzles/house/check with every cell of row 3 filled and
    every other cell empty returns 200 with 8 entries in rows, 8 entries in
    cols, rows[3] satisfied, rows[0] open, cols[0] satisfied and cols[3] open.

    The 8 by 8 board and the column axis of the check, in one request. The
    criterion pins nothing about solved, so neither does this test.
    """
    grid = empty_grid(8)
    grid[3] = ["filled"] * 8

    response = check(api, "house", grid)
    assert response.status_code == 200, response.text

    body = response.json()
    assert len(body["rows"]) == 8, f"rows are {body['rows']}"
    assert len(body["cols"]) == 8, f"cols are {body['cols']}"
    assert body["rows"][3] == "satisfied", f"rows are {body['rows']}"
    assert body["rows"][0] == "open", f"rows are {body['rows']}"
    assert body["cols"][0] == "satisfied", f"cols are {body['cols']}"
    assert body["cols"][3] == "open", f"cols are {body['cols']}"


def test_c_2_4_unknown_id_is_404_and_a_bad_grid_is_400_with_only_an_error_key(api):
    """c-2-4: POST /api/puzzles/nope/check with a 5 by 5 grid of empty cells
    returns 404, POST /api/puzzles/house/check with a grid of 7 rows returns
    400, and POST /api/puzzles/boat/check with the cell at row 0 column 0 set to
    the string maybe returns 400, each with a JSON body whose only key is error.
    """
    unknown = check(api, "nope", empty_grid(5))
    assert unknown.status_code == 404, (
        f"unknown id: {unknown.status_code} {unknown.text}"
    )
    unknown_body = unknown.json()
    assert set(unknown_body) == {"error"}, f"unknown id: keys {sorted(unknown_body)}"
    assert isinstance(unknown_body["error"], str) and unknown_body["error"], (
        f"unknown id: error is {unknown_body['error']!r}"
    )

    short = check(api, "house", empty_grid(8)[:7])
    assert short.status_code == 400, f"7 rows: {short.status_code} {short.text}"
    short_body = short.json()
    assert set(short_body) == {"error"}, f"7 rows: keys {sorted(short_body)}"
    assert isinstance(short_body["error"], str) and short_body["error"], (
        f"7 rows: error is {short_body['error']!r}"
    )

    bad_cell = empty_grid(5)
    bad_cell[0][0] = "maybe"
    bad = check(api, "boat", bad_cell)
    assert bad.status_code == 400, f"cell maybe: {bad.status_code} {bad.text}"
    bad_body = bad.json()
    assert set(bad_body) == {"error"}, f"cell maybe: keys {sorted(bad_body)}"
    assert isinstance(bad_body["error"], str) and bad_body["error"], (
        f"cell maybe: error is {bad_body['error']!r}"
    )
