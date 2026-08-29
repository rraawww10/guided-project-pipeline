"""ep-puzzle-check: POST /api/puzzles/[id]/check.

One test per criterion, asserting only what that criterion pins. Every grid is
built here from the seed strings spec.md prints, and every expected status is
the literal the criterion names - the suite never asks the app to grade itself.
"""
from __future__ import annotations

from helpers import CROSSED, EMPTY, FILLED, check, empty_grid, solution_grid


def _result(response) -> dict:
    """A 200 CheckResult, with the shape every criterion here reads."""
    assert response.status_code == 200, (
        f"check answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, dict), f"body is {type(body).__name__}, not an object"
    for key in ("rows", "cols", "solved"):
        assert key in body, f"the result has no {key}: {body}"
    assert isinstance(body["rows"], list), f"rows is {body['rows']!r}"
    assert isinstance(body["cols"], list), f"cols is {body['cols']!r}"
    return body


def test_c_2_1_boat_solution_is_solved_and_a_moved_cell_violates_column_zero(api):
    """c-2-1: POST /api/puzzles/boat/check with the boat solution as the grid -
    the five rows ..#.., .###., #####, .#.#. and .#.#., reading # as filled and
    . as empty - returns 200 with solved true, 5 entries in rows, 5 entries in
    cols and each of those 10 entries equal to satisfied; then the same grid
    with row 0 set to filled, empty, empty, empty, empty returns 200 with all 5
    entries of rows equal to satisfied, cols[0] violated, cols[2] open and
    solved false.

    The second request is the one that separates a boardSolved reading both axes
    from one that reads the rows and stops: every row still matches its clue,
    while column 0 now holds two blocks against a clue of [1].
    """
    solved = _result(check(api, "boat", solution_grid("boat")))
    assert solved["rows"] == ["satisfied"] * 5, f"rows are {solved['rows']}"
    assert solved["cols"] == ["satisfied"] * 5, f"cols are {solved['cols']}"
    assert solved["solved"] is True, f"solved is {solved['solved']!r}"

    moved = solution_grid("boat")
    moved[0] = [FILLED, EMPTY, EMPTY, EMPTY, EMPTY]
    body = _result(check(api, "boat", moved))
    assert body["rows"] == ["satisfied"] * 5, f"rows are {body['rows']}"
    assert len(body["cols"]) == 5, f"cols are {body['cols']}"
    assert body["cols"][0] == "violated", f"cols[0] is {body['cols'][0]!r}"
    assert body["cols"][2] == "open", f"cols[2] is {body['cols'][2]!r}"
    assert body["solved"] is False, f"solved is {body['solved']!r}"


def test_c_2_2_check_answers_satisfied_open_and_violated_and_reads_crossed(api):
    """c-2-2: blanks with every cell empty returns 200 with rows[0] satisfied,
    rows[1] open and solved false; boat with row 0 set to filled, empty, filled,
    empty, empty and every other cell empty returns 200 with rows[0] violated
    and rows[1] open; boat with row 1 set to filled, filled, crossed, crossed,
    crossed and row 3 set to filled, crossed, filled, empty, empty and every
    other cell empty returns 200 with rows[1] violated and rows[3] satisfied.

    All three answers, plus both halves of crossed: a crossed cell breaks a
    block, so row 3 reads [1,1] and is satisfied, and a crossed cell counts as
    decided, so row 1 with nothing empty left in it is violated rather than open.
    """
    blank = _result(check(api, "blanks", empty_grid(5)))
    assert blank["rows"][0] == "satisfied", f"rows[0] is {blank['rows'][0]!r}"
    assert blank["rows"][1] == "open", f"rows[1] is {blank['rows'][1]!r}"
    assert blank["solved"] is False, f"solved is {blank['solved']!r}"

    two_blocks = empty_grid(5)
    two_blocks[0] = [FILLED, EMPTY, FILLED, EMPTY, EMPTY]
    body = _result(check(api, "boat", two_blocks))
    assert body["rows"][0] == "violated", f"rows[0] is {body['rows'][0]!r}"
    assert body["rows"][1] == "open", f"rows[1] is {body['rows'][1]!r}"

    crossed = empty_grid(5)
    crossed[1] = [FILLED, FILLED, CROSSED, CROSSED, CROSSED]
    crossed[3] = [FILLED, CROSSED, FILLED, EMPTY, EMPTY]
    body = _result(check(api, "boat", crossed))
    assert body["rows"][1] == "violated", f"rows[1] is {body['rows'][1]!r}"
    assert body["rows"][3] == "satisfied", f"rows[3] is {body['rows'][3]!r}"


def test_c_2_3_house_row_three_filled_grades_both_axes_of_an_eight_by_eight(api):
    """c-2-3: POST /api/puzzles/house/check with every cell of row 3 filled and
    every other cell empty returns 200 with 8 entries in rows, 8 entries in
    cols, rows[3] satisfied, rows[0] open, cols[0] satisfied and cols[3] open.

    The 8 by 8 board and the column axis of the check in one request: cols[0]
    reads [1] against the house clue [1], while cols[3] reads [1] against [4,2]
    and still has empty cells, so it is open rather than violated.
    """
    grid = empty_grid(8)
    grid[3] = [FILLED] * 8
    body = _result(check(api, "house", grid))

    assert len(body["rows"]) == 8, f"rows are {body['rows']}"
    assert len(body["cols"]) == 8, f"cols are {body['cols']}"
    assert body["rows"][3] == "satisfied", f"rows[3] is {body['rows'][3]!r}"
    assert body["rows"][0] == "open", f"rows[0] is {body['rows'][0]!r}"
    assert body["cols"][0] == "satisfied", f"cols[0] is {body['cols'][0]!r}"
    assert body["cols"][3] == "open", f"cols[3] is {body['cols'][3]!r}"


def test_c_2_4_unknown_id_is_404_and_a_bad_grid_is_400_with_only_an_error_key(api):
    """c-2-4: POST /api/puzzles/nope/check with a 5 by 5 grid of empty cells
    returns 404, POST /api/puzzles/house/check with a grid of 7 rows returns
    400, and POST /api/puzzles/boat/check with the cell at row 0 column 0 set to
    the string maybe returns 400, each with a JSON body whose only key is error.

    The id is resolved before the body is validated, which is why the first
    request answers 404 with a grid that would be the wrong size for house.
    """
    short_house = [[EMPTY] * 8 for _ in range(7)]
    bad_cell = empty_grid(5)
    bad_cell[0][0] = "maybe"

    cases = [
        ("nope", empty_grid(5), 404),
        ("house", short_house, 400),
        ("boat", bad_cell, 400),
    ]
    for puzzle_id, grid, expected in cases:
        response = check(api, puzzle_id, grid)
        assert response.status_code == expected, (
            f"POST /api/puzzles/{puzzle_id}/check answered "
            f"{response.status_code}, expected {expected}: {response.text[:400]}"
        )
        body = response.json()
        assert isinstance(body, dict), f"body is {type(body).__name__}, not an object"
        assert list(body.keys()) == ["error"], (
            f"{puzzle_id} error body carries {sorted(body)}, expected only error"
        )
        assert isinstance(body["error"], str) and body["error"].strip(), (
            f"{puzzle_id} error is {body['error']!r}, expected a non-empty message"
        )
