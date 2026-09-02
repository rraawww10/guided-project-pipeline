"""sc-game at `/games/[id]` - c-1-4, c-1-5, c-1-6, c-2-6.

One test per criterion, asserting only it. This screen is a server component
(spec.md, Screens: it "reads the seed through `lib/store.ts` directly rather
than fetching `/api/games`"), so the route's HTTP status is part of what a
criterion can read: every test navigates through `open_game`, which hands back
the main response.

ambiguity.md A3 records two readings of the unknown-id case - a `notFound()`
throw, which gives the 404 but loses the id from the message, or the page
rendering the interpolated message itself and answering 200. c-1-6 pins *both*
the 404 and the exact interpolated text, so this suite asserts both, as the
criterion words it. Which file renders it is the Builder's to decide; the suite
reads the route and the `no-game` element and says nothing about either. A3 is
blocking and owned by `test-runner`, so if the two halves really cannot both
hold, this is the test that says so at step 6.

ambiguity.md A2 records two readings of how session 2's numbers reach the page -
`scoreGame` walking the frames `frames(rolls)` returns, or `lib/score.ts`
carrying its own chunking scan. Nothing here depends on the answer: c-2-6 reads
rendered text and nothing else.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    MIXED_FRAME_TEXTS,
    PARTIAL_EMPTY_CELLS,
    PARTIAL_SCORE_CELL_TEXTS,
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
    two of the four are the same string, so a symbol table that collapses two
    rules together fails on at least one.

    ambiguity.md B4 (owner: nothing) is the gap this test stops short of: no
    criterion in spec.json pins the `-` symbol for a roll of 0, because c-1-4
    reads g-perfect's page, c-1-5 reads g-mixed's frames 1, 3, 5 and 10, and no
    criterion renders g-partial's or g-gutter's boxes. g-mixed frame 6 is [0,1]
    and would read '- 1', and the Breaker's suggested wording was to add it
    here. It is not in the criterion, so it is not asserted - adding it would be
    this suite writing a criterion the person at Gate 1 never approved.
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

    ambiguity.md A3 is the finding this test brings to a head, and it is
    blocking with `test-runner` as its owner. The App Router puts the status and
    an id-bearing message in two different places: a page that renders the
    interpolated text answers 200, and `notFound()` answers 404 but hands
    `not-found.tsx` no route params. c-1-6 is also declared "No cut: shipped
    written", so `cutter.expected_skeleton_results` requires it green on the
    skeleton as well. This test reads the route's own response and the rendered
    text and says nothing about which file produced either, which is as far as
    the spec pins it; if no shape satisfies both halves, the failure lands in
    the Builder/test-runner loop at step 6 rather than being decided here.
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


def test_c_2_6_partial_game_scores_four_cells_a_total_of_34_and_two_blanks(page):
    """c-2-6: /games/g-partial displays the exact text '7', '16', '25' and '34'
    in the elements with data-testid total-1 through total-4, the exact text
    '34' in the element with data-testid game-total, and leaves the elements
    with data-testid total-5 and total-6 empty.

    The only criterion that drives all three session-2 cuts through the page,
    and the only one that reads a score cell with a number in it. The populated
    column and the empty column are graded by this one test, so a page that
    renders every score cell empty fails, one that renders `null` fails, and one
    that renders each frame's own score instead of the running total fails -
    7, 16, 25, 34 are cumulative and g-partial's own frame scores are 7, 9, 9, 9.

    Nothing asserted here is a value an unwritten block produces: spec.md fixes
    `cut-game-total`'s fallback at -1 rather than 0, an open
    `cut-score-lookahead` leaves every frame score null so the four cells read 0
    or nothing at all, and an open `cut-pending-frame` renders a number (or
    `NaN`) into total-5 and total-6 instead of leaving them blank. Each of the
    two blank cells is asserted to *exist* first and to be blank second, so "no
    score cells rendered at all" fails rather than passing by absence - spec.md,
    Screens, pins one score cell per entry `frames()` returned, so g-partial
    renders six.

    ambiguity.md B6 (owner: test-runner) records two readings of "empty": no
    text at all, or a layout placeholder. **This test takes reading one,
    `textContent` collapsing to the empty string**, because that is what
    spec.md's Screens table words - a score cell holds "the cumulative score as
    a decimal string, or nothing when that frame's score is `null`" - and
    because the grading-integrity argument that `NaN` cannot hide on the page is
    exactly "`NaN` is not an empty cell". A placeholder character in an
    unscored cell fails this test at step 6, which is where B6 said the
    resolution would surface.
    """
    open_game(page, "g-partial")

    # total-1 .. total-4: g-partial's cumulative scores as decimal strings.
    for number, expected in PARTIAL_SCORE_CELL_TEXTS.items():
        cell = by_testid(page, f"total-{number}")
        expect(cell).to_have_count(1, timeout=LOAD_TIMEOUT)
        assert text_of(cell) == expected, (
            f"total-{number} on /games/g-partial reads {text_of(cell)!r}, "
            f"expected {expected!r}"
        )

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
