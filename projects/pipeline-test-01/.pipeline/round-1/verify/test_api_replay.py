"""ep-board-replay at POST /api/boards/[id]/replay.

The server-side grading surface for both pure functions: `revealFrom` through
`revealed` (c-2-1, c-2-2) and `gameStatus` through `status` (c-3-2, c-3-3,
c-3-4), with no DOM involved. One test per criterion.
"""
from __future__ import annotations


def _error_of(response) -> str:
    body = response.json()
    assert "error" in body, f"body had no error key: {body!r}"
    assert isinstance(body["error"], str), f"error was {type(body['error']).__name__}"
    return body["error"]


def test_c_2_1_field_click_on_zero_opens_exactly_fourteen_cells(api):
    """c-2-1: POST /api/boards/field/replay with body {"clicks": [0]} returns 200
    with a revealed array of exactly 14 entries reading 0, 1, 2, 3, 4, 5, 6, 8,
    9, 10, 11, 12, 13, 14 in ascending order.

    This is the boundary rule: a fill that walks out of numbered cells opens 54
    here instead of 14, and the list below separates the two outright.
    """
    r = api.post("/api/boards/field/replay", json={"clicks": [0]})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"

    revealed = r.json()["revealed"]
    assert len(revealed) == 14, f"revealed held {len(revealed)} entries: {revealed!r}"
    assert revealed == [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14], (
        f"revealed was {revealed!r}")


def test_c_2_2_intro_opens_a_region_a_number_and_a_mine(api):
    """c-2-2: POST /api/boards/intro/replay returns 200 with a revealed array of
    exactly 6 entries reading 15, 16, 17, 20, 21, 22 for body {"clicks": [20]},
    of exactly 1 entry reading 3 for body {"clicks": [3]}, and of exactly 1 entry
    reading 9 for body {"clicks": [9]}.

    Three inputs on one board: the second zero region, a numbered cell that opens
    only itself, and a click straight onto a mine. A fill that always expands and
    a fill that never expands are both red here.
    """
    cases = [
        ([20], [15, 16, 17, 20, 21, 22]),
        ([3], [3]),
        ([9], [9]),
    ]
    for clicks, expected in cases:
        r = api.post("/api/boards/intro/replay", json={"clicks": clicks})
        assert r.status_code == 200, (
            f"clicks {clicks}: expected 200, got {r.status_code}: {r.text[:300]}")

        revealed = r.json()["revealed"]
        assert len(revealed) == len(expected), (
            f"clicks {clicks}: revealed held {len(revealed)} entries, expected "
            f"{len(expected)}: {revealed!r}")
        assert revealed == expected, f"clicks {clicks}: revealed was {revealed!r}"


def test_c_2_3_replay_answers_404_for_an_unknown_board_and_400_for_a_bad_body(api):
    """c-2-3: POST /api/boards/no-such-board/replay with body {"clicks": [0]}
    returns 404, POST /api/boards/intro/replay returns 400 for body {}, for body
    {"clicks": "0"} and for body {"clicks": [25]}, and each of those 4 responses
    carries a JSON body whose error key holds a non-empty string.
    """
    cases = [
        ("/api/boards/no-such-board/replay", {"clicks": [0]}, 404),
        ("/api/boards/intro/replay", {}, 400),
        ("/api/boards/intro/replay", {"clicks": "0"}, 400),
        ("/api/boards/intro/replay", {"clicks": [25]}, 400),
    ]
    for path, body, expected_status in cases:
        r = api.post(path, json=body)
        assert r.status_code == expected_status, (
            f"POST {path} {body!r}: expected {expected_status}, got "
            f"{r.status_code}: {r.text[:300]}")
        assert _error_of(r).strip() != "", (
            f"POST {path} {body!r}: error was an empty string")


def test_c_3_2_corner_replay_reads_won_on_one_click_and_playing_on_another(api):
    """c-3-2: POST /api/boards/corner/replay returns 200 with status won and a
    revealed array of exactly 13 entries reading 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
    10, 12, 13 for body {"clicks": [0]}, and returns 200 with status playing and
    a revealed array of exactly 1 entry reading 6 for body {"clicks": [6]}.
    """
    r = api.post("/api/boards/corner/replay", json={"clicks": [0]})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
    body = r.json()
    revealed = body["revealed"]
    assert len(revealed) == 13, f"revealed held {len(revealed)} entries: {revealed!r}"
    assert revealed == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13], (
        f"revealed was {revealed!r}")
    assert body["status"] == "won", f"status was {body['status']!r}, expected won"

    r = api.post("/api/boards/corner/replay", json={"clicks": [6]})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
    body = r.json()
    revealed = body["revealed"]
    assert len(revealed) == 1, f"revealed held {len(revealed)} entries: {revealed!r}"
    assert revealed == [6], f"revealed was {revealed!r}"
    assert body["status"] == "playing", (
        f"status was {body['status']!r}, expected playing")


def test_c_3_3_replay_reads_lost_on_a_mine_and_playing_short_of_the_win(api):
    """c-3-3: POST /api/boards/corner/replay with body {"clicks": [0, 15]}
    returns 200 with status lost and a revealed array of exactly 14 entries, and
    POST /api/boards/intro/replay with body {"clicks": [0, 20]} returns 200 with
    status playing and a revealed array of exactly 14 entries.

    Two boards, same revealed count, opposite status - so a rule that reads the
    count alone is red on one of them.
    """
    r = api.post("/api/boards/corner/replay", json={"clicks": [0, 15]})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
    body = r.json()
    assert len(body["revealed"]) == 14, (
        f"corner revealed held {len(body['revealed'])} entries: {body['revealed']!r}")
    assert body["status"] == "lost", f"corner status was {body['status']!r}"

    r = api.post("/api/boards/intro/replay", json={"clicks": [0, 20]})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"
    body = r.json()
    assert len(body["revealed"]) == 14, (
        f"intro revealed held {len(body['revealed'])} entries: {body['revealed']!r}")
    assert body["status"] == "playing", f"intro status was {body['status']!r}"


def test_c_3_4_flags_ride_through_the_replay_without_touching_the_status(api):
    """c-3-4: POST /api/boards/corner/replay with body
    {"clicks": [6], "flags": [11, 14, 15]} returns 200 with status playing, a
    revealed array of exactly 1 entry reading 6 and a flagged array reading 11,
    14, 15.

    All three of corner's mines are flagged and one cell is open: the win rule
    never consults flags, so this is still playing.
    """
    r = api.post("/api/boards/corner/replay",
                 json={"clicks": [6], "flags": [11, 14, 15]})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:300]}"

    body = r.json()
    revealed = body["revealed"]
    assert len(revealed) == 1, f"revealed held {len(revealed)} entries: {revealed!r}"
    assert revealed == [6], f"revealed was {revealed!r}"
    assert body["flagged"] == [11, 14, 15], f"flagged was {body['flagged']!r}"
    assert body["status"] == "playing", (
        f"status was {body['status']!r}, expected playing")
