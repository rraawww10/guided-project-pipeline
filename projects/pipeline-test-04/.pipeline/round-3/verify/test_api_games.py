"""ep-games-list at `GET /api/games` - the seed, and the frame split over HTTP.

One test per criterion, asserting only it. Three criteria read this route:
c-1-1 grades the scaffolding and the seed order, c-1-2 grades the whole
ten-frame split of `g-mixed`, and c-1-3 grades the six-frame split of
`g-partial`, which is the game whose rolls run out early.

The expected arrays are copied from spec.md's Data model table and live in
`helpers.py`. No test in this file re-chunks a roll list, so nothing here can
agree with a broken `frames()` by making the same mistake.
"""
from __future__ import annotations

from helpers import (
    GAME_IDS,
    GAME_KEYS,
    GAME_NAMES,
    GAME_ROLLS,
    MIXED_FRAMES,
    PARTIAL_FRAMES,
    get_games,
    one_game,
)


def test_c_1_1_games_are_the_four_seeded_games_in_seed_order(api):
    """c-1-1: GET /api/games returns 200 with a JSON array of 4 games whose id
    values are g-gutter, g-perfect, g-mixed and g-partial in that order, each
    carrying id, name, rolls and frames.

    The 200 and the array shape are asserted in `get_games`. The id list is
    compared as one ordered list rather than as a set, because spec.md says this
    criterion "is also what grades the seed order". Each object is then required
    to carry all four keys, with `name` and `rolls` equal to the seed table -
    those two are the inputs every other criterion's expected values are derived
    from, so a suite that never reads them cannot tell a re-ordered or re-typed
    seed from a scoring bug. `frames` is only required to be present and an
    array here; its contents are c-1-2 and c-1-3.

    This criterion declares no cuts: spec.md says the route and the store ship
    written, so it is green on the skeleton on purpose and tells the student the
    scaffolding is intact. It is red before any code exists, which is what the
    red-first check reads.
    """
    games = get_games(api)

    assert len(games) == 4, f"GET /api/games returned {len(games)} games, expected 4"
    ids = [g.get("id") for g in games]
    assert ids == GAME_IDS, f"ids are {ids} in response order, expected {GAME_IDS}"

    for game in games:
        game_id = game["id"]
        missing = [k for k in GAME_KEYS if k not in game]
        assert not missing, f"{game_id} is missing {missing}: {sorted(game)}"
        assert game["name"] == GAME_NAMES[game_id], (
            f"{game_id} name is {game['name']!r}, "
            f"expected {GAME_NAMES[game_id]!r}"
        )
        assert game["rolls"] == GAME_ROLLS[game_id], (
            f"{game_id} rolls are {game['rolls']}, expected {GAME_ROLLS[game_id]}"
        )
        assert isinstance(game["frames"], list), (
            f"{game_id} frames is {type(game['frames']).__name__}, not a JSON array"
        )


def test_c_1_2_mixed_game_splits_into_ten_frames_with_a_three_roll_tenth(api):
    """c-1-2: GET /api/games returns the g-mixed game with frames equal to
    [[1,4],[4,5],[6,4],[5,5],[10],[0,1],[7,3],[6,4],[10],[2,8,6]].

    Compared whole, in one equality, so a frame boundary that is off anywhere in
    the list fails - the single-roll strike frames at 5 and 9 and the three-roll
    tenth are all in the same assertion.

    Neither value an unwritten block produces can satisfy this: with
    `cut-frames-scan` open `out` is empty, and with only `cut-frames-tenth`
    filled `i` is still 0, so `out` holds the whole roll list as one frame.
    Nine frames is not ten, so this needs both frame cuts, which is what
    spec.md's Grading integrity table claims for it.
    """
    game = one_game(get_games(api), "g-mixed")
    assert game["frames"] == MIXED_FRAMES, (
        f"g-mixed frames are {game['frames']}, expected {MIXED_FRAMES}"
    )


def test_c_1_3_partial_game_stops_after_six_frames_when_the_rolls_run_out(api):
    """c-1-3: GET /api/games returns the g-partial game with frames equal to
    [[3,4],[7,2],[9,0],[8,1],[10],[10]].

    Six entries, not five: a naive pair-chunking scan pairs the two closing
    strikes into one frame and produces five, which is why spec.md names this
    the criterion that grades `cut-frames-scan` on its own. The length is
    asserted separately from the contents so a failure says which of the two
    went wrong.

    `cut-frames-tenth` contributes nothing here - g-partial's rolls run out
    before a tenth frame - so this test must not be satisfied by that block
    alone, and it is not: with `cut-frames-scan` open and `cut-frames-tenth`
    filled, `i` is 0 and the tenth block appends every roll as a single frame,
    giving one entry where this wants six.
    """
    game = one_game(get_games(api), "g-partial")
    frames = game["frames"]
    assert len(frames) == 6, (
        f"g-partial split into {len(frames)} frames, expected 6: {frames}"
    )
    assert frames == PARTIAL_FRAMES, (
        f"g-partial frames are {frames}, expected {PARTIAL_FRAMES}"
    )
