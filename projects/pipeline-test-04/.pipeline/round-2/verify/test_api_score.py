"""ep-games-score: POST /api/games/score - c-2-1 .. c-2-5.

One test per criterion, asserting only what that criterion pins. Every expected
array is a literal from spec.md's derived-values table; nothing here scores a
game, so a broken `scoreGame` cannot be graded by its own arithmetic.

The handler is stateless - spec.md: "The handler does not read the store; it
scores whatever it is given" - so every test posts its own rolls, no test
depends on another having run, and nothing on disk changes.
"""
from __future__ import annotations

from helpers import (
    EMPTY_TOTAL,
    GUTTER_ROLLS,
    GUTTER_TOTAL,
    MIXED_ROLLS,
    MIXED_SCORES,
    PARTIAL_ROLLS,
    PARTIAL_SCORES,
    PARTIAL_TOTAL,
    PERFECT_ROLLS,
    PERFECT_SCORES,
    ROLLS_ERROR,
    post_raw,
    post_score,
)

# spec.md, Endpoints: "`rolls` is absent, or is not an array of numbers: 400".
# Four shapes of the same rejection: the key missing, a string, a bare number,
# and an array with one non-number in it. Each is still valid JSON with a valid
# `rolls` reading, which is deliberate - ambiguity.md B7 records that a body
# which is not JSON at all has no declared status (the endpoint declares only
# [200, 400]), so no test here sends one and invents an expectation.
BAD_BODIES = [
    ({}, "rolls absent"),
    ({"rolls": "10 10"}, "rolls is a string"),
    ({"rolls": 10}, "rolls is a number"),
    ({"rolls": [3, "4"]}, "rolls is an array with a string in it"),
]


def test_c_2_1_perfect_game_scores_thirty_a_frame_up_to_three_hundred(api):
    """c-2-1: POST /api/games/score returns 200 with frames equal to
    [30,60,90,120,150,180,210,240,270,300] for the 12 rolls of g-perfect.

    The whole cumulative array is compared, not the final 300, so a strike that
    reaches for the wrong two rolls fails here. This is the criterion that
    grades `cut-score-lookahead` on its own: spec.md declares the fallback as
    `frameScore = null` with the shipped accumulator adding 0, so an open block
    answers ten zeros, and ten zeros is not this array. spec.md also warns that
    g-perfect alone is satisfied by `30 * frame` - which is why c-2-2 and c-2-3
    pin two more arrays that it is not.
    """
    body = post_score(api, PERFECT_ROLLS)
    assert body["frames"] == PERFECT_SCORES, (
        f"frames for the 12 rolls of g-perfect are {body['frames']!r}, "
        f"expected {PERFECT_SCORES!r}"
    )


def test_c_2_2_mixed_game_scores_the_array_that_thirty_times_frame_cannot_fake(api):
    """c-2-2: POST /api/games/score returns frames equal to
    [5,14,29,49,60,61,77,97,117,133] for the 19 rolls of g-mixed.

    spec.md: "This is the array that `30 * frame` cannot fake and the one to
    read first when session 2 goes red." Ten different numbers, containing a
    strike reaching over two rolls (frames 5 and 9), four spares reaching over
    one (frames 3, 4, 7 and 8), two open frames and a spare in the tenth, so two
    errors that cancel cannot both hide. Ten zeros - what an open
    `cut-score-lookahead` answers - is not this array.
    """
    body = post_score(api, MIXED_ROLLS)
    assert body["frames"] == MIXED_SCORES, (
        f"frames for the 19 rolls of g-mixed are {body['frames']!r}, "
        f"expected {MIXED_SCORES!r}"
    )


def test_c_2_3_partial_game_leaves_its_last_two_frames_null(api):
    """c-2-3: POST /api/games/score returns frames equal to [7,16,25,34,null,null]
    for the 10 rolls of g-partial.

    JSON `null` decodes to Python `None`, and `None == 0` is False, so the
    comparison distinguishes "the bonus rolls do not exist yet" from a score of
    zero - which spec.md's Outcome calls the one thing this project exists to
    teach. The list is compared whole, so the four numbers, the six-frame length
    and the two nulls are one assertion: an open `cut-score-lookahead` gives
    zeros where 7, 16, 25 and 34 belong.

    What this test cannot prove, and spec.md now says so itself under Grading
    integrity: `cut-pending-frame` can be empty and this body still match byte
    for byte, because an unguarded lookahead past the end of `rolls` gives `NaN`
    and `JSON.stringify(NaN)` is `null`. No assertion available over HTTP can
    tell the two apart once the body is serialised, so this test asserts exactly
    what the criterion words, and c-2-4 (where `NaN` is not 34) and c-2-6 (where
    `NaN` is not an empty cell) are the two that catch that cut.
    """
    body = post_score(api, PARTIAL_ROLLS)
    assert body["frames"] == PARTIAL_SCORES, (
        f"frames for the 10 rolls of g-partial are {body['frames']!r}, "
        f"expected {PARTIAL_SCORES!r}"
    )


def test_c_2_4_total_is_the_last_scored_frame_for_partial_and_zero_for_gutter(api):
    """c-2-4: POST /api/games/score returns total 34 for the 10 rolls of
    g-partial and total 0 for the 20 rolls of g-gutter.

    Two inputs, one call each, because one fixture cannot tell "the last frame
    that has a score" from a constant: 34 is g-partial's fourth frame and not
    its last entry (the last two are null), and 0 is g-gutter's tenth. A
    `gameTotal` that returns the final array entry answers `null` for g-partial;
    one that returns the array's maximum answers 34 and 0 too, which is why
    c-2-5 also pins the empty game.

    Neither number is what an unwritten block produces. spec.md fixes the
    fallback at `let total = -1`, "**not** 0", precisely so g-gutter's 0 cannot
    pass on an empty skeleton.
    """
    partial = post_score(api, PARTIAL_ROLLS)
    assert partial["total"] == PARTIAL_TOTAL, (
        f"total for the 10 rolls of g-partial is {partial['total']!r}, "
        f"expected {PARTIAL_TOTAL}"
    )

    gutter = post_score(api, GUTTER_ROLLS)
    assert gutter["total"] == GUTTER_TOTAL, (
        f"total for the 20 rolls of g-gutter is {gutter['total']!r}, "
        f"expected {GUTTER_TOTAL}"
    )


def test_c_2_5_a_non_numeric_rolls_body_is_400_and_an_empty_game_is_a_legal_zero(api):
    """c-2-5: POST /api/games/score rejects a body whose rolls is not an array of
    numbers with 400 and the JSON body {"error": "rolls must be an array of
    numbers"}, and returns 200 with frames [] and total 0 for an empty rolls
    array.

    Four rejected shapes, each asserted on the status *and* the whole body by
    equality, so a 400 carrying a different message fails and so does a 200 that
    quietly scores nonsense. spec.md's Endpoints section lists "absent, or is
    not an array of numbers" as one rule, which is why the missing key and the
    three wrong types all read the same string.

    The empty game is the half tied to `cut-game-total`: `frames` is `[]` and
    `total` is 0, and spec.md's declared fallback is -1, so an open block fails
    on the total while the shipped 400 half stays green. The 0 asserted here is
    therefore not a value the unwritten block also produces.
    """
    for payload, what in BAD_BODIES:
        response = post_raw(api, payload)
        assert response.status_code == 400, (
            f"POST /api/games/score with {what} ({payload!r}) answered "
            f"{response.status_code}, expected 400: {response.text[:400]}"
        )
        assert response.json() == ROLLS_ERROR, (
            f"POST /api/games/score with {what} ({payload!r}) answered body "
            f"{response.json()!r}, expected {ROLLS_ERROR!r}"
        )

    empty = post_score(api, [])
    assert empty["frames"] == [], (
        f"frames for an empty rolls array are {empty['frames']!r}, expected []"
    )
    assert empty["total"] == EMPTY_TOTAL, (
        f"total for an empty rolls array is {empty['total']!r}, "
        f"expected {EMPTY_TOTAL}"
    )
