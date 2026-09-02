"""sc-game at `/games/[id]` - the frame grid, the roll symbols, the total.

One test per criterion, asserting only it. This screen is a server component
(spec.md, Screens: it "reads the seed through `lib/store.ts` directly rather
than fetching `/api/games`"), so the route's HTTP status is part of what a
criterion can read: every test navigates through `open_game`, which hands back
the main response.

ambiguity.md B3 records two readings of the unknown-id case - a `notFound()`
throw with the message in `not-found.tsx`, or the page rendering the message
itself and answering 200. c-1-6 pins *both* the 404 and the exact text, so this
suite asserts both, as the criterion words it. Which file renders it is the
Builder's to decide; the suite reads the route.

ambiguity.md A2 records two readings of where session 2's score cells get their
numbers - `scoreGame(game.rolls)` in process, or a fetch of
`/api/games/score`. Nothing in this suite depends on the answer: c-2-6 reads
the rendered text and nothing else, so either shape satisfies it and the choice
stays the Builder's.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    MIXED_FRAME_TEXTS,
    PARTIAL_EMPTY_CELLS,
    PARTIAL_TOTAL_TEXT,
    PERFECT_FRAME_10_TEXT,
    PERFECT_FRAME_IDS,
    UNKNOWN_GAME_ID,
    UNKNOWN_GAME_TEXT,
    by_testid,
    data_testids,
    frame_boxes,
    open_game,
    text_of,
)


def test_c_1_4_perfect_game_draws_ten_boxes_and_three_strikes_in_the_tenth(page):
    """c-1-4: /games/g-perfect renders 10 elements with data-testid frame-1
    through frame-10 and displays the exact text 'X X X' in the element with
    data-testid frame-10.

    The family is enumerated on the `frame-` prefix, which is the prefix of no
    other data-testid in the spec (`total-*`, `game-total` and `no-game` all
    fail it), and the ids are compared as one whole ordered list - so nine boxes
    fails, eleven fails, and frame-1..frame-10 arriving out of order fails.

    Neither value is one an unwritten block produces: with `cut-frames-scan`
    open `frames()` returns the declared empty array and no box renders at all,
    and with only `cut-frames-tenth` open there are nine boxes and no frame-10.
    'X X X' is also the only three-symbol frame in the seed, so it grades the
    tenth frame's three-roll rule rather than the pair rule.
    """
    open_game(page, "g-perfect")

    boxes = frame_boxes(page)
    expect(boxes).to_have_count(len(PERFECT_FRAME_IDS), timeout=LOAD_TIMEOUT)
    assert data_testids(boxes) == PERFECT_FRAME_IDS, (
        f"/games/g-perfect renders {data_testids(boxes)} in document order, "
        f"expected {PERFECT_FRAME_IDS}"
    )

    tenth = by_testid(page, "frame-10")
    expect(tenth).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(tenth) == PERFECT_FRAME_10_TEXT, (
        f"frame-10 reads {text_of(tenth)!r}, expected {PERFECT_FRAME_10_TEXT!r}"
    )


def test_c_1_5_mixed_game_boxes_read_digits_a_spare_a_strike_and_a_bonus(page):
    """c-1-5: /games/g-mixed displays the exact text '1 4' in the element with
    data-testid frame-1, '6 /' in frame-3, 'X' in frame-5 and '2 / 6' in
    frame-10.

    Four boxes, four different symbol rules from spec.md's roll-symbol block:
    two plain digits, a spare on the second roll of a pair that adds to 10, a
    lone strike, and the tenth frame's spare plus its bonus roll. None of the
    four is a value an unwritten block produces - an open `cut-frames-scan`
    renders no boxes and an open `cut-frames-tenth` renders no frame-10 - and no
    two of the four are the same string, so a `symbols` map that collapses two
    rules together fails on at least one.
    """
    open_game(page, "g-mixed")

    for number, expected in MIXED_FRAME_TEXTS.items():
        box = by_testid(page, f"frame-{number}")
        expect(box).to_have_count(1, timeout=LOAD_TIMEOUT)
        assert text_of(box) == expected, (
            f"frame-{number} on /games/g-mixed reads {text_of(box)!r}, "
            f"expected {expected!r}"
        )


def test_c_1_6_an_unknown_game_id_is_a_404_carrying_the_id_in_its_message(page):
    """c-1-6: /games/no-such-game responds 404 and displays the exact text
    'No game with id no-such-game'.

    Both halves are asserted because the criterion pins both. The message is
    read through the `no-game` data-testid, which spec.md's Screens table gives
    the not-found element, and compared by equality - so a generic 404 page, or
    a message that drops the id, fails.

    ambiguity.md B3: App Router puts the status and an id-bearing message in two
    different files, so this is the one session-1 criterion that is shipped
    written *and* has to be green on the skeleton. This test reads the route's
    own response and the rendered text, and says nothing about which file
    produced either.
    """
    response = open_game(page, UNKNOWN_GAME_ID)
    assert response is not None and response.status == 404, (
        f"/games/{UNKNOWN_GAME_ID} answered "
        f"{response.status if response else 'no response'}, expected 404"
    )

    message = by_testid(page, "no-game")
    expect(message).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(message) == UNKNOWN_GAME_TEXT, (
        f"no-game reads {text_of(message)!r}, expected {UNKNOWN_GAME_TEXT!r}"
    )


def test_c_2_6_partial_game_shows_a_total_of_34_with_its_last_two_cells_blank(page):
    """c-2-6: /games/g-partial displays the exact text '34' in the element with
    data-testid game-total and leaves the elements with data-testid total-5 and
    total-6 empty.

    This is the only criterion that drives all three session-2 cuts through the
    page. Each of the two empty cells is asserted to *exist* first and to be
    blank second, so "no score cells rendered at all" fails rather than passing
    by absence - spec.md's Screens section pins one score cell per entry
    `frames()` returned, so g-partial renders six.

    '34' is the assertion that cannot be satisfied by an unwritten block:
    spec.md fixes `cut-game-total`'s fallback at -1, an open
    `cut-score-lookahead` leaves every frame null so the total falls to that
    fallback, and an open `cut-pending-frame` renders a number (or `NaN`) into
    total-5 and total-6 instead of leaving them blank. The blank halves on their
    own would be green on a fully open skeleton, which is why they are asserted
    beside the total and not alone.

    ambiguity.md A1 is the finding this test cannot close, and it is blocking
    and owned by nothing. No criterion in spec.json asserts a *number* in any
    `total-k` element: c-2-6 reads `game-total` and two empty cells, and c-2-1
    to c-2-5 are all POSTs. So the cumulative-score column - which the Outcome
    names as a deliverable and which ships as written markup rather than a cut -
    is graded nowhere, and a page rendering every score cell empty passes all
    twelve criteria. spec.md's Screens table does state what those cells hold
    ("the cumulative score as a decimal string"), and g-partial's derived
    scores are 7, 16, 25 and 34, so the fix is one clause on c-2-6. Adding it
    here would be this suite inventing a criterion, so the assertion stops
    where the criterion stops and the gap is reported at Gate 1.
    """
    open_game(page, "g-partial")

    total = by_testid(page, "game-total")
    expect(total).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(total) == PARTIAL_TOTAL_TEXT, (
        f"game-total on /games/g-partial reads {text_of(total)!r}, "
        f"expected {PARTIAL_TOTAL_TEXT!r}"
    )

    # total-5 and total-6 are the last two of g-partial's six frames, the two
    # spec.md's derived-values table gives a null score.
    for testid in PARTIAL_EMPTY_CELLS:
        cell = by_testid(page, testid)
        expect(cell).to_have_count(1, timeout=LOAD_TIMEOUT)
        assert text_of(cell) == "", (
            f"{testid} on /games/g-partial reads {text_of(cell)!r}, "
            f"expected it to be empty"
        )
