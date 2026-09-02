"""ep-games-list at `GET /api/games` - the seed, and the frame split over HTTP.

One test per criterion, asserting only what that criterion pins. Three criteria
read this route: c-1-1 grades the scaffolding and the seed order, c-1-2 grades
the whole ten-frame split of `g-mixed`, and c-1-3 grades the six-frame split of
`g-partial`, the game whose rolls run out early.

Every expected array is a literal in `helpers.py`, copied from spec.md's Data
model table. No test in this file chunks a roll list, so nothing here can agree
with a broken `frames()` by making the same mistake.

`frames()` is graded against three fixtures rather than one - `g-mixed` (ten
frames, single-roll strikes, a three-roll tenth), `g-partial` (the rolls run
out) and, on the page, `g-perfect` (a tenth of three strikes) - so no hardcoded
frame list satisfies the cut.
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

    The 200 and the array-of-objects shape are asserted in `get_games`. The id
    list is compared as one ordered list rather than as a set, because spec.md
    says of this criterion: "It is also what grades the seed order."

    Each object is then required to carry all four keys, with `name` and `rolls`
    equal to the seed table. Those two are the inputs every other criterion's
    expected values are derived from, so a suite that never reads them cannot
    tell a re-typed or re-ordered seed from a scoring bug. `frames` is only
    required to be present and to be an array here - its contents are c-1-2 and
    c-1-3, and asserting them here would put one criterion's requirement into
    another criterion's row of the report.

    This criterion declares no cuts. spec.md: "the route and the store ship
    written, so this is green on the skeleton and tells the student the
    scaffolding is intact." It is still red before any code exists, which is
    what the red-first check reads: with no route there is no 200.
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
            f"{game_id} name is {game['name']!r}, expected {GAME_NAMES[game_id]!r}"
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
    the list fails: the single-roll strike frames at 5 and 9, the nine two-roll
    frames and the three-roll tenth are all inside the same assertion. The
    length is asserted first so a nine-frame answer names itself.

    Neither state of an unwritten block satisfies this. With `cut-frames-scan`
    open, `out` is empty and `frames` is `[]`. With only `cut-frames-tenth`
    filled, `i` is still 0, so the tenth block appends every roll as one frame
    and `frames` is `[[1,4,4,5,...,6]]`. Ten frames needs both cuts, which is
    what spec.md's Grading integrity table claims for this criterion.
    """
    game = one_game(get_games(api), "g-mixed")
    frames = game["frames"]

    assert len(frames) == 10, (
        f"g-mixed split into {len(frames)} frames, expected 10: {frames}"
    )
    assert frames == MIXED_FRAMES, (
        f"g-mixed frames are {frames}, expected {MIXED_FRAMES}"
    )


def test_c_1_3_partial_game_stops_after_six_frames_when_the_rolls_run_out(api):
    """c-1-3: GET /api/games returns the g-partial game with frames equal to
    [[3,4],[7,2],[9,0],[8,1],[10],[10]].

    Six entries, not five. g-partial closes on two strikes, each a one-roll
    frame, and its ten rolls run out before a tenth frame exists; a naive
    pair-chunking scan pairs those two strikes into `[10,10]` and answers five.
    spec.md names this "the criterion that grades the scan on its own". The
    length is asserted before the contents so a failure says which of the two
    went wrong.

    `cut-frames-tenth` contributes nothing here - the rolls run out earlier, so
    that block appends nothing - and this test is not satisfied by that block
    alone: with `cut-frames-scan` open and `cut-frames-tenth` filled, `i` is 0
    and the tenth block appends the whole roll list as a single frame, giving
    one entry where this wants six.
    """
    game = one_game(get_games(api), "g-partial")
    frames = game["frames"]

    assert len(frames) == 6, (
        f"g-partial split into {len(frames)} frames, expected 6: {frames}"
    )
    assert frames == PARTIAL_FRAMES, (
        f"g-partial frames are {frames}, expected {PARTIAL_FRAMES}"
    )
