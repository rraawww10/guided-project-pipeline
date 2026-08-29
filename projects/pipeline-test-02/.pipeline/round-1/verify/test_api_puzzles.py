"""ep-puzzles-list: GET /api/puzzles. One test per criterion, asserting only it.

Every clue literal here is the derivation printed in spec.md's "Derived, never
stored" table. The endpoint hands out no solution, so a test that wants to know
the right answer has to carry it, and the suite does - in `helpers.SOLUTIONS`.
"""
from __future__ import annotations

from helpers import COL_CLUES, ROW_CLUES, SEED_ORDER


def test_c_1_1_puzzles_list_is_boat_blanks_house_with_the_boat_row_clues(api):
    """c-1-1: 200 and a JSON array of 3 puzzles whose ids in order are boat,
    blanks and house; the boat entry has size 5, title Boat and rowClues
    [[1],[3],[5],[1,1],[1,1]], and no entry carries a solution key."""
    response = api.get("/api/puzzles")
    assert response.status_code == 200, response.text

    puzzles = response.json()
    assert isinstance(puzzles, list), f"body is {type(puzzles).__name__}, not a list"
    assert len(puzzles) == 3, f"{len(puzzles)} puzzles: {puzzles}"

    ids = [p.get("id") for p in puzzles]
    assert ids == SEED_ORDER, f"ids are {ids}, expected {SEED_ORDER}"

    for puzzle in puzzles:
        assert "solution" not in puzzle, (
            f"{puzzle.get('id')!r} carries a solution key: {sorted(puzzle)}"
        )

    boat = puzzles[0]
    assert boat["size"] == 5, f"boat size is {boat['size']!r}"
    assert boat["title"] == "Boat", f"boat title is {boat['title']!r}"
    assert boat["rowClues"] == ROW_CLUES["boat"], (
        f"boat rowClues are {boat['rowClues']}, expected {ROW_CLUES['boat']}"
    )


def test_c_1_2_puzzles_list_col_clues_are_transposed_for_boat_and_house(api):
    """c-1-2: the boat entry has colClues [[1],[4],[3],[4],[1]] and the house
    entry has size 8 and colClues [[1],[6],[3],[4,2],[4,2],[3],[6],[1]].

    Both boards have colClues that differ from their rowClues, so a transpose
    that hands the rows back unchanged is red here."""
    response = api.get("/api/puzzles")
    assert response.status_code == 200, response.text

    by_id = {p["id"]: p for p in response.json()}
    assert "boat" in by_id and "house" in by_id, f"ids are {sorted(by_id)}"

    boat, house = by_id["boat"], by_id["house"]
    assert boat["colClues"] == COL_CLUES["boat"], (
        f"boat colClues are {boat['colClues']}, expected {COL_CLUES['boat']}"
    )
    assert house["size"] == 8, f"house size is {house['size']!r}"
    assert house["colClues"] == COL_CLUES["house"], (
        f"house colClues are {house['colClues']}, expected {COL_CLUES['house']}"
    )


def test_c_1_3_puzzles_list_blanks_row_clues_cover_the_empty_full_and_last_cell_runs(api):
    """c-1-3: the blanks entry has rowClues [[0],[5],[1,1],[3],[1,1,1]], so the
    empty row reads [0], the full row reads [5], and the run that ends at the
    last cell of row 4 is counted.

    The second fixture for runsOf and its edge case: a 5-element literal that
    passes c-1-1 cannot pass this."""
    response = api.get("/api/puzzles")
    assert response.status_code == 200, response.text

    by_id = {p["id"]: p for p in response.json()}
    assert "blanks" in by_id, f"ids are {sorted(by_id)}"

    blanks = by_id["blanks"]
    assert blanks["rowClues"] == ROW_CLUES["blanks"], (
        f"blanks rowClues are {blanks['rowClues']}, "
        f"expected {ROW_CLUES['blanks']}"
    )
