"""sc-game at `/games/[id]` - the frame grid, the roll symbols, the score column
and the message for an id that is not in the seed.

One test per criterion, asserting only what that criterion pins. This screen is
a server component, so nothing here waits on a client fetch: spec.md says it
"reads the seed through `lib/store.ts` directly rather than fetching
`/api/games`", and that session 2's score column "calls `scoreGame` and
`gameTotal` from `lib/score.ts` in process and never fetches
`/api/games/score`". A failure on this page is therefore a failure of the page,
not of a route another criterion already grades.

Every element is found by the `data-testid` spec.md's element table pins -
`frame-1..frame-10`, `total-1..total-10`, `game-total`, `no-game` - matched
exactly. No class name and no styling is read anywhere in this file.

Three things this file deliberately does not assert:

* **No HTTP status.** spec.md, Out of scope: "`/games/[id]` answers 200 for
  every id, including one that is not in the seed... c-1-6 therefore asserts the
  message and not a status." That scope question was decided in round 2;
  asserting a 404 here would grade a decision the spec made the other way.
* **Nothing about the score cells or `game-total` on the unknown-id page.**
  ambiguity.md's adjudicated round-3 B3 records that the spec does not say what
  they do there, and c-1-6 asserts only the message and the absence of
  `frame-1`. Guessing either way would be this suite inventing a requirement.
* **No frame count on a short game, and no assertion that `no-game` is absent
  on a valid game's page.** ambiguity.md B3 (round 4) says exactly this: the
  spec's rule "one frame box and one score cell per entry `frames()` returned"
  is stated in Screens and no criterion grades it, and it suggests extending
  c-2-6 to pin the absence of `frame-7`/`total-7`. c-2-6 as written does not say
  that, so this suite does not assert it - a padded ten-cell grid satisfies
  every criterion in `spec.json`. That is a finding for the person at Gate 1,
  not something the Test Writer closes by grading more than the criterion says.

The "scores not yet computed" state in `spec.json`'s `screens[sc-game].states`
gets no test on purpose: ambiguity.md's adjudicated round-3 B5 shows it is a
state of the *skeleton* with `lib/score.ts` unfilled, it cannot hold in the
finished app, and no criterion names it. A test for it would be red at step 6
against correct code.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    FRAME_SUFFIXES_TEN,
    LOAD_TIMEOUT,
    MIXED_FRAME_TEXTS,
    NO_GAME_ID,
    NO_GAME_TEXT,
    PARTIAL_EMPTY_CELLS,
    PARTIAL_GAME_TOTAL_TEXT,
    PARTIAL_TOTAL_TEXTS,
    PERFECT_FRAME_10_TEXT,
    by_testid,
    family,
    open_game,
    raw_text_of,
    suffixes,
    text_of,
)


def test_c_1_4_perfect_game_draws_ten_frame_boxes_ending_in_x_x_x(page):
    """c-1-4: /games/g-perfect renders 10 elements with data-testid frame-1
    through frame-10 and displays the exact text 'X X X' in the element with
    data-testid frame-10.

    The boxes are enumerated on the `frame-` prefix, which spec.md's element
    table leaves to the frame boxes alone, and the suffixes are compared as one
    ordered list ['1'..'10'] - so a grid of nine boxes, a grid of eleven, a grid
    numbered from 0 and a `frame-10` rendered before `frame-9` each fail.
    spec.json's element list pins the numbering as "frame-1 upwards", which is
    what makes the order part of the requirement rather than an extra.

    The tenth box is the three-roll tenth `[10,10,10]`, whose first two rolls
    add to 20 rather than 10, so no `/` appears and the text is three X glyphs
    joined by single spaces. Equality, not containment: 'X X X X' is not
    'X X X'. With either frame cut open the box does not exist at all, so no
    value an unwritten block produces reads this way.
    """
    open_game(page, "g-perfect")

    boxes = family(page, "frame-")
    expect(boxes).to_have_count(10, timeout=LOAD_TIMEOUT)
    found = suffixes(boxes, "frame-")
    assert found == FRAME_SUFFIXES_TEN, (
        f"frame boxes are {found} in document order, expected {FRAME_SUFFIXES_TEN}"
    )

    tenth = by_testid(page, "frame-10")
    expect(tenth).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(tenth) == PERFECT_FRAME_10_TEXT, (
        f"frame-10 reads {text_of(tenth)!r}, expected {PERFECT_FRAME_10_TEXT!r}"
    )


def test_c_1_5_mixed_game_boxes_read_their_roll_symbols(page):
    """c-1-5: /games/g-mixed displays the exact text '1 4' in the element with
    data-testid frame-1, '6 /' in frame-3, 'X' in frame-5, '- 1' in frame-6 and
    '2 / 6' in frame-10.

    Five boxes, one per symbol rule, each asserted by equality: two digits for
    an open frame; a `/` for the second roll of a spare in frame-3 (`[6,4]`); a
    lone `X` for the strike frame at 5, which holds one roll and not two; the
    `-` gutter glyph in frame-6 (`[0,1]`, which spec.md says "is what grades the
    `-` glyph for a gutter roll"); and the three-roll tenth `[2,8,6]`, where a
    spare `/` and a bonus digit share one box.

    All five use `==` rather than `in`, so '1 4 5' does not satisfy frame-1 and
    'X X' does not satisfy frame-5. Each box is required to exist before its
    text is read. None of the five is a value an unwritten block produces: with
    `cut-frames-scan` open there are no boxes at all, and with only
    `cut-frames-tenth` filled there is a single box holding the whole roll list.
    """
    open_game(page, "g-mixed")

    for number, expected in MIXED_FRAME_TEXTS.items():
        box = by_testid(page, f"frame-{number}")
        expect(box).to_have_count(1, timeout=LOAD_TIMEOUT)
        assert text_of(box) == expected, (
            f"frame-{number} reads {text_of(box)!r}, expected {expected!r}"
        )


def test_c_1_6_unknown_id_says_so_and_draws_no_grid(page):
    """c-1-6: /games/no-such-game displays the exact text 'No game with id
    no-such-game' in the element with data-testid no-game and renders no element
    with data-testid frame-1.

    The message is asserted by equality and carries the interpolated id, so a
    generic 'Not found' fails and so does a page that names a different id. The
    absence of the grid is asserted on `frame-1` by name - the element the
    criterion names - and it is read *after* the message has rendered, so the
    count of zero is taken on a settled page rather than on one that has not
    painted yet. Read in the other order, this half would be green against a
    blank page, which is the one thing a count of zero must not be.

    No status assertion, and nothing about the score cells or `game-total` - see
    this module's docstring.
    """
    open_game(page, NO_GAME_ID)

    message = by_testid(page, "no-game")
    expect(message).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(message) == NO_GAME_TEXT, (
        f"no-game reads {text_of(message)!r}, expected {NO_GAME_TEXT!r}"
    )

    expect(by_testid(page, "frame-1")).to_have_count(0, timeout=LOAD_TIMEOUT)


def test_c_2_6_partial_game_score_column_runs_out_into_two_empty_cells(page):
    """c-2-6: /games/g-partial displays the exact text '7', '16', '25' and '34'
    in the elements with data-testid total-1 through total-4, the exact text '34'
    in the element with data-testid game-total, and the elements with data-testid
    total-5 and total-6 contain no text at all.

    The populated column and the empty column in one test, which is what the
    criterion is and what spec.md's Grading integrity argument leans on twice:
    "a page that renders every score cell empty, or renders `null`, or renders
    `NaN`, or renders the frame's own score instead of the cumulative one, fails
    here." The four numbers are cumulative and not per-frame - the frames are
    [3,4], [7,2], [9,0], [8,1], whose own sums are 7, 9, 9, 9 - so 16, 25 and 34
    are only reachable by carrying the running total forward.

    The two pending cells are read with `raw_text_of`, which does not collapse
    whitespace, and are required to be exactly the empty string. spec.md: "It is
    not a placeholder character, not `&nbsp;`, not an em dash and not the `-`
    gutter glyph." Each is required to exist first, because an element that is
    absent is not an element holding no text.

    `game-total` reads '34' and not '300', '133', '-1' or the last array entry:
    the last two frames are `null`, so the total is the fourth frame's score.
    `-1` is `cut-game-total`'s declared fallback, so the number asserted here is
    not one an unwritten block produces - and neither is an empty cell, because
    with `cut-pending-frame` open those two cells hold `NaN` or a number. This
    is the only criterion that drives all three session-2 cuts through the page.
    """
    open_game(page, "g-partial")

    for number, expected in PARTIAL_TOTAL_TEXTS.items():
        cell = by_testid(page, f"total-{number}")
        expect(cell).to_have_count(1, timeout=LOAD_TIMEOUT)
        assert text_of(cell) == expected, (
            f"total-{number} reads {text_of(cell)!r}, expected {expected!r}"
        )

    game_total = by_testid(page, "game-total")
    expect(game_total).to_have_count(1, timeout=LOAD_TIMEOUT)
    assert text_of(game_total) == PARTIAL_GAME_TOTAL_TEXT, (
        f"game-total reads {text_of(game_total)!r}, "
        f"expected {PARTIAL_GAME_TOTAL_TEXT!r}"
    )

    for number in PARTIAL_EMPTY_CELLS:
        cell = by_testid(page, f"total-{number}")
        expect(cell).to_have_count(1, timeout=LOAD_TIMEOUT)
        assert raw_text_of(cell) == "", (
            f"total-{number} holds {raw_text_of(cell)!r}, expected no text at all"
        )
