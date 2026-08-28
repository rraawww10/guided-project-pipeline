"""ep-board-replay at POST /api/boards/[id]/replay.

The endpoint folds an ordered list of clicks into one open set and one status,
so revealFrom and gameStatus are both graded here with no browser involved.

One test per criterion, each asserting only its own criterion.
"""
from __future__ import annotations

from helpers import CORNER_FROM_0, FIELD_FROM_0, INTRO_FROM_20


def replay(api, board_id: str, body: dict):
    return api.post(f"/api/boards/{board_id}/replay", json=body)


def assert_error_body(r, where: str) -> None:
    """Every non-200 body is a JSON object with a non-empty error message."""
    body = r.json()
    assert isinstance(body, dict), f"{where}: body is {type(body).__name__}"
    assert isinstance(body.get("error"), str), f"{where}: error is {body.get('error')!r}"
    assert body["error"] != "", f"{where}: error is the empty string"


def test_c_2_1_one_click_on_field_index_zero_opens_exactly_fourteen_cells(api):
    """c-2-1: POST /api/boards/field/replay with body {"clicks": [0]} is 200
    with a revealed array of exactly 14 entries reading 0, 1, 2, 3, 4, 5, 6, 8,
    9, 10, 11, 12, 13, 14 ascending. A fill that walks out of numbered cells
    opens 54 here, so the count alone separates the two rules."""
    r = replay(api, "field", {"clicks": [0]})
    assert r.status_code == 200, f"answered {r.status_code}, expected 200"

    revealed = r.json()["revealed"]
    assert len(revealed) == 14, f"{len(revealed)} entries, expected 14"
    assert revealed == FIELD_FROM_0


def test_c_2_2_intro_opens_a_zero_region_a_number_and_a_mine(api):
    """c-2-2: on intro, clicks [20] opens exactly 6 cells reading 15, 16, 17,
    20, 21, 22, clicks [3] opens exactly 1 reading 3, and clicks [9] opens
    exactly 1 reading 9 - so a fill that always expands and a fill that never
    expands are both red."""
    r20 = replay(api, "intro", {"clicks": [20]})
    assert r20.status_code == 200, f"clicks [20] answered {r20.status_code}"
    revealed20 = r20.json()["revealed"]
    assert len(revealed20) == 6, f"clicks [20]: {len(revealed20)} entries, expected 6"
    assert revealed20 == INTRO_FROM_20

    r3 = replay(api, "intro", {"clicks": [3]})
    assert r3.status_code == 200, f"clicks [3] answered {r3.status_code}"
    revealed3 = r3.json()["revealed"]
    assert len(revealed3) == 1, f"clicks [3]: {len(revealed3)} entries, expected 1"
    assert revealed3 == [3]

    r9 = replay(api, "intro", {"clicks": [9]})
    assert r9.status_code == 200, f"clicks [9] answered {r9.status_code}"
    revealed9 = r9.json()["revealed"]
    assert len(revealed9) == 1, f"clicks [9]: {len(revealed9)} entries, expected 1"
    assert revealed9 == [9]


def test_c_2_3_replay_resolves_the_board_first_then_validates_the_body(api):
    """c-2-3: an unknown board is 404 for a good body and for a malformed one,
    intro is 400 for a missing clicks, a string clicks and an out-of-range
    index, all 5 carry a non-empty error, and an empty clicks list is a valid
    request answering 200 with 0 revealed and 0 flagged."""
    missing_good = replay(api, "no-such-board", {"clicks": [0]})
    assert missing_good.status_code == 404, (
        f"no-such-board with a valid body answered {missing_good.status_code}")
    assert_error_body(missing_good, "no-such-board + valid body")

    missing_bad = replay(api, "no-such-board", {"bogus": 1})
    assert missing_bad.status_code == 404, (
        f"no-such-board with a malformed body answered {missing_bad.status_code} - "
        f"the board id is resolved before the body is read")
    assert_error_body(missing_bad, "no-such-board + malformed body")

    for body, where in (
        ({}, "intro + no clicks key"),
        ({"clicks": "0"}, "intro + clicks as a string"),
        ({"clicks": [25]}, "intro + an index off the 25-cell board"),
    ):
        r = replay(api, "intro", body)
        assert r.status_code == 400, f"{where} answered {r.status_code}, expected 400"
        assert_error_body(r, where)

    empty = replay(api, "intro", {"clicks": []})
    assert empty.status_code == 200, (
        f"intro + an empty clicks list answered {empty.status_code}, expected 200")
    empty_body = empty.json()
    assert len(empty_body["revealed"]) == 0, f"revealed: {empty_body['revealed']}"
    assert len(empty_body["flagged"]) == 0, (
        f"flagged: {empty_body.get('flagged')!r} - with no flags key the response "
        f"carries an empty array, not a missing one")


def test_c_3_2_corner_is_won_in_one_click_and_still_playing_after_a_number(api):
    """c-3-2: on corner, clicks [0] is 200 with status won and exactly 13
    revealed reading 0 to 10, 12, 13, and clicks [6] is 200 with status playing
    and exactly 1 revealed reading 6."""
    won = replay(api, "corner", {"clicks": [0]})
    assert won.status_code == 200, f"clicks [0] answered {won.status_code}"
    won_body = won.json()
    assert won_body["status"] == "won", f"status is {won_body['status']!r}"
    assert len(won_body["revealed"]) == 13, (
        f"{len(won_body['revealed'])} entries, expected 13")
    assert won_body["revealed"] == CORNER_FROM_0

    playing = replay(api, "corner", {"clicks": [6]})
    assert playing.status_code == 200, f"clicks [6] answered {playing.status_code}"
    playing_body = playing.json()
    assert playing_body["status"] == "playing", f"status is {playing_body['status']!r}"
    assert len(playing_body["revealed"]) == 1, (
        f"{len(playing_body['revealed'])} entries, expected 1")
    assert playing_body["revealed"] == [6]


def test_c_3_3_a_mine_in_the_list_reads_lost_even_on_the_winning_count(api):
    """c-3-3: corner [0, 15] is lost with 14 revealed, intro [0, 20] is still
    playing with 14 revealed, and the 9-click list on intro is lost with exactly
    21 revealed that holds the mine at 9 - 21 is also the win threshold on intro
    (25 - 4), so an implementation that tests won before lost answers won there
    and is red."""
    lost = replay(api, "corner", {"clicks": [0, 15]})
    assert lost.status_code == 200, f"corner [0, 15] answered {lost.status_code}"
    lost_body = lost.json()
    assert lost_body["status"] == "lost", f"corner [0, 15]: {lost_body['status']!r}"
    assert len(lost_body["revealed"]) == 14, (
        f"corner [0, 15]: {len(lost_body['revealed'])} entries, expected 14")

    playing = replay(api, "intro", {"clicks": [0, 20]})
    assert playing.status_code == 200, f"intro [0, 20] answered {playing.status_code}"
    playing_body = playing.json()
    assert playing_body["status"] == "playing", (
        f"intro [0, 20]: {playing_body['status']!r}")
    assert len(playing_body["revealed"]) == 14, (
        f"intro [0, 20]: {len(playing_body['revealed'])} entries, expected 14")

    order = replay(api, "intro", {"clicks": [0, 20, 4, 10, 12, 13, 14, 19, 9]})
    assert order.status_code == 200, f"the 9-click list answered {order.status_code}"
    order_body = order.json()
    assert order_body["status"] == "lost", (
        f"the 9-click list on intro: {order_body['status']!r} - 21 revealed against "
        f"a win threshold of 21, one of them the mine at 9, must read lost")
    assert len(order_body["revealed"]) == 21, (
        f"the 9-click list on intro: {len(order_body['revealed'])} entries, "
        f"expected 21")
    assert 9 in order_body["revealed"]


def test_c_3_4_flags_come_back_sorted_and_deduplicated_without_winning(api):
    """c-3-4: corner with clicks [6] and flags [15, 11, 14, 15] is 200 with
    status playing, exactly 1 revealed reading 6 and exactly 3 flagged reading
    11, 14, 15 - all three mines flagged and the game is still playing, because
    the win rule never consults flags."""
    r = replay(api, "corner", {"clicks": [6], "flags": [15, 11, 14, 15]})
    assert r.status_code == 200, f"answered {r.status_code}, expected 200"

    body = r.json()
    assert body["status"] == "playing", (
        f"status is {body['status']!r} - flagging every mine does not win")
    assert len(body["revealed"]) == 1, f"{len(body['revealed'])} revealed, expected 1"
    assert body["revealed"] == [6]
    assert len(body["flagged"]) == 3, f"{len(body['flagged'])} flagged, expected 3"
    assert body["flagged"] == [11, 14, 15]
