"""ep-puzzle-check: POST /api/puzzles/[id]/check.

One test per criterion, asserting only it. Every grid posted here is built in
the test from spec.md's seed, never read back from the app, so the endpoint is
graded against the answer rather than against itself.
"""
from __future__ import annotations

from helpers import check, empty_grid, solution_grid


def test_c_2_1_boat_solution_is_solved_with_ten_satisfied_lines(api):
    """c-2-1: POST /api/puzzles/boat/check with the boat solution as the grid
    returns 200 with solved true, 5 entries in rows, 5 entries in cols, and each
    of those 10 entries equal to satisfied.

    The only criterion that pins solved true, so it is the one that grades
    cut-board-solved - whose fallback is false."""
    response = check(api, "boat", solution_grid("boat"))
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["solved"] is True, f"solved is {body['solved']!r}: {body}"
    assert len(body["rows"]) == 5, f"rows are {body['rows']}"
    assert len(body["cols"]) == 5, f"cols are {body['cols']}"
    assert body["rows"] == ["satisfied"] * 5, f"rows are {body['rows']}"
    assert body["cols"] == ["satisfied"] * 5, f"cols are {body['cols']}"


def test_c_2_2_check_answers_satisfied_open_and_violated_on_one_rule(api):
    """c-2-2: POST /api/puzzles/blanks/check with every cell empty returns 200
    with rows[0] satisfied, rows[1] open and solved false; and POST
    /api/puzzles/boat/check with row 0 set to filled, empty, filled, empty,
    empty and every other cell empty returns 200 with rows[0] violated and
    rows[1] open.

    All three answers: a [0] clue satisfied by an empty line, a line that is
    wrong-but-still-open, and a line that is genuinely violated. rows[0]
    satisfied and rows[0] violated are both red against the cut-line-status
    fallback of open."""
    blank_board = check(api, "blanks", empty_grid(5))
    assert blank_board.status_code == 200, blank_board.text
    blanks = blank_board.json()
    assert blanks["rows"][0] == "satisfied", f"rows are {blanks['rows']}"
    assert blanks["rows"][1] == "open", f"rows are {blanks['rows']}"
    assert blanks["solved"] is False, f"solved is {blanks['solved']!r}"

    two_blocks = empty_grid(5)
    two_blocks[0] = ["filled", "empty", "filled", "empty", "empty"]
    boat_board = check(api, "boat", two_blocks)
    assert boat_board.status_code == 200, boat_board.text
    boat = boat_board.json()
    assert boat["rows"][0] == "violated", f"rows are {boat['rows']}"
    assert boat["rows"][1] == "open", f"rows are {boat['rows']}"


def test_c_2_3_house_row_three_filled_grades_both_axes_of_an_eight_by_eight(api):
    """c-2-3: POST /api/puzzles/house/check with every cell of row 3 filled and
    every other cell empty returns 200 with 8 entries in rows, 8 entries in
    cols, rows[3] satisfied, rows[0] open, cols[0] satisfied and cols[3] open.

    The 8 by 8 board and the column axis of the check, in one request. The
    criterion pins nothing about solved, so neither does this test."""
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
    the string maybe returns 400, each with a JSON body whose only key is
    error."""

    def only_an_error(response, label: str) -> None:
        body = response.json()
        assert isinstance(body, dict), f"{label}: body is {body!r}"
        assert set(body) == {"error"}, f"{label}: body keys are {sorted(body)}"
        assert isinstance(body["error"], str) and body["error"], (
            f"{label}: error is {body['error']!r}"
        )

    unknown = check(api, "nope", empty_grid(5))
    assert unknown.status_code == 404, (
        f"unknown id: {unknown.status_code} {unknown.text}"
    )
    only_an_error(unknown, "unknown id")

    short = check(api, "house", empty_grid(8)[:7])
    assert short.status_code == 400, f"7 rows: {short.status_code} {short.text}"
    only_an_error(short, "7 rows")

    bad_cell = empty_grid(5)
    bad_cell[0][0] = "maybe"
    unknown_state = check(api, "boat", bad_cell)
    assert unknown_state.status_code == 400, (
        f"cell maybe: {unknown_state.status_code} {unknown_state.text}"
    )
    only_an_error(unknown_state, "cell maybe")
