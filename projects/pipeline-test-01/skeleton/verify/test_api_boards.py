"""ep-board-get at GET /api/boards/[id] and ep-boards-list at GET /api/boards.

One test per criterion, each asserting only its own criterion.
"""
from __future__ import annotations

from helpers import (
    BOARD_IDS,
    FIELD_COUNT_PICKS,
    INTRO_COUNTS,
    INTRO_MINES,
    MINE_COUNTS,
)


def test_c_1_1_intro_board_answers_its_size_mines_and_twenty_five_counts(api):
    """c-1-1: GET /api/boards/intro is 200 with width 5, height 5, mines
    9, 11, 18, 23 and a counts array of exactly 25 numbers in index order."""
    r = api.get("/api/boards/intro")
    assert r.status_code == 200, f"GET /api/boards/intro answered {r.status_code}"

    body = r.json()
    assert body["width"] == 5
    assert body["height"] == 5
    assert body["mines"] == INTRO_MINES

    counts = body["counts"]
    assert len(counts) == 25, f"counts has {len(counts)} entries, expected 25"
    assert counts == INTRO_COUNTS


def test_c_1_2_field_board_counts_are_sixty_four_and_read_right_at_the_edges(api):
    """c-1-2: GET /api/boards/field is 200 with 64 counts whose entries at
    indices 0, 7, 8, 15, 54, 56, 57 and 63 are 0, 1, 1, 0, 3, 1, 2 and 0 - the
    four corners, three edge cells and the interior 3, plus index 63, which is
    itself a mine and still carries a count."""
    r = api.get("/api/boards/field")
    assert r.status_code == 200, f"GET /api/boards/field answered {r.status_code}"

    counts = r.json()["counts"]
    assert len(counts) == 64, f"counts has {len(counts)} entries, expected 64"

    got = {i: counts[i] for i in FIELD_COUNT_PICKS}
    assert got == FIELD_COUNT_PICKS


def test_c_1_3_unknown_board_answers_404_with_an_error_message(api):
    """c-1-3: GET /api/boards/no-such-board is 404 with a JSON body whose error
    key holds a non-empty string."""
    r = api.get("/api/boards/no-such-board")
    assert r.status_code == 404, f"answered {r.status_code}, expected 404"

    body = r.json()
    assert isinstance(body, dict), f"body is {type(body).__name__}, expected an object"
    assert isinstance(body.get("error"), str), f"error key: {body.get('error')!r}"
    assert body["error"] != ""


def test_c_3_1_board_index_lists_the_three_seeded_boards_in_seed_order(api):
    """c-3-1: GET /api/boards is 200 with exactly 3 entries whose ids are intro,
    field and corner in that order and whose mineCount values are 4, 10 and 3."""
    r = api.get("/api/boards")
    assert r.status_code == 200, f"GET /api/boards answered {r.status_code}"

    body = r.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, expected an array"
    assert len(body) == 3, f"{len(body)} entries, expected 3"
    assert [b["id"] for b in body] == BOARD_IDS
    assert [b["mineCount"] for b in body] == MINE_COUNTS
