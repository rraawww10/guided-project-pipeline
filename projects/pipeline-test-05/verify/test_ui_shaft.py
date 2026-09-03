"""sc-shaft at `/scenarios/[id]` - the shaft, the car readouts, the served lines
and the message for an id that is not in the seed.

One test per criterion, asserting only what that criterion pins. Every element is
found by the `data-testid` spec.md's element table pins - `floor-1..floor-8`,
`car-floor`, `car-mode`, `tick`, `step-button`, `served-<floor>`,
`served-count`, `no-scenario` - matched exactly. No class name and no styling is
read anywhere in this file.

The page is stepped by hand from `manualStart`, not by `runUntil`: spec.md says
`manualStart` gives "a `moving` car at `scenario.start` aimed at `calls[0].floor`
with the direction that points at it, or an `idle` car for a scenario with no
calls", and that the step button's handler is "exactly `setState(step(state))`".
So the only thing these five criteria grade past the shipped markup is `step` -
`nextTarget` does not exist in session 1 and nothing on this page consults it.
That is why `/scenarios/passing` does *not* stop at floor 3 here (c-1-4) while
`passing` through the endpoint does (c-2-3): different seed, same `step`.

Session 1's criteria drive `above`, `passing` and `quiet` only, and the seed
order the spec now pins leaves all three unchanged: `above`'s `calls[0]` is
still floor 6 and `passing`'s is still floor 5. ambiguity.md W1 (worth a look,
owner `pack-writer`) is about `/scenarios/overtake`, whose `calls[0]` moved to a
tick-2 call and which now opens its doors on an empty landing when stepped by
hand. No criterion drives that route, so no test here does either - it is a demo
defect for the Pack Writer, not a grading one.

Presses are counted through `click_step`, which waits for the `tick` readout to
advance once per press - see its docstring for why that signal and not another.

Three things this file deliberately does not assert:

* **No HTTP status, on either page.** No criterion names one, and spec.md gives
  `/scenarios/[id]` a `no-scenario` message rather than a not-found status.
* **No document order for the shaft rows.** spec.json's element list says "one
  row per floor of the building, highest floor first" and spec.md says "floor 8
  at the top down to floor 1", but c-1-2 asks only that the eight elements are
  rendered. ambiguity.md W10 (worth a look, owner `nothing`) is exactly this gap
  and suggests adding "with `floor-8` appearing before `floor-1` in document
  order" to c-1-2. c-1-2 as written does not say it, so this suite does not
  grade it - an upside-down lift satisfies every criterion in `spec.json`. That
  is a finding for the person at Gate 1, not something the Test Writer closes by
  grading more than the criterion says.
* **Nothing about the shaft, the readouts or the served lines on the
  unknown-id page.** The spec does not say what they do there; c-1-2 asserts the
  message alone and so does this suite.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    FLOOR_TESTIDS,
    LOAD_TIMEOUT,
    NO_SCENARIO_ID,
    NO_SCENARIO_TEXT,
    by_testid,
    click_step,
    family,
    open_shaft,
    read_testid,
)


def test_c_1_2_above_draws_eight_floors_at_tick_zero_and_an_unknown_id_says_so(page):
    """c-1-2: /scenarios/above renders 8 elements with data-testid floor-1
    through floor-8, the exact text 2 in the element with data-testid car-floor
    and the exact text 0 in the element with data-testid tick; and
    /scenarios/no-such-lift displays the exact text No scenario with id
    no-such-lift in the element with data-testid no-scenario.

    The rows are counted twice over: the `floor-` family must hold exactly 8
    elements, so a ninth row fails, and each of `floor-1`..`floor-8` must exist
    exactly once, so a shaft that renders `floor-1` eight times fails too.
    Counting the family alone would accept the second; naming the eight alone
    would accept an extra `floor-9`.

    `car-floor` reads `2` - `above`'s `start` - and `tick` reads `0`, both by
    equality rather than containment, so "floor 2 of 8" does not satisfy
    `car-floor` and `10` does not satisfy `tick`. This is the seeded state of
    `manualStart` before anything is pressed, which is why this half of the
    criterion is read on a page that is never clicked.

    The message is asserted by equality and carries the interpolated id, so a
    generic "Not found" fails and so does a page that names a different id.

    This criterion declares no cuts - spec.md lists it among the criteria that
    "stay green on the all-open skeleton" - and it is still red before any code
    exists: there is no page, so there are no eight rows and no message.
    """
    open_shaft(page, "above")

    rows = family(page, "floor-")
    expect(rows).to_have_count(8, timeout=LOAD_TIMEOUT)
    for testid in FLOOR_TESTIDS:
        expect(by_testid(page, testid)).to_have_count(1, timeout=LOAD_TIMEOUT)

    car_floor = read_testid(page, "car-floor")
    assert car_floor == "2", f"car-floor reads {car_floor!r}, expected '2'"

    tick = read_testid(page, "tick")
    assert tick == "0", f"tick reads {tick!r}, expected '0'"

    open_shaft(page, NO_SCENARIO_ID)

    message = read_testid(page, "no-scenario")
    assert message == NO_SCENARIO_TEXT, (
        f"no-scenario reads {message!r}, expected {NO_SCENARIO_TEXT!r}"
    )


def test_c_1_3_above_opens_its_doors_on_floor_six_after_four_presses(page):
    """c-1-3: /scenarios/above displays the exact text 6 in the element with
    data-testid car-floor and the exact text doors in the element with
    data-testid car-mode after the element with data-testid step-button is
    clicked 4 times.

    `above` starts `moving` at floor 2 aimed at floor 6, so the four presses walk
    3, 4, 5, 6 and the fourth lands the car on its target - the tick that turns
    the car into `{ mode: 'doors', floor: car.target }`. Both halves are
    asserted by equality: `6` and not "6 of 8", `doors` and not "doors open".

    Neither value is one an unwritten block produces. `cut-step-move` open
    leaves `step`'s declared fallback - "tick forward, car unchanged" - so after
    four presses the car is still `moving` at floor 2: `car-floor` reads 2 and
    `car-mode` reads moving, and both assertions here are red. `cut-step-doors`
    contributes nothing to this criterion, which is why it declares only the one
    cut.

    The pair is what grades the *landing*: a block that always opens the doors
    reads `doors` here and fails c-1-4, and a block that never opens them reads
    `6` here after four presses only if it moved the car and then failed to
    stop, which this assertion catches on the mode.
    """
    open_shaft(page, "above")
    click_step(page, 4)

    car_floor = read_testid(page, "car-floor")
    assert car_floor == "6", (
        f"car-floor reads {car_floor!r} after 4 presses, expected '6'"
    )

    car_mode = read_testid(page, "car-mode")
    assert car_mode == "doors", (
        f"car-mode reads {car_mode!r} after 4 presses, expected 'doors'"
    )


def test_c_1_4_passing_car_is_still_moving_at_floor_three_after_two_presses(page):
    """c-1-4: /scenarios/passing displays the exact text 3 in the element with
    data-testid car-floor and the exact text moving in the element with
    data-testid car-mode after the element with data-testid step-button is
    clicked 2 times.

    `manualStart` aims the car at `calls[0].floor`, which for `passing` is floor
    5, so the car starts `moving` at floor 1 heading up and the two presses walk
    2, 3. Floor 3 is a called floor - `{floor: 3, tick: 2}` - and the car does
    **not** stop there, because spec.md says "at tick 2 the manual page has no
    dispatcher"; picking up a call in passing is `nextTarget`'s rule 2, built in
    session 2 and consulted only by `runUntil`. c-2-3 is the criterion that
    grades the other behaviour on the same scenario, through the endpoint.

    This is `cut-step-move`'s second fixture, and the floor is the half that
    discriminates: `moving` is also what the open cut's fallback leaves in
    `car-mode`, since the fallback changes nothing but the tick. `3` is not -
    the fallback leaves the car at floor 1 - so this test goes red on an
    unwritten block, and it goes red on a block that opens the doors whenever it
    passes a called floor, which is the error the criterion exists to catch.
    """
    open_shaft(page, "passing")
    click_step(page, 2)

    car_floor = read_testid(page, "car-floor")
    assert car_floor == "3", (
        f"car-floor reads {car_floor!r} after 2 presses, expected '3'"
    )

    car_mode = read_testid(page, "car-mode")
    assert car_mode == "moving", (
        f"car-mode reads {car_mode!r} after 2 presses, expected 'moving'"
    )


def test_c_1_5_above_serves_floor_six_at_tick_four_and_goes_idle(page):
    """c-1-5: /scenarios/above displays the exact text 4 in the element with
    data-testid served-6, the exact text 1 in the element with data-testid
    served-count and the exact text idle in the element with data-testid
    car-mode after the element with data-testid step-button is clicked 5 times.

    The fifth press is spent with the doors open at floor 6 on tick 4, so the
    call `{floor: 6, tick: 0}` joins `served` as `{floor: 6, calledAt: 0,
    servedAt: 4}` and the car becomes `{ mode: 'idle', floor: 6 }`.
    `served-6` holds "the tick that call was served", which is the `servedAt` 4
    and not the `calledAt` 0 and not the tick the page is now on, 5 - so the
    equality here separates all three.

    `served-6` is looked up by its exact testid, never as a `served-` prefix:
    `served-count` begins with those characters, and a prefix match would read
    the counter as a served line.

    This is the only criterion that drives both session-1 cuts, and spec.md's
    leave-one-out table says no proper subset satisfies it. Neither state
    produces a value asserted here: with `cut-step-move` open the car never
    leaves floor 2, so there is no `served-6` element at all and `served-count`
    reads 0; with `cut-step-doors` open the car reaches the doors on press 4 and
    then nothing is ever served, so `served-6` is still absent, `served-count`
    is still 0 and `car-mode` still reads doors. `served-count` is required to
    read 1 rather than "at least one", so an empty page cannot answer it.

    ambiguity.md W8 (worth a look, owner `nothing`) records what this test
    cannot separate: a `cut-step-doors` filled with the literal `served: [{floor:
    6, calledAt: 0, servedAt: 4}]` satisfies every assertion below, because all
    three numbers are printed in the criterion. The fixtures that do separate it
    are session 2's folds - c-2-1, c-2-2, c-2-3 and c-2-6 - and adding a second
    observation to this criterion is a spec change, not a test change.
    """
    open_shaft(page, "above")
    click_step(page, 5)

    served_six = read_testid(page, "served-6")
    assert served_six == "4", (
        f"served-6 reads {served_six!r} after 5 presses, expected '4'"
    )

    served_count = read_testid(page, "served-count")
    assert served_count == "1", (
        f"served-count reads {served_count!r} after 5 presses, expected '1'"
    )

    car_mode = read_testid(page, "car-mode")
    assert car_mode == "idle", (
        f"car-mode reads {car_mode!r} after 5 presses, expected 'idle'"
    )


def test_c_1_6_quiet_car_stays_idle_on_floor_five_with_nothing_served(page):
    """c-1-6: /scenarios/quiet displays the exact text idle in the element with
    data-testid car-mode, the exact text 5 in the element with data-testid
    car-floor and the exact text 0 in the element with data-testid served-count
    after the element with data-testid step-button is clicked 3 times.

    `quiet` has no calls, so `manualStart` gives an `idle` car at floor 5 and
    `step`'s third case - "nothing but the tick changes" - is the whole of what
    three presses do. spec.md ships that case written, "because it is exactly the
    declared fallback of `next`", and c-1-6 declares no cuts.

    All three values this criterion pins are also the page's seeded values, so
    the three presses are the only thing separating this test from one that
    reads an untouched page. That is why `click_step` waits for the `tick`
    readout to advance once per press: without observing the tick, this test
    would be green against a step button wired to nothing, which is the one
    thing it must not be. The tick is not asserted as a criterion value -
    ambiguity.md W10 suggests adding it to c-1-6 and that is a spec change for
    Gate 1 - but the presses are not counted as landed until it moves.

    `served-count` reads 0 here, which is a value an all-open skeleton also
    produces. It is asserted because the criterion pins it and because the
    reading it rules out is real: a car that moves or serves anything on a
    scenario with no calls at all fails on `car-floor` or on the count. The
    criteria that hold the doors transition to a non-zero answer are c-1-5 and
    session 2's four folds.
    """
    open_shaft(page, "quiet")
    click_step(page, 3)

    car_mode = read_testid(page, "car-mode")
    assert car_mode == "idle", (
        f"car-mode reads {car_mode!r} after 3 presses, expected 'idle'"
    )

    car_floor = read_testid(page, "car-floor")
    assert car_floor == "5", (
        f"car-floor reads {car_floor!r} after 3 presses, expected '5'"
    )

    served_count = read_testid(page, "served-count")
    assert served_count == "0", (
        f"served-count reads {served_count!r} after 3 presses, expected '0'"
    )
