"""ep-puzzles-list: GET /api/puzzles.

One test per criterion, asserting only what that criterion pins. Every clue is
compared against the literal spec.md prints, never against a value this suite
recomputes - a test that re-derives the clues would agree with a broken runsOf.
"""
from __future__ import annotations

from helpers import COL_CLUES, ROW_CLUES, SEED_ORDER

REQUIRED_KEYS = ("id", "title", "size", "rowClues", "colClues")


def _puzzles(api) -> list[dict]:
    """The list endpoint's body, with the shape every criterion here reads."""
    response = api.get("/api/puzzles")
    assert response.status_code == 200, (
        f"GET /api/puzzles answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, not a JSON array"
    for entry in body:
        assert isinstance(entry, dict), f"entry is {entry!r}, not an object"
    return body


def test_c_1_1_puzzles_list_is_boat_blanks_house_with_the_boat_row_clues(api):
    """c-1-1: 200 and a JSON array of 3 puzzles whose ids in order are boat,
    blanks and house; the boat entry has size 5, title Boat and rowClues
    [[1],[3],[5],[1,1],[1,1]], and no entry carries a solution key.

    The rowClues literal is the half that goes red against the cut-runs-of
    fallback, where `runs` starts empty and every clue derives to [].

    Reading taken: the criterion pins "no entry carries a solution key", so that
    is what this asserts. spec.md's endpoint paragraph is stricter - the five
    keys "and no other key" - but c-1-1 does not pin the key set, and
    ambiguity.md W4 records that gap as owned by nothing. Grading the stricter
    prose here would fail a Builder for something its criterion never asked, so
    it stays a Gate 1 finding rather than a silent extra assertion.
    """
    puzzles = _puzzles(api)
    assert len(puzzles) == 3, f"{len(puzzles)} puzzles: {puzzles}"
    assert [p.get("id") for p in puzzles] == SEED_ORDER, (
        f"ids are {[p.get('id') for p in puzzles]}, expected {SEED_ORDER}"
    )

    for entry in puzzles:
        for key in REQUIRED_KEYS:
            assert key in entry, f"{entry.get('id')!r} has no {key}: {entry}"
        assert "solution" not in entry, (
            f"{entry.get('id')!r} carries a solution key: {entry}"
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
    that hands the rows back unchanged fails here, and the cut-transpose
    fallback - `out` empty, so colClues serves as [] - fails here too.
    """
    by_id = {p.get("id"): p for p in _puzzles(api)}
    assert sorted(by_id) == sorted(SEED_ORDER), f"ids are {sorted(by_id)}"

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
    passes c-1-1 cannot pass this one.
    """
    by_id = {p.get("id"): p for p in _puzzles(api)}
    assert "blanks" in by_id, f"no blanks entry: ids are {sorted(by_id)}"

    blanks = by_id["blanks"]
    assert blanks["rowClues"] == ROW_CLUES["blanks"], (
        f"blanks rowClues are {blanks['rowClues']}, expected {ROW_CLUES['blanks']}"
    )
