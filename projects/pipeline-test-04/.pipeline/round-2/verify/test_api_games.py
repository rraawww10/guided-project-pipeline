"""ep-games-list: GET /api/games - c-1-1, c-1-2, c-1-3.

One test per criterion, asserting only what that criterion pins. Every expected
value is a literal from spec.md's seed table and derived-values table, so no
test agrees with a broken `frames()` by running the same scan over the same
rolls.

ambiguity.md A2 records two readings of how `scoreGame` gets its frames, and
nothing in this file depends on the answer: session 1's criteria read `frames`
off the endpoint's own JSON, which `ep-games-list` produces as `frames(rolls)`
under either reading.
"""
from __future__ import annotations

from helpers import (
    MIXED_FRAMES,
    PARTIAL_FRAMES,
    SEED_IDS,
    SEED_NAMES,
    SEED_ROLLS,
    get_games,
    one_game,
)


def test_c_1_1_games_list_is_the_four_seeded_games_with_a_frames_key(api):
    """c-1-1: GET /api/games returns 200 with a JSON array of 4 games, each
    carrying id, name, rolls and frames.

    "Each carrying `frames`" is read here as **key presence with the value
    unconstrained**, and that is the reading spec.md's own wording forces:
    c-1-1 declares "No cut: the route and the store ship written, so this is
    green on the skeleton and tells the student the scaffolding is intact", and
    `cutter.expected_skeleton_results` requires a criterion with no cuts to PASS
    on the skeleton. On the skeleton `cut-frames-scan` is open and `frames()`
    returns the declared empty array, so demanding a non-empty list would make
    the one criterion whose whole job is to be green there fail. The frame
    *values* are graded by c-1-2 and c-1-3, which do carry those cuts.

    This is still not vacuous and does not agree with an unwritten block: it
    pins four ids, four names and all four roll lists element for element - 20
    zeros, 12 tens, the 19 mixed rolls and the 10 partial rolls - which is
    `data/games.json` and `lib/store.ts`, both shipped written, and neither
    touched by any cut.

    The array *order* is asserted from spec.md, Endpoints, ep-games-list: "in
    the seed's order: g-gutter, g-perfect, g-mixed, g-partial". ambiguity.md B4
    records (owner: nothing) that no criterion pins that order, so it is a rule
    stated in the spec's endpoint contract and nowhere in `criteria`. It is
    asserted here because this test's target *is* that endpoint and the seed
    order is the one shipped-written fact c-1-1 exists to confirm; the id-keyed
    lookups below are order-independent so a reordering failure names itself.
    """
    games = get_games(api)

    assert len(games) == 4, f"GET /api/games returned {len(games)} games, expected 4"
    assert [g.get("id") for g in games] == SEED_IDS, (
        f"game ids in array order are {[g.get('id') for g in games]}, "
        f"expected {SEED_IDS}"
    )
    assert [g.get("name") for g in games] == SEED_NAMES, (
        f"game names in array order are {[g.get('name') for g in games]}, "
        f"expected {SEED_NAMES}"
    )

    for game_id, expected_rolls in SEED_ROLLS.items():
        game = one_game(games, game_id)
        assert game.get("rolls") == expected_rolls, (
            f"{game_id} carries rolls {game.get('rolls')!r}, "
            f"expected {expected_rolls!r}"
        )
        assert "frames" in game, f"{game_id} has no frames key: {game}"
        assert isinstance(game["frames"], list), (
            f"{game_id}.frames is {type(game['frames']).__name__}, "
            f"not a JSON array"
        )


def test_c_1_2_mixed_game_frames_are_nine_frames_and_a_three_roll_tenth(api):
    """c-1-2: GET /api/games returns the g-mixed game with frames equal to
    [[1,4],[4,5],[6,4],[5,5],[10],[0,1],[7,3],[6,4],[10],[2,8,6]].

    The whole array is compared as one value, so the frame count, the one-roll
    strike frames, the two-roll open frames and the three-roll tenth are all
    pinned at once. Neither cut this criterion carries can leave it green: with
    `cut-frames-scan` open `frames()` returns the declared empty array, and with
    only `cut-frames-tenth` open it returns nine frames, and nine frames is not
    ten - which is the by-hand check spec.md's grading-integrity table claims
    and the skeleton check cannot see.
    """
    game = one_game(get_games(api), "g-mixed")
    assert game.get("frames") == MIXED_FRAMES, (
        f"g-mixed frames are {game.get('frames')!r}, expected {MIXED_FRAMES!r}"
    )


def test_c_1_3_partial_game_frames_stop_at_six_when_the_rolls_run_out(api):
    """c-1-3: GET /api/games returns the g-partial game with frames equal to
    [[3,4],[7,2],[9,0],[8,1],[10],[10]].

    This is the scan's edge case and the criterion that grades `cut-frames-scan`
    on its own: g-partial's ten rolls run out before a tenth frame, so
    `cut-frames-tenth` contributes nothing here. Six entries rather than five is
    the whole point - spec.md: "a naive pair-chunking scan produces five" - and
    comparing the array whole catches both the wrong count and a wrong split.
    The empty array an open `cut-frames-scan` leaves behind is not this value.
    """
    game = one_game(get_games(api), "g-partial")
    assert game.get("frames") == PARTIAL_FRAMES, (
        f"g-partial frames are {game.get('frames')!r}, expected {PARTIAL_FRAMES!r}"
    )
