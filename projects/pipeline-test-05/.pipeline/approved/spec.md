# Lift

A lift simulated one tick at a time. Two sessions of 40 minutes, Next.js (App
Router), React, TypeScript. Nothing reads a clock: tick 0 is the seed, tick *n*
is a fold of one pure `step`, and the same scenario gives the same trace forever.

## Outcome

Five seeded scenarios in an 8-floor building, each call given as
`{ floor, tick }`. A pure `step(state)` that advances exactly one tick. A
dispatch policy, `nextTarget(state)`, written down as one ordered procedure so
there is exactly one legal trace per scenario. And `runUntil(scenario, maxTicks)`
behind `POST /api/scenarios/simulate`, answering with the car's floor, mode and
direction at every tick plus the tick each caller got in.

At the end of session 1 the student opens `/scenarios/above`, presses the step
button, and watches the car climb one floor per tick and pick up the caller on
floor 6. At the end of session 2 the both-sides scenario runs to completion
through the endpoint and the trace names the tick every passenger got in.

## Out of scope

- More than one lift, and any coordination between cars.
- Destinations inside the car. Every call is a hall call naming a floor only.
- Capacity, weight, door obstruction, express floors, out-of-service states.
- Animation and real elapsed time. A tick is a tick, never a second.
- Choosing or editing the policy from the UI. The policy is code.
- A trace screen. The session-2 trace is JSON from `POST
  /api/scenarios/simulate`; rendering it would cost a second screen build that
  session 2 has no minutes for. Session 1's shaft page is the only screen.
- Persistence. Nothing is written at runtime, so there is no live store, and
  `app/.gitignore` needs no entry to keep one out of the skeleton.

## Data model

`lib/types.ts`, shipped written:

```ts
export type Direction = 'up' | 'down'
export type Call = { floor: number; tick: number }
export type Scenario = { id: string; name: string; floors: number; start: number; calls: Call[] }

export type Car =
  | { mode: 'moving'; floor: number; direction: Direction; target: number }
  | { mode: 'doors'; floor: number }
  | { mode: 'idle'; floor: number }

export type Served = { floor: number; calledAt: number; servedAt: number }
export type SimState = { tick: number; car: Car; pending: Call[]; served: Served[] }
export type TraceRow = { tick: number; floor: number; mode: Car['mode']; direction: Direction | null }
export type Trace = { rows: TraceRow[]; served: Served[]; complete: boolean }
```

The car's mode is a discriminated union rather than three booleans, so a car
cannot be moving and idle at once. `direction` on a `TraceRow` is `null` for
`doors` and `idle`.

### The seed - `data/scenarios.json`

All five scenarios use `floors: 8`, floors numbered 1 to 8. No scenario calls
the same floor twice, which is what makes the page's `served-<floor>` element
unique.

| id | name | start | calls, in this array order |
|---|---|---|---|
| `above` | One call above the car | 2 | `{floor: 6, tick: 0}` |
| `both-sides` | Calls on either side | 4 | `{floor: 6, tick: 0}`, `{floor: 2, tick: 0}` |
| `overtake` | A nearer call behind | 4 | `{floor: 5, tick: 2}`, `{floor: 8, tick: 0}` |
| `passing` | A call at the passing floor | 1 | `{floor: 5, tick: 0}`, `{floor: 3, tick: 2}` |
| `quiet` | No calls at all | 5 | none |

The idea asked for four scenarios. `overtake` is the fifth and it is not
decoration: it is the only fixture on which "the nearest call ahead" and "the
nearest call anywhere" disagree, so without it `cut-calls-ahead` cannot be told
apart from a car that always chases the closest caller.

**The `calls` column is deliberately not registration order.** `live` (below) is
a filter, so it preserves array order, and a student who writes `ahead = live` -
no direction filter and no ordering, which is the `dir === null` case of
`cut-calls-ahead`'s hint applied unconditionally - would otherwise reproduce
every pinned trace below byte for byte and be graded correct while holding the
opposite dispatch policy. So `overtake` lists its tick-2 floor-5 call *first*
and its tick-0 floor-8 call second, and `both-sides` lists floor 6 before floor
2. Every pinned trace below is unchanged for a correct implementation, while the
unfiltered, unordered reading now targets floor 5 from floor 6 at tick 2
(`c-2-2` red) and heads for floor 6 first from floor 4 in `both-sides`
(`c-2-1`'s two `servedAt` values swap, red).

`both-sides` is also a distance tie - floor 2 and floor 6 are both 2 floors from
floor 4 - and because the array now holds floor 6 first, insertion order and the
tie rule give *different* answers, so `c-2-1` grades the tie rule as well.

### One tick - `step(state)` in `lib/step.ts`

Total function. `tick` always advances by exactly one. The car's mode decides
the rest, and there are exactly three cases:

1. **`moving`** - the car advances one floor along `car.direction`: `'up'` adds
   one to `car.floor`, `'down'` takes one away. `car.target` decides only
   *where the doors open*, never which way the car travels - `step` must not
   derive its movement from `Math.sign(car.target - car.floor)`, because that
   makes `direction` a decorative field on the row instead of the value the
   simulation runs on. Landing on `car.target` makes the car
   `{ mode: 'doors', floor: car.target }`; stopping short leaves it `moving` at
   the new floor with the same `direction` and `target`. `pending` and `served`
   are untouched. This is `cut-step-move`.
2. **`doors`** - the tick is spent with the doors open. Every call in `pending`
   for `car.floor` whose `tick` is at or below `state.tick` moves into `served`
   as `{ floor, calledAt: the call's tick, servedAt: state.tick }` and leaves
   `pending`. The car becomes `{ mode: 'idle', floor: car.floor }`. This is
   `cut-step-doors`.
3. **`idle`** - nothing but the tick changes. Shipped written, because it is
   exactly the declared fallback of `next` (below), so the `idle` branch needs
   no code at all.

Re-dispatch is not `step`'s job. A car that has just closed its doors is
`idle`, and `nextTarget` sends it somewhere on the next tick.

Because movement follows `car.direction`, a `direction` set wrongly by
`cut-dispatch-target` runs the car the wrong way and the trace collapses - which
is what `c-2-2`'s tick-5 row grades.

### The policy - `nextTarget(state)` in `lib/dispatch.ts`

The policy is arguable, so it is written here as **one ordered procedure**, and
the first rule that applies wins. `runUntil` consults it once per tick, which is
what makes "serve calls in passing order" fall out: a call that arrives while
the car is in flight is considered again on the very next tick.

1. `live` is the calls in `state.pending` with `tick <= state.tick`, kept in the
   scenario's array order. A call registered for a future tick does not exist
   yet. With `live` empty the answer is `{ mode: 'idle', floor: car.floor }`.
   *Shipped written.*
2. With a call in `live` at `car.floor`, the answer is
   `{ mode: 'doors', floor: car.floor }`. *Shipped written.* This is the case
   that decides whether the policy is honest: a call registered at tick *t* for
   the floor the car is standing on at tick *t* is picked up at tick *t*, not
   skipped. `passing` is the fixture that proves it.
3. `dir` is `car.direction` for a `moving` car and `null` for a car with no
   direction. `ahead` is every call in `live` the car reaches without turning
   round - above `car.floor` for `'up'`, below it for `'down'`, all of `live`
   for `null` - ordered by distance from the car, closest first, a tie taken by
   the lower floor. This is `cut-calls-ahead`.
4. With `ahead` non-empty the car keeps going: `moving`, still standing at
   `car.floor`, `target` `ahead[0].floor`. With `ahead` empty it reverses:
   `target` is the floor in `live` closest to the car, again lower floor on a
   tie. `direction` is `'up'` for a target above the car and `'down'` for one
   below. This is `cut-dispatch-target`.

So: keep going while anything is pending ahead, take those calls in passing
order, reverse only when nothing is pending ahead, go idle when nothing is
pending at all.

### The run - `runUntil(scenario, maxTicks)` in `lib/run.ts`

Each tick: hand the state to `nextTarget`, append that dispatched car's row to
`trace.rows`, advance the dispatched state through `step`. The run ends
**complete** on a dispatched car that is `idle` with `pending` empty, with that
final row appended. It ends **incomplete** the moment `trace.rows` reaches
`maxTicks`. `trace.served` is the last state's `served`. This is
`cut-run-until`, and the `maxTicks` bound is what makes the loop provably
finite rather than hopefully finite.

### Two seeds, and why there are two

Both shipped written in `lib/state.ts`:

- `seed(scenario)` - tick 0, `{ mode: 'idle', floor: scenario.start }`,
  `pending` the scenario's calls, `served` empty. Used by `runUntil`, so that
  every dispatch decision in the trace comes from `nextTarget`.
- `manualStart(scenario)` - tick 0, a `moving` car at `scenario.start` aimed at
  `calls[0].floor` with the direction that points at it, or an `idle` car for a
  scenario with no calls. Used by the shaft page, so session 1 can step a car
  by hand with no dispatcher in existence yet.

`manualStart` reads `calls[0]` straight out of the data and computes no nearest
floor and no direction rule, so no part of session 2's policy is visible in
session 1's shipped code for a student to copy. Session 1's criteria drive only
`above`, `passing` and `quiet`; `both-sides` and `overtake` are session 2's
fixtures, and `manualStart` on either of them simply aims at whichever call the
array holds first.

### The pinned traces

The Builder and the Verifier must produce the same trace, so here they are in
full. Every number in a session-2 criterion is read off these tables.

`both-sides` through `runUntil`, 9 rows, `complete` true. At tick 0 the car is
idle at floor 4, both calls are live, and the tie between floor 6 and floor 2 is
taken by the lower floor - so the car goes down first even though the array
holds floor 6 first.

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

`served`: `{floor: 2, calledAt: 0, servedAt: 2}`, `{floor: 6, calledAt: 0, servedAt: 7}`.

`overtake`, 10 rows, `complete` true. The car is at floor 6 heading up on tick 2
when the floor-5 call becomes live one floor behind it; the policy carries on to
floor 8 first and comes back for it. Rows 5 to 7 are the only downward-moving
car in any pinned trace.

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

`served`: `{floor: 8, calledAt: 0, servedAt: 4}`, `{floor: 5, calledAt: 2, servedAt: 8}`.

`passing`, 7 rows, `complete` true. The floor-3 call arrives at tick 2, which is
the tick the car is standing on floor 3, and it is picked up at tick 2.

| tick | floor | mode | direction |
|---|---|---|---|
| 0 | 1 | moving | up |
| 1 | 2 | moving | up |
| 2 | 3 | doors | null |
| 3 | 3 | moving | up |
| 4 | 4 | moving | up |
| 5 | 5 | doors | null |
| 6 | 5 | idle | null |

`served`: `{floor: 3, calledAt: 2, servedAt: 2}`, `{floor: 5, calledAt: 0, servedAt: 5}`.

`quiet`, 1 row, `complete` true, `served` empty: tick 0, floor 5, mode `idle`,
direction `null`.

`above` is session 1's fixture and is stepped by hand from `manualStart`, not by
`runUntil`: the car starts `moving` at floor 2 aimed at floor 6, and five clicks
of the step button give floor 3, floor 4, floor 5, floor 6 with the doors open,
then `idle` at floor 6 with floor 6 served at tick 4.

## Endpoints

| id | method | path | answers |
|---|---|---|---|
| `ep-scenarios` | GET | `/api/scenarios` | 200 with the five seeded `Scenario` objects, in the order above |
| `ep-simulate` | POST | `/api/scenarios/simulate` | 200 with a `Trace`, or 400 with `{"error": "..."}` |

`ep-simulate` takes `{ scenario, maxTicks? }`. `maxTicks` defaults to 100 when
the body omits it, which is more than any seeded scenario needs, so the four
scenarios that run through it all complete.

Validation, shipped written, is exactly one predicate with one message. The
endpoint answers 400 with
`{"error": "scenario must carry floors, start and calls"}` when the body is not
valid JSON, when it carries no `scenario` object with numeric `floors` and
`start` and an array `calls`, or when a call names a floor outside 1 to `floors`.
Nothing else is validated: `start` is trusted, because no fixture sends a bad
one and `maxTicks` bounds the run either way.

## Screens

`sc-shaft` at `/scenarios/[id]`, built in session 1, a client component holding
one `SimState` in `useState` seeded from `manualStart`. The step button's
handler is shipped written and is exactly `setState(step(state))` - the learning
is inside `step`, not in the click.

| element | `data-testid` | holds |
|---|---|---|
| one row per floor, floor 8 at the top down to floor 1 | `floor-1` .. `floor-8` | the floor number |
| the car readout | `car-floor` | the car's floor number |
| the mode readout | `car-mode` | the exact text `moving`, `doors` or `idle` |
| the tick readout | `tick` | the tick number |
| the step button | `step-button` | - |
| one line per served call | `served-<floor>` | the tick that call was served |
| the served counter | `served-count` | how many calls have been served |
| the unknown-id message | `no-scenario` | the text `No scenario with id <id>` |

Every count and every string a criterion reads is pinned to a `data-testid`, so
styling cannot move a test. States: tick 0, car moving, doors open, no calls at
all, unknown scenario id.

The page reads its scenario from `GET /api/scenarios` and picks the matching
`id`. Both the screen and the endpoint it fetches are built in session 1, so
session 1's skeleton has nothing dangling.

## Sessions

### Session 1 - Setup, the shaft, and one tick

**Goal:** seed five scenarios, draw the shaft, and write the one-tick
transition so the car climbs a floor per tick and picks up the caller it stops
for.

**Teaches:** a discriminated union for the car's mode; one pure transition per
tick.

**Builds:** `ep-scenarios`, `sc-shaft`.

This session carries the project setup - the types, the seed file, the route and
the page - so it carries two cut points against session 2's three.

**Acceptance criteria**

- **c-1-1** - `GET /api/scenarios` returns 200 with a JSON array of 5 scenarios
  whose id values are `above`, `both-sides`, `overtake`, `passing` and `quiet`
  in that order, each carrying `id`, `name`, `floors`, `start` and `calls`.
- **c-1-2** - `/scenarios/above` renders 8 elements with `data-testid` `floor-1`
  through `floor-8`, the exact text `2` in `car-floor` and the exact text `0` in
  `tick`; and `/scenarios/no-such-lift` displays the exact text `No scenario
  with id no-such-lift` in `no-scenario`.
- **c-1-3** - `/scenarios/above` displays the exact text `6` in `car-floor` and
  the exact text `doors` in `car-mode` after `step-button` is clicked 4 times.
- **c-1-4** - `/scenarios/passing` displays the exact text `3` in `car-floor`
  and the exact text `moving` in `car-mode` after `step-button` is clicked 2
  times. The car is passing floor 3 on its way to floor 5 and does not stop,
  because at tick 2 the manual page has no dispatcher.
- **c-1-5** - `/scenarios/above` displays the exact text `4` in `served-6`, the
  exact text `1` in `served-count` and the exact text `idle` in `car-mode` after
  `step-button` is clicked 5 times.
- **c-1-6** - `/scenarios/quiet` displays the exact text `idle` in `car-mode`,
  the exact text `5` in `car-floor` and the exact text `0` in `served-count`
  after `step-button` is clicked 3 times.

`c-1-1`, `c-1-2` and `c-1-6` name no cut: they grade shipped code, and they are
the criteria that stay green on the all-open skeleton.

**Cut points**

- **`cut-step-move`** - `lib/step.ts`, writes into `next`.
  *Hint:* "The car is `moving`, so put into `next` a car one floor along
  `car.direction`: `'up'` adds one to `car.floor` and `'down'` takes one away.
  `car.target` decides only where the doors open, never which way the car
  travels. Landing on `car.target` gives the pair
  `{ mode: 'doors', floor: car.target }`, and otherwise a `moving` car at the
  new floor keeping the same `direction` and `target`. Leave `pending` and
  `served` as they are."
  Graded by `c-1-3`, `c-1-4` and `c-1-5`. `c-1-4` is its second fixture, on a
  scenario where the car must *not* stop, so a block that always opens the doors
  fails it.
- **`cut-step-doors`** - `lib/step.ts`, writes into `next`.
  *Hint:* "The doors are open at `car.floor`, so put into `next` the state one
  tick on: each call in `state.pending` for that floor with a `tick` at or below
  `state.tick` joins `served` as
  `{ floor, calledAt: the call's own tick, servedAt: state.tick }` and leaves
  `pending`, and the car becomes `{ mode: 'idle', floor: car.floor }`."
  Graded by `c-1-5` alone - the only criterion that reads `served-6` and
  `served-count`.

**Marker placement.** `step` declares its fallback above the markers and returns
below them, so the skeleton compiles:

```
export function step(state: SimState): SimState {
  let next: SimState = { ...state, tick: state.tick + 1 }
  if (state.car.mode === 'moving') { const car = state.car; <cut-step-move> }
  else if (state.car.mode === 'doors') { const car = state.car; <cut-step-doors> }
  return next
}
```

The fallback is the `idle` behaviour - tick forward, car unchanged - and it
fails on purpose: with `cut-step-move` open the car never leaves floor 2, so
`c-1-3` and `c-1-4` go red; with `cut-step-doors` open nothing is ever served,
so `c-1-5` goes red.

**Drop candidate if the session runs long:** hand `cut-step-doors` over written
and keep `cut-step-move`. That is about 6 minutes of live typing recovered, and
it costs `c-1-5`, which is the only criterion that needs it.

### Session 2 - Dispatch and the trace

**Goal:** write the dispatch policy and the fold that turns a scenario into a
trace naming the tick each caller got in.

**Teaches:** a closed dispatch policy; folding a transition into a bounded trace.

**Builds:** `ep-simulate`.

**Acceptance criteria**

- **c-2-1** - `POST /api/scenarios/simulate` returns 200 for the `both-sides`
  scenario with `rows` holding 9 entries and `served` naming floor 2 at
  `servedAt` 2 and floor 6 at `servedAt` 7.
- **c-2-2** - `POST /api/scenarios/simulate` returns 200 for the `overtake`
  scenario with `served` naming floor 8 at `servedAt` 4 and floor 5 at
  `servedAt` 8, the `rows` entry for tick 2 holding floor 6 with `direction`
  `up`, and the `rows` entry for tick 5 holding floor 8 with `direction`
  `down`.
- **c-2-3** - `POST /api/scenarios/simulate` returns 200 for the `passing`
  scenario with `served` naming floor 3 at `calledAt` 2 and `servedAt` 2, and
  floor 5 at `servedAt` 5.
- **c-2-4** - `POST /api/scenarios/simulate` returns 200 for the `both-sides`
  scenario sent with `maxTicks` 4 and answers with `rows` holding 4 entries and
  `complete` false.
- **c-2-5** - `POST /api/scenarios/simulate` rejects a body carrying no
  `scenario` object with 400 and the JSON body
  `{"error": "scenario must carry floors, start and calls"}`, rejects a scenario
  whose call names a floor outside 1 to `floors` with that same 400 body, and
  rejects a body that is not valid JSON with that same 400 body.
- **c-2-6** - `POST /api/scenarios/simulate` returns 200 for the `quiet`
  scenario with `rows` holding one entry of tick 0, floor 5, mode `idle` and
  direction `null`, `served` empty and `complete` true.

Criteria pin the served tick per call and the floor and direction at two named
ticks, plus the row count. They deliberately do not assert a whole `rows` array:
one extra doors tick should fail one criterion, not all six. The tick-5 row in
`c-2-2` is the only place any criterion observes a downward-moving car, and it
is there so `direction` cannot be written as the constant `'up'`: it is the
value `step` moves on, not a label.

**Cut points**

- **`cut-calls-ahead`** - `lib/dispatch.ts`, writes into `ahead`.
  *Hint:* "Put into `ahead` every call in `live` the car reaches without turning
  round: floors above `state.car.floor` for a `dir` of `'up'`, floors below it
  for a `dir` of `'down'`, and all of `live` for a `dir` of `null`. Order them
  by distance from the car, closest first, a tie taken by the lower floor."
  Graded by `c-2-2` alone, and that is the whole point: `overtake` is the only
  fixture where chasing the nearest call anywhere gives a different trace from
  keeping to the current direction. Because the seed lists `overtake`'s floor-5
  call first, dropping either half of this cut - the direction filter or the
  ordering - moves the tick-2 row.
- **`cut-dispatch-target`** - `lib/dispatch.ts`, writes into `next`.
  *Hint:* "Set `next` to a `moving` car standing at `state.car.floor`, its
  `target` taken from `ahead[0].floor` and falling back to the floor in `live`
  closest to the car - the lower floor on a tie - when `ahead` is empty, and its
  `direction` set to `'up'` for a target above the car and `'down'` for one
  below it."
  Graded by `c-2-1`, `c-2-2` and `c-2-3`. `c-2-2`'s tick-5 row is the criterion
  that holds its `direction` rule to something: a car that always claims `'up'`
  runs off the top of the shaft, because `step` moves on `car.direction`.
- **`cut-run-until`** - `lib/run.ts`, writes into `trace`.
  *Hint:* "Fold the run from `seed(scenario)` into `trace`: on each tick give
  the state to `nextTarget`, append the row
  `{ tick, floor, mode, direction }` of that dispatched car to `trace.rows`, and
  carry the dispatched state on through `step`. A dispatched car that is `idle`
  with `pending` empty ends the run with its row appended and `trace.complete`
  true; reaching `maxTicks` rows ends it with `trace.complete` false. The
  `served` list of the last state is `trace.served`."
  Graded by `c-2-1`, `c-2-2`, `c-2-3`, `c-2-4` and `c-2-6`. `c-2-4` and `c-2-6`
  are its own: the `maxTicks` exit and the empty run are decided by the fold and
  by nothing else.

**Marker placement.** Both dispatch cuts sit below their fallbacks, and the
single `return` stays outside every marker pair:

```
export function nextTarget(state: SimState): Car {
  const live = state.pending.filter(c => c.tick <= state.tick)
  if (live.length === 0) return { mode: 'idle', floor: state.car.floor }
  if (live.some(c => c.floor === state.car.floor)) return { mode: 'doors', floor: state.car.floor }
  const dir: Direction | null = state.car.mode === 'moving' ? state.car.direction : null
  let ahead: Call[] = []
  <cut-calls-ahead>
  let next: Car = { mode: 'idle', floor: state.car.floor }
  <cut-dispatch-target>
  return next
}

export function runUntil(scenario: Scenario, maxTicks: number): Trace {
  let trace: Trace = { rows: [], served: [], complete: false }
  <cut-run-until>
  return trace
}
```

The two early returns are the policy's rules 1 and 2 and are shipped written, so
the student's two cuts are rules 3 and 4. Every fallback fails on purpose: an
empty `ahead` leaves `cut-dispatch-target` chasing the nearest call anywhere,
which is a different trace on `overtake`; an idle `next` never moves the car at
all; an empty `trace` has no rows.

**No proper subset of a multi-cut criterion passes.** Checked by hand, because
the step-8 skeleton check only proves the all-open and no-cut cases:

| criterion | with only that cut left open |
|---|---|
| `c-1-5` | `cut-step-move` open, the car never reaches floor 6, nothing is served, red. `cut-step-doors` open, the car reaches the doors and `served-6` never appears, red. |
| `c-2-1`, `c-2-3` | `cut-dispatch-target` open, the car idles for ever, red. `cut-run-until` open, `rows` is empty, red. |
| `c-2-2` | as above, and with `cut-calls-ahead` open the car reverses at tick 2 and floor 5 is served at tick 3 rather than tick 8, red. |

**And no wrongly-filled cut passes either.** The two readings a student is most
likely to write instead of the hint are both red now:

| wrong reading | which criterion catches it |
|---|---|
| `ahead = live` in `cut-calls-ahead` - no direction filter, no ordering | `c-2-2`: at tick 2 the array holds floor 5 first, so the car turns round and the tick-2 row reads `down`. `c-2-1` too: floor 6 is targeted first from floor 4, so the two `servedAt` values swap. |
| `direction: 'up'` unconditionally in `cut-dispatch-target` | `c-2-2`: the tick-5 row must read `down`, and since `step` moves on `car.direction` the car also leaves the shaft. |
| a `both-sides` tie broken by the higher floor | `c-2-1`: the array holds floor 6 first, so insertion order and the tie rule differ and the `servedAt` values swap. |

**Drop candidate if the session runs long:** hand `cut-calls-ahead` over
written and keep the other two. That is about 6 minutes of live typing
recovered, and it costs `c-2-2`, the direction-rule criterion. Do not move a cut
into session 1 to relieve this session - session 1 carries the setup.

## Determinism, and what owns it

`code_checks: ["utc-dates"]` is declared, for the clock half of that check: no
`new Date()` with no arguments and no `Date.now()` anywhere in `app/`. A tick is
a tick and never a second, and this is the one constraint the test suite cannot
see - two runs of the same scenario would still agree even if the Builder timed
something off the wall clock. It is checked at step 6, so a violation lands in
the Builder/test-runner loop instead of at a gate. The date-accessor half of
`utc-dates` is inert here: the project holds no dates at all.

What nothing checks, stated plainly so Gate 1 knows: whether the policy is a
*good* policy. It is arguable by design, and the trace exists to make the
argument visible. The tests only hold it to the ordered procedure written above.

## Session load

The linter's estimate, computed from these hints: **session 1 at 39.3 minutes**
(2 cuts, 2 builds, 2 concepts, plus the project setup) and **session 2 at 36.5
minutes** (3 cuts, 1 build, 2 concepts). Session 2's heaviest cut takes 38% of
its 20.5 cut minutes, under the 45% cap. Session 1's heaviest,
`cut-step-move` at 8.3 of 14.3 cut minutes, is 58% - the 45% cap is not applied
to a two-cut session, because two cuts always split at least 50/50, so read that
number rather than the absent warning. It is why session 1 names a drop
candidate.

Read all of it as a signal, not a measurement. Five projects have overrun a 40
minute cap and the estimate has been between 5 and 13 minutes low on every
flow-2 session ever timed. Nothing before the step 13 dry run measures teaching
time, so each session names one drop candidate above, and each is a block the
student would otherwise type by hand.
