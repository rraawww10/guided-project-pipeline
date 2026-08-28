"""ep-board-get at GET /api/boards/[id] and ep-boards-list at GET /api/boards.

One test per criterion, asserting that criterion and nothing else.
"""
from __future__ import annotations

from helpers import INTRO_COUNTS, INTRO_MINES


def test_c_1_1_intro_board_returns_its_shape_mines_and_twenty_five_counts(api):
    """c-1-1: GET /api/boards/intro returns 200 with width 5, height 5, a mines
    array reading 9, 11, 18, 23 and a counts array of exactly 25 numbers reading
    0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 2, 2, 2, 1, 1, 3, 1, 2, 0, 0, 2, 1, 2 in
    index order.
    """
    r = api.get("/api/boards/intro")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"

    body = r.json()
    assert body["width"] == 5, f"width was {body['width']!r}"
    assert body["height"] == 5, f"height was {body['height']!r}"
    assert body["mines"] == INTRO_MINES, f"mines were {body['mines']!r}"

    counts = body["counts"]
    assert len(counts) == 25, f"counts had {len(counts)} entries, expected 25"
    assert counts == INTRO_COUNTS, f"counts were {counts!r}"


def test_c_1_2_field_board_returns_sixty_four_counts_with_the_pinned_entries(api):
    """c-1-2: GET /api/boards/field returns 200 with a counts array of exactly 64
    numbers whose entries at indices 0, 7, 8, 15, 54, 56, 57 and 63 are 0, 1, 1,
    0, 3, 1, 2 and 0.

    Four corners of the 8x8 (0, 7, 56, 63), three edge cells (8, 15, 57) and the
    interior 3 at 54 - the places a missing bounds test wraps a row or reads off
    the end. Index 15 and index 63 are themselves mines and their counts are 0
    and 0, which pins that a mine still gets a neighbour count.
    """
    r = api.get("/api/boards/field")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"

    counts = r.json()["counts"]
    assert len(counts) == 64, f"counts had {len(counts)} entries, expected 64"

    expected = {0: 0, 7: 1, 8: 1, 15: 0, 54: 3, 56: 1, 57: 2, 63: 0}
    actual = {i: counts[i] for i in expected}
    assert actual == expected, f"counts at those indices were {actual!r}"


def test_c_1_3_unknown_board_returns_404_with_a_non_empty_error(api):
    """c-1-3: GET /api/boards/no-such-board returns 404 with a JSON body whose
    error key holds a non-empty string.
    """
    r = api.get("/api/boards/no-such-board")
    assert r.status_code == 404, f"expected 404, got {r.status_code}: {r.text[:300]}"

    body = r.json()
    assert "error" in body, f"body had no error key: {body!r}"
    assert isinstance(body["error"], str), f"error was {type(body['error']).__name__}"
    assert body["error"].strip() != "", "error was an empty string"


def test_c_3_1_board_index_lists_intro_field_and_corner_with_their_mine_counts(api):
    """c-3-1: GET /api/boards returns 200 with a JSON array of exactly 3 entries
    whose id values are intro, field and corner in that order and whose mineCount
    values are 4, 10 and 3.
    """
    r = api.get("/api/boards")
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"

    body = r.json()
    assert isinstance(body, list), f"body was {type(body).__name__}, expected a list"
    assert len(body) == 3, f"body held {len(body)} entries, expected 3"

    assert [b["id"] for b in body] == ["intro", "field", "corner"], (
        f"ids were {[b.get('id') for b in body]!r}")
    assert [b["mineCount"] for b in body] == [4, 10, 3], (
        f"mineCounts were {[b.get('mineCount') for b in body]!r}")
