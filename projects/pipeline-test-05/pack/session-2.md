# Session 2 - Dispatch and the trace

**Time:** the plan below runs to **48 minutes** against a 40-minute cap. That is
an overrun of eight. The trim list at the bottom gets it to **40.5 without
dropping anything graded** - read that section before you teach this, because
this session needs its trims and session 1 did not.

**Students start from:** their finished `lib/step.ts` from session 1. The car
moves, lands, opens its doors and serves whoever is waiting - but only ever
towards the floor `manualStart` handed it. `POST /api/scenarios/simulate` already
exists and already answers: 400 with one message for a bad body (c-2-5 is
green), and 200 with `{"rows":[],"served":[],"complete":false}` for a good one,
because the fold is empty.

**Students end with:** the same endpoint answering a full trace - nine rows for
`both-sides`, ten for `overtake`, one for `quiet` - naming the car's floor, mode
and direction at every tick and the tick each caller got in. c-2-1, c-2-2, c-2-3,
c-2-4 and c-2-6 green, so all twelve criteria in the project pass.

## What they learn

1. **A policy written down as one ordered procedure.** "Serve calls in passing
   order" has at least three readings. Four numbered rules, first match wins, and
   there is exactly one legal trace per scenario. This is the point of the
   session and it is worth naming as a skill: an arguable rule becomes a testable
   one only when somebody writes down the order.
2. **Sorting by a derived key with a tie-break.** Distance from the car, closest
   first, and on a tie the lower floor - which is one comparator with an `||` in
   it.
3. **Folding a transition into a bounded trace.** Dispatch, record, step,
   repeat. The loop's bound is part of the specification, not a safety net: it is
   what makes the run provably finite instead of hopefully finite.
4. **Two exits from one loop**, and they answer different things: `complete`
   true when there is nothing left to do, `complete` false when the bound ran
   out.

## Before you start

- Every student's session-1 work is finished and `/scenarios/above` serves floor
  6 at tick 4. A student whose `step` is wrong cannot pass anything today except
  c-2-5 - `mutation.json` records that removing either session-1 cut turns
  c-2-1, c-2-2 and c-2-3 red on its own. Fix that first or pair them up.
- Have open: `lib/dispatch.ts`, `lib/run.ts`, `data/scenarios.json`, and
  `app/api/scenarios/simulate/route.ts` for the ninety seconds you read it.
- Have the browser on `/scenarios/both-sides` with the **devtools console open**.
  You will type one `fetch` into it, and it is the only place the trace is
  visible - there is no trace screen in this project.
- Have the four policy rules where the room can see them for the whole session.
  A whiteboard is enough. You will point at them six or seven times.

## The plan

| Minutes | What you do |
|---|---|
| 0-3 | Recap in one line: `step` moves the car, and nothing in the project decides where. On `/scenarios/both-sides`, press step three times - the car goes up to floor 6, serves it, and then sits there for ever with a caller still waiting on floor 2. That waiting caller is today. |
| 3-8 | The four rules on the board, in order, first match wins. Then read `nextTarget`'s shipped head off the screen: rules 1 and 2 are already there, as two early returns. Point out that rule 2 is what picks up a caller on the floor the car is standing on - the thing session 1's page could not do. Their job is rules 3 and 4, plus the fold in `run.ts`. |
| 8-17 | Live: **`cut-calls-ahead`**. The three cases of `dir`, then the comparator with the tie-break. |
| 17-26 | Live: **`cut-dispatch-target`**. `ahead[0]`, the fallback, and the direction rule. |
| 26-38 | Live: **`cut-run-until`**. The bound at the top, dispatch, the row, the completion exit, then `step`. |
| 38-45 | Students catch up. Circulate. The symptoms under **Where students get stuck** are the ones you will actually see, in roughly that order. |
| 45-48 | The payoff. Paste the `fetch` into the console on `both-sides` and read the nine rows out loud against the four rules on the board. Then `overtake`, and stop on the tick-5 row: the car is above the caller and going down. That is the policy arguing its case. |

## The code they are handed, and that you read on screen

`nextTarget`'s shipped head - rules 1 and 2, and the `dir` line their first cut
depends on:

```ts
export function nextTarget(state: SimState): Car {
  const live = state.pending.filter((call) => call.tick <= state.tick)
  if (live.length === 0) return { mode: 'idle', floor: state.car.floor }
  if (live.some((call) => call.floor === state.car.floor)) return { mode: 'doors', floor: state.car.floor }

  const dir: Direction | null = state.car.mode === 'moving' ? state.car.direction : null

  let ahead: Call[] = []
```

Read it in this order and say what each line decides:

- `live` is the calls that have actually been made by now. A call registered for
  a future tick **does not exist yet**. This is a filter, so it keeps the seed's
  array order - which matters more than it looks, and is why the seed file must
  not be tidied.
- Nothing live at all: the car is idle where it stands. Rule 1, and it is one of
  the two ways the run ends.
- Somebody live on this floor: the doors open here. Rule 2. This is what makes
  `passing` work - a call registered at tick 2 for the floor the car is standing
  on at tick 2 is a pickup, not a skip.
- `dir` is the car's own direction when it is moving, and `null` when it is not.
  A car with the doors open, or an idle car, is committed to nothing.

The other seed, `lib/state.ts` - the one the fold starts from:

```ts
export function seed(scenario: Scenario): SimState {
  return {
    tick: 0,
    car: { mode: 'idle', floor: scenario.start },
    pending: scenario.calls.map((call) => ({ floor: call.floor, tick: call.tick })),
    served: [],
  }
}
```

Say why there are two seeds: `runUntil` starts from an **idle** car so that
every dispatch decision in the trace comes from `nextTarget`. Session 1's page
started from a moving car with a target already chosen, which was the only way to
have a working page before the dispatcher existed.

The endpoint, which ships written. Ninety seconds, no more - the point is that
it does nothing but validate and delegate:

```ts
const ERROR_BODY = { error: 'scenario must carry floors, start and calls' }
const DEFAULT_MAX_TICKS = 100
```

```ts
export async function POST(request: Request): Promise<Response> {
  let raw: unknown
  try {
    raw = await request.json()
  } catch {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  if (typeof raw !== 'object' || raw === null) {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const envelope = raw as { scenario?: unknown; maxTicks?: unknown }
  if (!isScenarioBody(envelope.scenario)) {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const body = envelope.scenario
  const scenario: Scenario = {
    id: body.id ?? '',
    name: body.name ?? '',
    floors: body.floors,
    start: body.start,
    calls: body.calls,
  }
  const maxTicks =
    typeof envelope.maxTicks === 'number' && Number.isFinite(envelope.maxTicks)
      ? envelope.maxTicks
      : DEFAULT_MAX_TICKS

  return Response.json(runUntil(scenario, maxTicks))
}
```

Two things to say about it. The body is an **envelope**: `{ scenario, maxTicks? }`
and not the scenario itself - which is the mistake to expect the moment anyone
hand-tests it. And `maxTicks` defaults to 100, which is more than any seeded
scenario needs, so a run that stops short of 100 stopped because it finished.

## Cut points in this session

### cut-calls-ahead - `lib/dispatch.ts:34`

**What students see** (the skeleton, exactly - and note that `ahead` is declared
above the `TODO`, so they assign to it, they do not declare it):

```ts
  let ahead: Call[] = []
  // TODO(cut-calls-ahead): Put into `ahead` every call in `live` the car reaches without turning round: floors above `state.car.floor` for a `dir` of `'up'`, floors below it for a `dir` of `'down'`, and all of `live` for a `dir` of `null`. Order them by distance from the car, closest first, a tie taken by the lower floor.
```

**What they write.** One `filter` over `live` with three cases on `dir` -
`'up'` keeps floors above the car, `'down'` keeps floors below it, `null` keeps
everything - then one `sort` whose comparator is the difference of the two
absolute distances from the car, falling back to the difference of the floors.
Ten lines.

**Teach it like this.** "'Ahead' means: can I get there without turning round?
If I am going up, ahead is upstairs. If I am going down, ahead is downstairs. If
I am standing still, everything is ahead of me."

Then the comparator, and this is the minute of the session that decides c-2-1.
Two things:

- **Distance, not floor number.** `Math.abs(call.floor - state.car.floor)` is
  the key. Sorting by `floor` puts floor 2 before floor 6 whichever way the car
  is going, which happens to be right on `both-sides` and wrong on a car heading
  down from floor 8.
- **The tie-break is not decoration.** On `both-sides` the car starts on floor 4
  and floors 2 and 6 are *both* two floors away. `|| a.floor - b.floor` is what
  chooses floor 2, and c-2-1 pins the consequence: floor 2 served at tick 2,
  floor 6 at tick 7. Break the tie the other way and you get the same two ticks
  on the other two floors - the values swap, and c-2-1 is red.

Say plainly why `overtake` exists, because it is the only reason this cut is a
cut: it is the one scenario where "the nearest call ahead" and "the nearest call
anywhere" disagree. At tick 2 the car is on floor 6 heading up, the floor-5
caller has just become live one floor *behind* it, and floor 8 is two floors
ahead. Without the direction filter the car turns round for the nearer call. With
it, the car finishes its journey up and comes back. Both are defensible lift
policies. The spec picked one, so it can be graded.

**Reference solution** - your copy, from `app/lib/dispatch.ts`:

```ts
  ahead = live
    .filter((call) => {
      if (dir === 'up') return call.floor > state.car.floor
      if (dir === 'down') return call.floor < state.car.floor
      return true
    })
    .sort(
      (a, b) =>
        Math.abs(a.floor - state.car.floor) - Math.abs(b.floor - state.car.floor) || a.floor - b.floor,
    )
```

**Passes when:** c-2-2 goes green - `overtake`'s tick-2 row reading floor 6 with
`direction` `up`, and floor 5 served at tick 8 rather than tick 3. It is the only
criterion `spec.json` lists for this cut. It is not the only criterion the cut
affects: the *ordering* half is graded by c-2-1, because `both-sides` at tick 0
is the only state in any fixture where `ahead` holds two calls at once. (That
gap between what the spec says and what the suite does is `ambiguity.md` W3.)

### cut-dispatch-target - `lib/dispatch.ts:37`

**What students see** (the skeleton, exactly - `next` is declared with the idle
fallback above the `TODO`, and the single `return next` is below it):

```ts
  let next: Car = { mode: 'idle', floor: state.car.floor }
  // TODO(cut-dispatch-target): Set `next` to a `moving` car standing at `state.car.floor`, its `target` taken from `ahead[0].floor` and falling back to the floor in `live` closest to the car - the lower floor on a tie - when `ahead` is empty, and its `direction` set to `'up'` for a target above the car and `'down'` for one below it.

  return next
```

**What they write.** The target is `ahead[0].floor` when `ahead` has anything
in it, and otherwise the closest floor in `live` - the same distance-and-tie
ordering as the cut before, applied to all of `live`. Then `next` is a `moving`
car standing **where it already is**, with that `target`, and `direction` `'up'`
when the target is above the car and `'down'` when it is below. Thirteen lines.

**Teach it like this.** "This function does not move anything. It answers one
question - where is this car trying to get to, as of right now - and it is asked
again on every single tick. That is the whole reason a call made mid-journey
gets picked up in passing: nothing is committed."

Three points:

1. **`floor: state.car.floor`.** The car has not gone anywhere yet. Moving is
   `step`'s job and this is the only line in the session where the two get
   confused.
2. **`ahead[0]` is already the right answer** because the previous cut sorted
   it. If somebody asks why there is no `Math.min` here, that is why.
3. **`direction` compared against the car, not against `ahead`.** `'up'` when
   `target > state.car.floor`, else `'down'`. And be blunt about why this matters:
   `step` *moves on this field*. A car that always claims `'up'` does not merely
   mislabel a row - it climbs out of the top of the shaft. c-2-2's tick-5 row is
   the only place any criterion watches a downward car, and it is there for
   exactly this.

About the `ahead`-empty fallback: write it, and do not spend three minutes
justifying it. On all five fixtures it never executes - by the time rules 1 and 2
have not returned, a moving car is moving towards a live call that is still ahead
of it, and a car that is not moving has `dir === null`, for which `ahead` is all
of `live`. It is `ambiguity.md` W6, owned by nothing, and the honest line for the
room is: "this branch is what makes the expression total. On these five scenarios
you will never see it run." What you must not do is leave `ahead[0].floor`
unguarded - a wrong filter makes the branch reachable, and then it is a
`TypeError` in the server log rather than a red test.

**Reference solution** - your copy, from `app/lib/dispatch.ts`:

```ts
  const nearest = live
    .slice()
    .sort(
      (a, b) =>
        Math.abs(a.floor - state.car.floor) - Math.abs(b.floor - state.car.floor) || a.floor - b.floor,
    )
  const target = ahead.length > 0 ? ahead[0].floor : nearest[0].floor
  next = {
    mode: 'moving',
    floor: state.car.floor,
    direction: target > state.car.floor ? 'up' : 'down',
    target,
  }
```

**Passes when:** c-2-1, c-2-2 and c-2-3 all go green - but only together with
`cut-run-until`, because with the fold empty there are no rows to read. With this
cut left open and the fold written, the car idles for ever and all three are red.

### cut-run-until - `lib/run.ts:26`

**What students see** (the skeleton, exactly - the whole function is a
declaration, a `TODO` and a `return`):

```ts
export function runUntil(scenario: Scenario, maxTicks: number): Trace {
  let trace: Trace = { rows: [], served: [], complete: false }
  // TODO(cut-run-until): Fold the run from `seed(scenario)` into `trace`: on each tick give the state to `nextTarget`, append the row `{ tick, floor, mode, direction }` of that dispatched car to `trace.rows`, and carry the dispatched state on through `step`. A dispatched car that is `idle` with `pending` empty ends the run with its row appended and `trace.complete` true; reaching `maxTicks` rows ends it with `trace.complete` false. The `served` list of the last state is `trace.served`.
  return trace
}
```

**What they write.** A local state, starting at `seed(scenario)`. A `while` loop
whose condition is `trace.rows.length < maxTicks`. Inside: ask `nextTarget` for
the car, make a dispatched state that is the current state with that car,
push the row `{ tick, floor, mode, direction }` - `direction` taken from the car
when it is `moving` and `null` otherwise - record `served`, and if the dispatched
car is `idle` with nothing pending, set `complete` and break. Otherwise `step`
the dispatched state and go round. Eighteen lines, and it is the biggest block in
the project.

**Teach it like this.** Draw the tick on the board before typing anything:

> one tick = **ask** where we are going, **write down** what that looks like,
> **do** it.

Then: "the row is the *dispatched* car, not the car we arrived with. The row for
tick 0 of `both-sides` says `moving down` - the car has not moved yet, but it has
been told where it is going."

Five points, in this order. The order is the lesson.

1. **The bound is tested at the top.** `while (trace.rows.length < maxTicks)`.
   c-2-4 sends `maxTicks` 4 and pins exactly 4 rows: test it after pushing and
   you get 5. Say what the bound is for - this loop is the only unbounded thing
   in the project, and the spec makes its termination part of the contract rather
   than a hope.
2. **Dispatch, then record, then move.** Three lines in that order. Recording
   before dispatching gives a trace one tick behind itself.
3. **`direction` is `null` unless the car is `moving`.** The type says so:
   `TraceRow.direction` is `Direction | null`. c-2-6 pins `quiet`'s single row at
   `direction: null`, so a row that carries `'up'` on an `idle` car is red.
4. **The completion exit is two conditions.** `idle` **and** `pending` empty.
   `idle` alone is not enough: a car can be idle for a tick with somebody
   registered for a future tick, and the run must wait for them. Have them look
   at rule 1 on the board and see that `nextTarget` answers `idle` whenever
   nothing is *live* - which is not the same as nothing being *pending*.
5. **The final row is appended, then the loop stops.** `quiet` is one row, not
   zero, and c-2-6 pins it. So the break comes after the push.

The `served` bookkeeping is the one line nobody guesses. `trace.served` is the
last state's `served` list, and the state changes twice in a turn of the loop -
once at dispatch and once at `step` - so the reference records it in both places.
If a student's rows are perfect and `served` is empty, this is the line.

**Reference solution** - your copy, from `app/lib/run.ts`:

```ts
  let state: SimState = seed(scenario)
  while (trace.rows.length < maxTicks) {
    const car = nextTarget(state)
    const dispatched: SimState = { ...state, car }
    trace.rows.push({
      tick: dispatched.tick,
      floor: car.floor,
      mode: car.mode,
      direction: car.mode === 'moving' ? car.direction : null,
    })
    trace.served = dispatched.served
    if (car.mode === 'idle' && dispatched.pending.length === 0) {
      trace.complete = true
      break
    }
    state = step(dispatched)
    trace.served = state.served
  }
```

**Passes when:** c-2-1, c-2-2, c-2-3, c-2-4 and c-2-6 go green - all five of
today's graded criteria, and c-2-4 and c-2-6 are its alone. `maxTicks` stopping a
run short, and a scenario with no calls at all, are decided by this fold and by
nothing else.

## The payoff - where the trace is actually visible

There is no trace screen in this project. `spec.md` put one out of scope because
session 2 has no minutes for a second screen build, which is true - and it means
the last three minutes of the session are the only place the thing they built
becomes visible. `ambiguity.md` W11 is that gap, filed against this pack, so here
is the exact request. Do not improvise it live.

Stay on `/scenarios/both-sides` so the relative URL resolves, open the devtools
console, and paste:

```text
fetch('/api/scenarios/simulate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    scenario: {
      id: 'both-sides',
      name: 'Calls on either side',
      floors: 8,
      start: 4,
      calls: [{ floor: 6, tick: 0 }, { floor: 2, tick: 0 }],
    },
  }),
})
  .then((r) => r.json())
  .then((t) => {
    console.table(t.rows)
    console.table(t.served)
    console.log('complete:', t.complete, 'rows:', t.rows.length)
  })
```

`console.table` is what makes this worth doing - the rows come out as a grid that
looks like a lift shaft on its side. The nine rows must read:

| tick | floor | mode | direction |
|---|---|---|---|
| 0 | 4 | moving | down |
| 1 | 3 | moving | down |
| 2 | 2 | doors | null |
| 3 | 2 | moving | up |
| 4 | 3 | moving | up |
| 5 | 4 | moving | up |
| 6 | 5 | moving | up |
| 7 | 6 | doors | null |
| 8 | 6 | idle | null |

and `served` must name floor 2 at `servedAt` 2 and floor 6 at `servedAt` 7. Read
tick 0 out loud: **both callers pressed at tick 0, both are two floors away, and
the tie rule sent the car down.** That is one line of their comparator deciding
the whole shape of the trace.

Then change `id` to `overtake` and the body to
`start: 4, calls: [{ floor: 5, tick: 2 }, { floor: 8, tick: 0 }]`, and read the
ten rows:

| tick | floor | mode | direction |
|---|---|---|---|
| 0 | 4 | moving | up |
| 1 | 5 | moving | up |
| 2 | 6 | moving | up |
| 3 | 7 | moving | up |
| 4 | 8 | doors | null |
| 5 | 8 | moving | down |
| 6 | 7 | moving | down |
| 7 | 6 | moving | down |
| 8 | 5 | doors | null |
| 9 | 5 | idle | null |

`served`: floor 8 at `servedAt` 4, floor 5 at `calledAt` 2 and `servedAt` 8. Stop
on tick 2. The car is on floor 6 going up; the floor-5 caller pressed the button
one tick ago and is one floor behind. **The car does not turn round.** Ask the
room whether that is the right policy - somebody will say the floor-5 caller
waited six ticks when a car that turned round would have reached them at tick 3,
and they are right, and that is the argument the trace exists to make visible. The answer is not in the code. The code just makes the
argument checkable.

## Where students get stuck

- **"`rows` is empty and `complete` is false."** - `cut-run-until` is still
  open. This is the correct starting state of the endpoint, and it is also what
  you get from the two dispatch cuts alone, so say it before anyone concludes
  their comparator is broken.
- **"The request comes back 400 and the body is valid."** - They sent the
  scenario as the whole body. It goes inside an envelope:
  `{"scenario": { ... }}`. This is the single most common hand-testing error in
  the session and it has nothing to do with their code.
- **"400, and I did use `scenario`."** - A call names a floor outside 1 to
  `floors`, which is the other half of c-2-5's one predicate. Check the `calls`
  array against `floors: 8`.
- **"`floor 2 servedAt 7` and `floor 6 servedAt 2`."** - The tie is being broken
  the wrong way, or `ahead` is not being sorted at all and insertion order is
  deciding. The seed lists floor 6 first, on purpose, so the unsorted answer is
  visibly wrong here. - "Both callers are two floors away. Which one does your
  comparator return first, and why?"
- **"The tick-2 row on `overtake` says `down`."** - `ahead` has no direction
  filter - most often written as `ahead = live`. The car sees the nearer caller
  behind it and turns round. - "Read rule 3 off the board. Can the car reach
  floor 5 without turning round?"
- **"`TypeError: Cannot read properties of undefined (reading 'floor')`."** -
  `ahead[0]` on an empty `ahead`. The fallback branch is missing. It is
  unreachable when the filter is right, which is why this error is a message
  about the *filter*, not about the fallback: a `dir` case is inverted or the
  comparison is `>=` where it should be `>`.
- **"The car is on floor 9. Then floor 10."** - `direction` is a constant
  `'up'`. `step` moves on that field, so the car climbs out of the building. -
  "Compare the target to the floor you are standing on. Which way is it?"
- **"`rows` has 200 entries" / "the request never comes back."** - The loop's
  bound is not being tested, or the served calls are not leaving `pending`. Both
  give a run that cannot finish; with the bound in place you get exactly
  `maxTicks` rows and `complete` false, which is the diagnostic. Check
  `cut-step-doors` from session 1: a caller who boards without being removed from
  `pending` is picked up for ever.
- **"`maxTicks` 4 gives 5 rows."** - The bound is tested after the push. Move it
  to the `while` condition, where it decides whether the tick happens at all.
- **"`quiet` answers 0 rows."** - The completion check runs before the row is
  pushed. The final row is part of the trace: `quiet` is one row, `idle`, and
  `complete` true.
- **"`quiet` answers `complete` false."** - The exit tested only `pending`, or
  only `idle`, or the loop ended by running out of ticks rather than by
  completing. Both conditions, and `break` only when both hold.
- **"The `direction` on my doors rows says `up`."** - No `null` mapping.
  `TraceRow.direction` is `Direction | null` for exactly this, and c-2-6 pins it
  on `quiet`'s idle row.
- **"`rows` looks right and `served` is empty."** - `trace.served` was never
  assigned, or was read off `seed`, whose `served` is always `[]`. The state
  moves twice per turn of the loop; record it after both.
- **"TypeScript: Type 'string' is not assignable to type 'Direction'."** - The
  direction was built in a separate `let` that TypeScript widened to `string`.
  Put the ternary directly in the object literal, or annotate the local
  `Direction`.
- **"It passes but I used `Math.sign(car.target - car.floor)` in `step`."** - It
  really does pass all twelve criteria. `spec.md` forbids it and nothing enforces
  that, which is `ambiguity.md` W4. Argue it on the merits: `direction` is the
  field the simulation runs on, and if `step` recomputes it then the code they
  just wrote in `cut-dispatch-target` cannot be wrong - and code that cannot be
  wrong cannot be checked.

## Check before moving on

`python3 -m pipeline test pipeline-test-05 --target skeleton` on a finished
student tree reports 12 passed. In the room, without the harness: the console
`fetch` above returns 9 rows for `both-sides` with floor 2 at `servedAt` 2, and
10 rows for `overtake` whose tick-5 row reads floor 8 `direction` `down`.

If the tick-5 row reads `up`, the direction rule is wrong and the car is leaving
the shaft even though the served list may look plausible. That is the one to
check before signing anyone off.

## Timing - the overrun and what to trim

The plan above is **48 minutes**. `lint.json` says 36.5. Where the eleven and a
half minutes went:

| block | estimator | this plan |
|---|---|---|
| `cut-calls-ahead` | 6.0 | 9 |
| `cut-dispatch-target` | 7.7 | 9 |
| `cut-run-until` | 6.8 | 12 |

`cut-run-until` is the gap. Its hint is 74 words and states no conditional prose
at all, so the decision-count model reads it as an easy cut - and it is five
ordered rules in eighteen lines, three of which (the bound at the top, the row
before the step, the push before the break) are *ordering* rules that cost a
sentence each to explain and a red criterion each to get wrong.

Trim in this order and stop as soon as you are inside the cap. **None of the
first three removes anything a criterion grades.**

1. **Both comparators go on a slide, already written.** Explain the
   distance-then-tie shape once, left to right, instead of deriving it twice.
   Saves 3.
2. **Hand out the four policy rules printed** and read them in two minutes
   rather than five. They need to be visible all session anyway. Saves 3.
3. **Show `both-sides` in the console and skip `overtake`.** You lose the best
   two minutes of the session, so take this one last. Saves 1.5.

Those three give **40.5**. That is the plan to teach.

4. **If you must go further, `spec.md`'s drop candidate is `cut-calls-ahead`
   handed over written.** Saves 9. It costs c-2-2 - and it costs more than the
   spec admits, because the ordering half of that cut is what c-2-1 grades
   through the `both-sides` tie (`ambiguity.md` W3). You would be handing over
   the one cut that makes `overtake` a different scenario from every other one.
   Prefer trims 1 to 3.

**Do not move a cut into session 1 to relieve this session.** Session 1 carries
the whole project setup and already runs seven minutes over; the rule that the
setup session holds strictly fewer cuts than the others exists because of exactly
that trade.
