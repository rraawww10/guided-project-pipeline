"""ep-games-score at `POST /api/games/score` - the cumulative array, the total,
and the two rejections.

One test per criterion, asserting only it. The handler does not read the store;
it scores whatever roll list it is given, so every fixture here is a roll list
copied from spec.md's seed table and every expected array is copied from
spec.md's derived table. Nothing in this file adds up a frame or looks ahead in a
roll list, so no test can agree with a broken `scoreGame` by repeating its
mistake.

Three games are posted rather than one, deliberately: spec.md's Data model says
"`g-perfect` alone is satisfied by `30 * frame` and `g-gutter` alone is satisfied
by `0`", so the whole cumulative array is pinned for g-perfect, g-mixed and
g-partial, and c-2-4 pins two different totals rather than one.
"""
from __future__ import annotations

from helpers import (
    ERROR_BODY,
    EMPTY_GAME_TOTAL,
    GUTTER_ROLLS,
    GUTTER_TOTAL,
    MIXED_ROLLS,
    MIXED_SCORES,
    PARTIAL_ROLLS,
    PARTIAL_SCORES,
    PARTIAL_TOTAL,
    PERFECT_ROLLS,
    PERFECT_SCORES,
    post_score,
    score_ok,
)


def test_c_2_1_perfect_game_scores_thirty_a_frame_to_three_hundred(api):
    """c-2-1: POST /api/games/score returns 200 with frames equal to
    [30,60,90,120,150,180,210,240,270,300] for the 12 rolls of g-perfect.

    The 200 is asserted in `score_ok`. The array is compared whole, so the
    tenth frame - the one whose bonus rolls are its own second and third rolls -
    is graded in the same assertion as the first nine.

    Not a value an unwritten block produces: with `cut-score-lookahead` open
    every frame scores its declared `null` fallback, so the array is ten nulls
    and not one entry of this list appears.
    """
    body = score_ok(api, PERFECT_ROLLS)
    assert body["frames"] == PERFECT_SCORES, (
        f"g-perfect frames are {body['frames']}, expected {PERFECT_SCORES}"
    )


def test_c_2_2_mixed_game_cumulative_array_that_thirty_a_frame_cannot_fake(api):
    """c-2-2: POST /api/games/score returns frames equal to
    [5,14,29,49,60,61,77,97,117,133] for the 19 rolls of g-mixed.

    spec.md calls this "the array that `30 * frame` cannot fake and the one to
    read first when session 2 goes red": it mixes open frames, spares, a strike
    at frame 5 and a spare-closing tenth, so two errors that cancel cannot go
    green against it. Compared whole and in order, which is what makes the
    per-frame steps (5, 9, 15, 20, 11, 1, 16, 20, 20, 16) part of the assertion
    rather than just the 133 at the end.
    """
    body = score_ok(api, MIXED_ROLLS)
    assert body["frames"] == MIXED_SCORES, (
        f"g-mixed frames are {body['frames']}, expected {MIXED_SCORES}"
    )


def test_c_2_3_partial_game_leaves_its_last_two_frames_null(api):
    """c-2-3: POST /api/games/score returns frames equal to
    [7,16,25,34,null,null] for the 10 rolls of g-partial.

    Asserted exactly as the criterion words it: six entries, the first four
    numbers and the last two JSON `null`, which arrive as Python None. The
    equality distinguishes None from 0 and from the string "null", which is the
    distinction the whole project exists to teach.

    What this test does not prove, stated here because spec.md states it in
    Grading integrity rather than leaving it to be discovered: an unguarded
    lookahead past the end of `rolls` yields NaN, `JSON.stringify(NaN)` is
    `null`, so this body can match byte for byte with `cut-pending-frame` still
    empty. c-2-4 (a total, where NaN is not 34) and c-2-6 (a page, where NaN is
    not an empty cell) are the two that catch that. This suite asserts what the
    criterion says and does not try to reach behind the serialisation for a NaN
    it cannot see over HTTP - ambiguity.md's blocking finding A1 is about which
    function owns that guard, and it is a decision for the person at Gate 1, not
    something a test can pick.
    """
    body = score_ok(api, PARTIAL_ROLLS)
    frames = body["frames"]
    assert len(frames) == 6, (
        f"g-partial scored {len(frames)} frames, expected 6: {frames}"
    )
    assert frames == PARTIAL_SCORES, (
        f"g-partial frames are {frames}, expected {PARTIAL_SCORES}"
    )


def test_c_2_4_total_is_the_last_scored_frame_for_partial_and_zero_for_gutter(api):
    """c-2-4: POST /api/games/score returns total 34 for the 10 rolls of
    g-partial and total 0 for the 20 rolls of g-gutter.

    Two inputs, because one cannot tell a real "last frame that has a score"
    from a constant. 34 is g-partial's fourth frame and not its last entry -
    frames 5 and 6 are null - and 0 is a whole game of gutter balls, so a
    `total` that returns the final array entry, or the array length, or the sum
    of the array, fails on one of the two.

    Neither number is a value an unwritten block produces: `gameTotal`'s
    declared fallback is -1, which spec.md requires precisely so that this
    criterion's g-gutter half cannot pass on an empty skeleton, and an open
    `cut-pending-frame` leaves g-partial's total at NaN rather than 34.
    """
    partial = score_ok(api, PARTIAL_ROLLS)
    assert partial["total"] == PARTIAL_TOTAL, (
        f"g-partial total is {partial['total']!r}, expected {PARTIAL_TOTAL}"
    )

    gutter = score_ok(api, GUTTER_ROLLS)
    assert gutter["total"] == GUTTER_TOTAL, (
        f"g-gutter total is {gutter['total']!r}, expected {GUTTER_TOTAL}"
    )


def test_c_2_5_bad_rolls_and_bad_json_are_the_same_four_hundred_and_empty_is_a_game(api):
    """c-2-5: POST /api/games/score rejects a body whose rolls is not an array of
    numbers with 400 and the JSON body {"error": "rolls must be an array of
    numbers"}, rejects a request whose body is not valid JSON with that same 400
    body, and returns 200 with frames [] and total 0 for an empty rolls array.

    All three halves the criterion words, in the one test the criterion is.

    The rejected bodies are four: `rolls` absent, `rolls` a string, `rolls` an
    array holding a non-number, and a body that is not JSON at all. spec.md's
    endpoint section covers the first three with "`rolls` is absent, or is not an
    array of numbers" and the fourth with "The body is absent, empty, or not
    valid JSON: treated the same as an absent `rolls`". Each is compared as a
    whole body equality, not a substring, so an extra key or a reworded message
    fails.

    The empty-array half is what ties this criterion to `cut-game-total`:
    `gameTotal([])` is 0 while the declared fallback is -1, so 0 here is not a
    value an unwritten block produces.
    """
    bad_bodies = [
        ({}, "rolls absent"),
        ({"rolls": "1,2,3"}, "rolls is a string"),
        ({"rolls": [1, 4, "seven"]}, "rolls holds a non-number"),
    ]
    for payload, what in bad_bodies:
        response = post_score(api, json=payload)
        assert response.status_code == 400, (
            f"{what}: answered {response.status_code}, expected 400 "
            f"({response.text[:200]})"
        )
        assert response.json() == ERROR_BODY, (
            f"{what}: body is {response.json()!r}, expected {ERROR_BODY!r}"
        )

    unparseable = post_score(
        api,
        content="{this is not json",
        headers={"Content-Type": "application/json"},
    )
    assert unparseable.status_code == 400, (
        f"an unparseable body answered {unparseable.status_code}, expected 400 "
        f"({unparseable.text[:200]})"
    )
    assert unparseable.json() == ERROR_BODY, (
        f"an unparseable body returned {unparseable.json()!r}, expected {ERROR_BODY!r}"
    )

    empty = score_ok(api, [])
    assert empty["frames"] == [], (
        f"an empty game scored {empty['frames']!r}, expected []"
    )
    assert empty["total"] == EMPTY_GAME_TOTAL, (
        f"an empty game totalled {empty['total']!r}, expected {EMPTY_GAME_TOTAL}"
    )
