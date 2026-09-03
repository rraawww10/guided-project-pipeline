"""ep-simulate at `POST /api/scenarios/simulate` - the dispatch policy, the fold
and the validation, over HTTP.

One test per criterion, asserting only what that criterion pins. Every expected
number is a literal in `helpers.py` or in the test below it, read off spec.md's
four pinned trace tables - "The Builder and the Verifier must produce the same
trace, so here they are in full. Every number in a session-2 criterion is read
off these tables."

**No test here re-derives a trace.** There is no distance comparison, no
tie-break, no direction rule and no tick loop anywhere in this file, so nothing
in this suite can agree with a broken `nextTarget` or a broken `runUntil` by
making the same mistake. The request body is the seed as a literal, built by
`helpers.scenario`, so a wrong `data/scenarios.json` fails c-1-1 and does not
silently move the answers here. That choice is ambiguity.md W2's second half -
the spec does not say where the body comes from - and `helpers.py`'s docstring
records the reading and what it costs.

Because the body is a literal, the `calls` order these tests send is the order
spec.md's seed table pins: `overtake` floor 5 (tick 2) before floor 8 (tick 0),
`both-sides` floor 6 before floor 2. That order is what makes a
`cut-calls-ahead` written as `ahead = live` fail rather than reproduce the
pinned traces, so it is load-bearing here and not cosmetic.

Four criteria send no `maxTicks` at all, which is also what grades spec.md's
"`maxTicks` defaults to 100 when the body omits it": at 100 all four of these
scenarios complete, and a route that defaulted to 0 or dropped the key would
answer no rows.

Per the spec's own note, these tests "deliberately do not assert a whole `rows`
array: one extra doors tick should fail one criterion, not all six." What each
one reads is the served tick per call, the row count, or one named row.
"""
from __future__ import annotations

from helpers import (
    ERROR_BODY,
    number,
    post_simulate,
    row_for,
    scenario,
    served_for,
    simulate,
)


def test_c_2_1_both_sides_runs_nine_ticks_serving_the_lower_call_first(api):
    """c-2-1: POST /api/scenarios/simulate returns 200 for the both-sides
    scenario with rows holding 9 entries and served naming floor 2 at servedAt 2
    and floor 6 at servedAt 7.

    `both-sides` starts on a distance tie - floors 2 and 6 are both two floors
    from the car at floor 4 - and the policy's tie rule takes the lower floor,
    so the car goes down first and floor 2 is served at tick 2 while floor 6
    waits until tick 7. A student who breaks the tie the other way serves floor
    6 at tick 2 and floor 2 at tick 7: the same two floors, the same two ticks,
    swapped. Reading each entry by its floor and asserting its own `servedAt` is
    what makes that swap fail; a test that only checked that the ticks 2 and 7
    appear somewhere would pass it. The seed lists floor 6 first, so insertion
    order and the tie rule give different answers here - which is what turns
    this criterion into a grade of the tie rule rather than a grade of the array.

    The row count is 9, asserted exactly, so an extra doors tick or a run that
    stops one row early fails here.

    Two cuts named in spec.json, and spec.md's leave-one-out table says neither
    alone satisfies this: with `cut-dispatch-target` open the car idles for ever
    and nothing is served, and with `cut-run-until` open `rows` is `[]` and
    `served` is `[]`. Neither answers 9 rows, and neither produces a `served`
    entry at all, so no value asserted here is one an unwritten block also
    produces.

    ambiguity.md W3 (worth a look, owner `nothing`) adds a third cut this test
    in fact holds and spec.json does not record: `both-sides` at tick 0 is the
    only state in any fixture where `ahead` holds two calls, so dropping the
    distance *ordering* half of `cut-calls-ahead` while keeping its direction
    filter moves this criterion's two `servedAt` values and moves nothing on
    `overtake`. Trimming this criterion on the strength of the spec's "graded by
    c-2-2 alone" sentence would leave the ordering rule ungraded.
    """
    trace = simulate(api, scenario("both-sides"))

    assert len(trace["rows"]) == 9, (
        f"both-sides answered {len(trace['rows'])} rows, expected 9: {trace['rows']}"
    )

    lower = served_for(trace, 2)
    assert number(lower["servedAt"], "floor 2 servedAt") == 2, (
        f"floor 2 was served at {lower['servedAt']!r}, expected 2 - the tie at "
        f"floor 4 is taken by the lower floor: {trace['served']}"
    )

    upper = served_for(trace, 6)
    assert number(upper["servedAt"], "floor 6 servedAt") == 7, (
        f"floor 6 was served at {upper['servedAt']!r}, expected 7: {trace['served']}"
    )


def test_c_2_2_overtake_carries_on_up_past_the_nearer_call_behind_it(api):
    """c-2-2: POST /api/scenarios/simulate returns 200 for the overtake scenario
    with served naming floor 8 at servedAt 4 and floor 5 at servedAt 8, the rows
    entry for tick 2 holding floor 6 with direction up, and the rows entry for
    tick 5 holding floor 8 with direction down.

    This is `cut-calls-ahead`'s fixture and the one where "the nearest call
    ahead" and "the nearest call anywhere" disagree. The floor-5 call arrives at
    tick 2, when the car is at floor 6 heading up - one floor *behind* it - so a
    policy that keeps to its direction carries on to floor 8, serves it at tick
    4, and comes back for floor 5 at tick 8. A policy that chases the closest
    caller turns round at tick 2 and serves floor 5 at tick 3 instead, which
    fails on floor 5's `servedAt` and on tick 2's row. The seed lists the
    floor-5 call first, so `ahead = live` - no filter, no ordering - targets
    floor 5 from floor 6 at tick 2 and the tick-2 row reads `down`: that is the
    reading the seed order exists to catch.

    Both named rows are looked up by their `tick` field rather than as `rows[n]`,
    and both fields the criterion names on each are asserted:

    * tick 2 - floor 6, `direction` exactly the string "up".
    * tick 5 - floor 8, `direction` exactly the string "down". This is the only
      downward-moving car any criterion in the spec observes, and it is what
      holds `cut-dispatch-target`'s direction rule to something: `direction:
      'up'` unconditionally fails here, and since `step` moves on
      `car.direction` such a car also leaves the shaft.

    `None` is not "up" and not "down", so a row that omits the direction fails
    either way.

    Three cuts, and no proper subset satisfies this. `cut-run-until` open leaves
    `rows` empty, so there is no tick-2 row; `cut-dispatch-target` open leaves
    the car idle for ever, so nothing is served; `cut-calls-ahead` open leaves
    `ahead` empty, which sends `cut-dispatch-target` down its reversing branch
    at tick 2 and serves floor 5 at tick 3.

    ambiguity.md W4 (worth a look, owner `nothing`) records what these rows do
    not separate: a `cut-step-move` that moves by `Math.sign(car.target -
    car.floor)` instead of by `car.direction` reproduces every value asserted
    here, tick-5 row included. The prohibition is stated in spec.md and no
    criterion grades the mechanism; grading it would need a fixture whose
    `direction` and `target` disagree, which the spec does not have.
    """
    trace = simulate(api, scenario("overtake"))

    top = served_for(trace, 8)
    assert number(top["servedAt"], "floor 8 servedAt") == 4, (
        f"floor 8 was served at {top['servedAt']!r}, expected 4: {trace['served']}"
    )

    behind = served_for(trace, 5)
    assert number(behind["servedAt"], "floor 5 servedAt") == 8, (
        f"floor 5 was served at {behind['servedAt']!r}, expected 8 - the car "
        f"finishes its climb before it comes back: {trace['served']}"
    )

    climbing = row_for(trace, 2)
    assert number(climbing["floor"], "tick 2 floor") == 6, (
        f"the tick 2 row is at floor {climbing['floor']!r}, expected 6: {climbing}"
    )
    assert climbing["direction"] == "up", (
        f"the tick 2 row has direction {climbing['direction']!r}, expected 'up' - "
        f"the call one floor behind does not turn the car round: {climbing}"
    )

    returning = row_for(trace, 5)
    assert number(returning["floor"], "tick 5 floor") == 8, (
        f"the tick 5 row is at floor {returning['floor']!r}, expected 8: {returning}"
    )
    assert returning["direction"] == "down", (
        f"the tick 5 row has direction {returning['direction']!r}, expected "
        f"'down' - the car reverses once nothing is pending ahead: {returning}"
    )


def test_c_2_3_passing_picks_up_the_call_on_the_floor_it_is_standing_on(api):
    """c-2-3: POST /api/scenarios/simulate returns 200 for the passing scenario
    with served naming floor 3 at calledAt 2 and servedAt 2, and floor 5 at
    servedAt 5.

    The floor-3 call is registered for tick 2, which is the tick the car is
    standing on floor 3, and the policy's rule 2 picks it up on that same tick
    rather than skipping it. So `calledAt` and `servedAt` are both 2 - the one
    entry in the whole spec where they are equal, and the reason this criterion
    pins `calledAt` as well as `servedAt`. An implementation that took
    `calledAt` from the current tick rather than "the call's own tick" would
    pass here and fail on floor 5, whose call is registered at tick 0 and served
    at tick 5; an implementation that served the passing call one tick late
    fails on `servedAt`.

    Floor 5 is the car's original target, delayed to tick 5 by the stop, so its
    `servedAt` also grades that the passing stop cost exactly one doors tick.

    Two cuts, and neither alone satisfies this: `cut-dispatch-target` open idles
    the car and serves nothing, `cut-run-until` open answers an empty `served`.
    A missing entry fails in `served_for`, so no assertion below reads a value
    an unwritten block produces.
    """
    trace = simulate(api, scenario("passing"))

    passing_call = served_for(trace, 3)
    assert number(passing_call["calledAt"], "floor 3 calledAt") == 2, (
        f"floor 3 has calledAt {passing_call['calledAt']!r}, expected 2 - the "
        f"call's own tick: {trace['served']}"
    )
    assert number(passing_call["servedAt"], "floor 3 servedAt") == 2, (
        f"floor 3 was served at {passing_call['servedAt']!r}, expected 2 - the "
        f"tick the car was already standing there: {trace['served']}"
    )

    target_call = served_for(trace, 5)
    assert number(target_call["servedAt"], "floor 5 servedAt") == 5, (
        f"floor 5 was served at {target_call['servedAt']!r}, expected 5: "
        f"{trace['served']}"
    )


def test_c_2_4_max_ticks_four_stops_both_sides_short_and_incomplete(api):
    """c-2-4: POST /api/scenarios/simulate returns 200 for the both-sides
    scenario sent with maxTicks 4 and answers with rows holding 4 entries and
    complete false.

    `both-sides` needs 9 rows to finish, so a bound of 4 stops it five rows
    short: the run has further to go and says so. The count is asserted exactly,
    so a run that appends the row it was about to stop on (5) or stops one early
    (3) fails, and `complete` is compared with `is False` rather than for
    falsiness, so a missing key arriving as `None` does not satisfy it.

    This is one of `cut-run-until`'s own two criteria - the `maxTicks` exit is
    decided by the fold and by nothing else. With the cut open `trace` is its
    declared fallback `{ rows: [], served: [], complete: false }`, whose
    `complete` is already false: that half of this test is green on an unwritten
    block, which is exactly why the row count is asserted too. Four rows is not
    a value the fallback produces.

    The 200 is asserted in `simulate`: a bound the run does not reach is not an
    error, it is an incomplete trace.

    Two things this test does not observe, both recorded in ambiguity.md as
    worth a look and owned by `nothing`. W9: a row that both completes the run
    and reaches `maxTicks` - a bound of 4 on a 9-row run is five rows short of
    the coincidence, and the criterion names no other bound. W5: a `maxTicks`
    that is not a positive integer, which the spec leaves unvalidated while
    claiming it "bounds the run either way"; c-2-5 sends three bad scenarios and
    no bad bound, so nothing in this suite sends `"soon"` either.
    """
    trace = simulate(api, scenario("both-sides"), max_ticks=4)

    assert len(trace["rows"]) == 4, (
        f"both-sides with maxTicks 4 answered {len(trace['rows'])} rows, "
        f"expected 4: {trace['rows']}"
    )
    assert trace["complete"] is False, (
        f"complete is {trace['complete']!r}, expected false - the run had five "
        f"more rows to go"
    )


def test_c_2_5_a_missing_scenario_a_bad_floor_and_bad_json_are_one_four_hundred(api):
    """c-2-5: POST /api/scenarios/simulate rejects a body carrying no scenario
    object with 400 and the JSON body {"error": "scenario must carry floors,
    start and calls"}, rejects a scenario whose call names a floor outside 1 to
    floors with that same 400 body, and rejects a body that is not valid JSON
    with that same 400 body.

    spec.md: validation "is exactly one predicate with one message", so all
    three shapes answer the same status and the same body. Each is asserted as a
    whole-body equality rather than a substring, so a route that adds a `detail`
    key or reworded the message fails, and none of them may answer 200 with a
    trace.

    The out-of-range call is sent twice, once at floor 9 and once at floor 0,
    because "outside 1 to `floors`" has two sides and the obvious half-written
    predicate - `floor > floors` - accepts floor 0. Both are single-call
    variations of a body that is otherwise valid, so what they grade is the
    range test and not the shape test.

    The unparseable body is sent as raw bytes with a JSON content type, which is
    the shape a route that calls `await request.json()` without a guard turns
    into a 500. spec.md puts it under the same predicate as the other two.

    This criterion declares no cuts - the validation ships written, and spec.md
    lists c-2-5 among the criteria that stay green on the all-open skeleton. It
    is still red before any code exists: with no route there is no 400 and no
    JSON body to read.
    """
    no_scenario = post_simulate(api, json={"maxTicks": 10})
    assert no_scenario.status_code == 400, (
        f"a body with no scenario answered {no_scenario.status_code}, "
        f"expected 400: {no_scenario.text[:400]}"
    )
    assert no_scenario.json() == ERROR_BODY, (
        f"a body with no scenario answered {no_scenario.json()!r}, "
        f"expected {ERROR_BODY!r}"
    )

    for bad_floor in (9, 0):
        body = scenario("both-sides")
        body["calls"][0]["floor"] = bad_floor
        response = post_simulate(api, json={"scenario": body})
        assert response.status_code == 400, (
            f"a call naming floor {bad_floor} of 8 answered "
            f"{response.status_code}, expected 400: {response.text[:400]}"
        )
        assert response.json() == ERROR_BODY, (
            f"a call naming floor {bad_floor} of 8 answered {response.json()!r}, "
            f"expected {ERROR_BODY!r}"
        )

    not_json = post_simulate(
        api,
        content=b'{"scenario": ',
        headers={"content-type": "application/json"},
    )
    assert not_json.status_code == 400, (
        f"an unparseable body answered {not_json.status_code}, expected 400: "
        f"{not_json.text[:400]}"
    )
    assert not_json.json() == ERROR_BODY, (
        f"an unparseable body answered {not_json.json()!r}, expected {ERROR_BODY!r}"
    )


def test_c_2_6_quiet_completes_in_one_idle_row_with_nothing_served(api):
    """c-2-6: POST /api/scenarios/simulate returns 200 for the quiet scenario
    with rows holding one entry of tick 0, floor 5, mode idle and direction
    null, served empty and complete true.

    `quiet` has no calls, so the policy's rule 1 answers an `idle` car on the
    first tick and the fold ends the run immediately with that row appended.
    All four fields of the single row are asserted, because this is the
    criterion that pins what a `TraceRow` looks like when there is nothing to
    do: `direction` is `None` and not the string "null", not "up" and not
    absent, and `mode` is exactly "idle".

    `tick` 0 and the empty `served` list are the two values an unwritten
    `cut-run-until` also produces - its fallback is `{ rows: [], served: [],
    complete: false }` - which is why the row count and `complete` are asserted
    as well: one row is not zero rows, and `complete` is compared with `is True`
    so a fallback that reports false fails and a truthy string does not pass.
    This is the other criterion `cut-run-until` owns alone: the empty run is
    decided by the fold and by nothing else.
    """
    trace = simulate(api, scenario("quiet"))

    assert len(trace["rows"]) == 1, (
        f"quiet answered {len(trace['rows'])} rows, expected 1: {trace['rows']}"
    )
    row = trace["rows"][0]
    assert number(row["tick"], "the only row's tick") == 0, (
        f"the only row is at tick {row['tick']!r}, expected 0: {row}"
    )
    assert number(row["floor"], "the only row's floor") == 5, (
        f"the only row is at floor {row['floor']!r}, expected 5 - quiet starts "
        f"there and never moves: {row}"
    )
    assert row["mode"] == "idle", (
        f"the only row has mode {row['mode']!r}, expected 'idle': {row}"
    )
    assert row["direction"] is None, (
        f"the only row has direction {row['direction']!r}, expected null: {row}"
    )

    assert trace["served"] == [], (
        f"served is {trace['served']!r}, expected empty - quiet has no calls"
    )
    assert trace["complete"] is True, (
        f"complete is {trace['complete']!r}, expected true - a run with nothing "
        f"pending is finished, not bounded"
    )
