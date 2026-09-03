# Lift - instructor pack

A lift, simulated one tick at a time. Nothing in this project reads a clock.
Tick 0 is the seed, tick *n* is a fold of one pure `step`, and the same scenario
gives the same answer for ever.

Five scenarios are seeded in an 8-floor building. Each call is a hall call given
as `{ floor, tick }` - the floor somebody pressed the button on, and the tick
they pressed it. `/scenarios/[id]` draws the shaft and a step button, so the car
can be walked a tick at a time by hand. `POST /api/scenarios/simulate` runs a
whole scenario to the end and answers with the car's floor, mode and direction
at every tick, plus the tick each caller got in.

The idea being taught is **a policy written down as one ordered procedure**.
"Serve calls in passing order" has at least three readings, so the spec fixes
one, numbers its four rules, and the trace exists to make the argument visible.

**Stack:** Next.js 15.5.24 App Router, React 19, TypeScript 5.7 strict. No
database, no writes at runtime, no clock, no network call out of the app. There
is no store to reset, so the tenth run in a working copy answers exactly as the
first.

**Shape:** 2 sessions, 5 cut points, 12 acceptance criteria. All 12 pass on
`app/`. On the untouched skeleton 4 pass and 8 fail.

---

## Read this before you schedule the sessions

`spec.md` and `lint.json` estimate session 1 at **39.3** minutes and session 2 at
**36.5**, against a 40-minute cap. **This pack does not agree.** Timed cut by cut
against the real code, with the live explanation each hint actually needs:

| session | spec estimate | this pack | over the cap by |
|---|---|---|---|
| 1 - Setup, the shaft, and one tick | 39.3 | **47** | 7 |
| 2 - Dispatch and the trace | 36.5 | **48** | 8 |

Three things a person at Gate 3 should know about that gap.

**The overrun was predicted, by name, at Gate 1.** `ambiguity.md` W12 (worth a
look, owner `pack-writer`) says session 1 sits on 0.7 minutes of headroom on a
model `learning/lessons.md` records as 5 to 13 minutes low on every flow-2
session ever timed, and that its heaviest cut is 58% of its cut minutes with the
share check structurally unable to fire on a two-cut session. That is what this
table is. Nothing new was discovered here; the disclosure was the obligation and
this is it.

**This project's drop candidates are real, unlike the last one's.** `spec.md`
offers `cut-step-doors` in session 1 and `cut-calls-ahead` in session 2. Both are
blocks a student types with their own hands, so dropping either really does
recover live minutes - which was not true of the markup trims pipeline-test-03
offered. Each session file names its own trim list under **Timing - the overrun
and what to trim**, in the order to take them.

**Session 2 needs its trims more than session 1 does.** Session 1 gets inside the
cap by taking one trim: hand `cut-step-doors` over written. Session 2 gets to
40.5 by taking three trims that cost nothing graded, and its own drop candidate
costs `c-2-2`, which is the only criterion that grades the direction filter - so
prefer the three small trims there and keep all three cuts.

If you are the one running the step 13 dry run: **write down which trims you
pulled.** Two dry runs in a row could not say, and a measured overrun that cannot
distinguish "the plan is too big" from "the plan was taught untrimmed" teaches
nobody anything.

---

## What the student is handed

The skeleton is the finished app with five bodies removed. Everything else -
scaffold, types, the seed file, both API routes, the page, the client component,
the CSS - ships written.

```text
skeleton/
  app/
    layout.tsx                        (ships written)
    globals.css                       (ships written)
    api/scenarios/route.ts            ep-scenarios          (ships written)
    api/scenarios/simulate/route.ts   ep-simulate           (ships written)
    scenarios/[id]/page.tsx           the server resolve    (ships written)
    scenarios/[id]/Shaft.tsx          sc-shaft, the client component (ships written)
  lib/
    types.ts                          the data model        (ships written)
    scenarios.ts                      the typed seed read   (ships written)
    state.ts                          seed + manualStart    (ships written)
    step.ts                           2 TODOs - session 1
    dispatch.ts                       2 TODOs - session 2
    run.ts                            1 TODO  - session 2
  data/scenarios.json                 the seed, read-only   (ships written)
```

**All five cut points are in `lib/`, and three of those files are one function
each.** No student writes a line of JSX, a line of routing or a line of
validation in this project. Say that out loud on day one: a student who goes
looking for their work in `app/` will not find it.

## The five cut points

Line numbers are the **skeleton's** - what the student opens.
`.cut-manifest.json` records the `app/` marker line instead, which is a
different number for four of the five.

| cut | skeleton file:line | session | graded by | fails alone on |
|---|---|---|---|---|
| `cut-step-move` | `lib/step.ts:27` | 1 | c-1-3, c-1-4, c-1-5 | c-1-3, c-1-4, c-1-5 |
| `cut-step-doors` | `lib/step.ts:30` | 1 | c-1-5 | c-1-5 |
| `cut-calls-ahead` | `lib/dispatch.ts:34` | 2 | c-2-2 | c-2-2 |
| `cut-dispatch-target` | `lib/dispatch.ts:37` | 2 | c-2-1, c-2-2, c-2-3 | c-2-1, c-2-2, c-2-3 |
| `cut-run-until` | `lib/run.ts:26` | 2 | c-2-1, c-2-2, c-2-3, c-2-4, c-2-6 | all five |

"Fails alone on" is read off `mutation.json`: every one of the five turns at
least one of its own criteria red when it alone is removed, and nothing stayed
green anywhere. Those are the criteria to point a stuck student at.

`mutation.json` also records **collateral**, which is useful in the room:
removing either session-1 cut also turns c-2-1, c-2-2 and c-2-3 red, because
session 2's fold runs the student's own `step`. A student who fudged session 1
finds out in session 2.

## The twelve criteria

| id | session | what it reads | test file |
|---|---|---|---|
| c-1-1 | 1 | `GET /api/scenarios` - five scenarios in seed order, with their keys | `verify/test_api_scenarios.py` |
| c-1-2 | 1 | `/scenarios/above` at tick 0 - 8 floor rows, `car-floor` `2`, `tick` `0`; and the unknown-id message | `verify/test_ui_shaft.py` |
| c-1-3 | 1 | `/scenarios/above` after 4 presses - `car-floor` `6`, `car-mode` `doors` | `verify/test_ui_shaft.py` |
| c-1-4 | 1 | `/scenarios/passing` after 2 presses - `car-floor` `3`, `car-mode` `moving` | `verify/test_ui_shaft.py` |
| c-1-5 | 1 | `/scenarios/above` after 5 presses - `served-6` `4`, `served-count` `1`, `car-mode` `idle` | `verify/test_ui_shaft.py` |
| c-1-6 | 1 | `/scenarios/quiet` after 3 presses - still `idle` on floor `5`, nothing served | `verify/test_ui_shaft.py` |
| c-2-1 | 2 | `both-sides` - 9 rows, floor 2 served at 2, floor 6 at 7 | `verify/test_api_simulate.py` |
| c-2-2 | 2 | `overtake` - floor 8 at 4, floor 5 at 8, tick 2 row up, tick 5 row down | `verify/test_api_simulate.py` |
| c-2-3 | 2 | `passing` - floor 3 `calledAt` 2 `servedAt` 2, floor 5 at 5 | `verify/test_api_simulate.py` |
| c-2-4 | 2 | `both-sides` with `maxTicks` 4 - 4 rows, `complete` false | `verify/test_api_simulate.py` |
| c-2-5 | 2 | three bad bodies, one 400 and one message | `verify/test_api_simulate.py` |
| c-2-6 | 2 | `quiet` - one idle row, nothing served, `complete` true | `verify/test_api_simulate.py` |

c-1-1, c-1-2, c-1-6 and c-2-5 name no cut. They grade shipped code and they are
the four that stay green on the untouched skeleton, which is what makes them
useful on day one: "four of these already pass, and none of them is yours."

## The data model

`lib/types.ts`, shipped written. The whole project is these seven types:

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

The car's mode is a **discriminated union**, not three booleans, so a car cannot
be moving and idle at once - and a `doors` car has no `direction` and no
`target`, because those fields do not exist on that member of the union.
`direction` on a `TraceRow` is `null` for `doors` and for `idle`.

## The seed

`data/scenarios.json`, read-only, shipped written:

```json
[
  {
    "id": "above",
    "name": "One call above the car",
    "floors": 8,
    "start": 2,
    "calls": [{ "floor": 6, "tick": 0 }]
  },
  {
    "id": "both-sides",
    "name": "Calls on either side",
    "floors": 8,
    "start": 4,
    "calls": [{ "floor": 6, "tick": 0 }, { "floor": 2, "tick": 0 }]
  },
  {
    "id": "overtake",
    "name": "A nearer call behind",
    "floors": 8,
    "start": 4,
    "calls": [{ "floor": 5, "tick": 2 }, { "floor": 8, "tick": 0 }]
  },
  {
    "id": "passing",
    "name": "A call at the passing floor",
    "floors": 8,
    "start": 1,
    "calls": [{ "floor": 5, "tick": 0 }, { "floor": 3, "tick": 2 }]
  },
  {
    "id": "quiet",
    "name": "No calls at all",
    "floors": 8,
    "start": 5,
    "calls": []
  }
]
```

### Do not let anybody tidy that file

The order of the objects **inside** each `calls` array is load-bearing and no
criterion pins it. `overtake` lists its tick-2 floor-5 call *first* and its
tick-0 floor-8 call second; `both-sides` lists floor 6 before floor 2. That is
deliberate: it is what makes a `cut-calls-ahead` written as `ahead = live` - no
direction filter, no ordering - fail c-2-2 and c-2-1 instead of reproducing every
pinned trace exactly.

Sorting either array into the obvious registration order leaves **all twelve
criteria green** and silently stops grading both the direction filter and the tie
rule. This was carried from Gate 1 to Gate 2 as the one thing no script can
check, hand-checked there, and it is carried here. It is the most important
paragraph in this README for anyone maintaining the project.

## What the five scenarios are for

| id | start | calls | what it exists to grade |
|---|---|---|---|
| `above` | 2 | floor 6 at tick 0 | session 1's whole manual walk: climb, land, open, serve, go idle |
| `both-sides` | 4 | floor 6 at 0, floor 2 at 0 | a distance tie, taken by the lower floor - c-2-1 |
| `overtake` | 4 | floor 5 at 2, floor 8 at 0 | the only fixture where "nearest ahead" and "nearest anywhere" disagree - c-2-2 |
| `passing` | 1 | floor 5 at 0, floor 3 at 2 | a call registered for the floor the car is standing on, on that tick - c-2-3 |
| `quiet` | 5 | none | the empty run, and the `idle` case of `step` - c-1-6, c-2-6 |

## How to run it

Each tree has its own `node_modules` and its own `package-lock.json`. Install in
whichever one you open.

```text
cd projects/pipeline-test-05/skeleton     # or .../app for the finished build
npm ci
npm run dev
```

Then `http://localhost:3000/scenarios/above`. There is no index route: `/` is a
404 and that is not a defect. Every URL in this project is `/scenarios/<id>` or
an `/api/` path.

Use `npm run dev`, not `npm run start` - the page and both routes are
`force-dynamic`, and a stale production build will not pick up an edit to
`lib/`.

To run the graded suite, let the pipeline boot the app. Do not start a server
first:

```text
python3 -m pipeline test pipeline-test-05 --target skeleton
python3 -m pipeline test pipeline-test-05 --target app
```

It installs, builds, starts the server on a free port, exports `BASE_URL`, runs
pytest with Playwright and writes `skeleton-results.json` / `results.json`.

## Six claims to get right in class

All six were raised at Gate 1, left in the spec on purpose, and land in the
teaching. They are corrected here so nobody teaches them wrong.

**1. Do not open `/scenarios/overtake` in session 1.** (`ambiguity.md` W1, owner
`pack-writer` - this pack.) `manualStart` aims the car at `calls[0].floor`, and
`overtake`'s first call is floor 5 registered for **tick 2**. So one press lands
the car on floor 5 at tick 1 with the doors open, the doors branch finds no call
that is live yet, nobody boards, `served-count` stays `0`, and the car goes idle
for ever with the call still pending. It teaches the exact opposite of what
`cut-step-doors` says. Session 1 walks `above`, `passing` and `quiet` only. Both
session files say so at the top of their plans.

**2. The prohibition on `Math.sign` is not graded.** (W4, owner `nothing`.)
`spec.md` says `step` must not derive its movement from
`Math.sign(car.target - car.floor)`. A cut written that way passes all twelve
criteria, including c-2-2's downward tick-5 row. Teach `direction` as the value
the simulation runs on rather than a label on the row - and if a student asks
whether the tests catch it, the honest answer is no.

**3. `cut-dispatch-target`'s `ahead`-empty branch never runs.** (W6, owner
`nothing`.) On all five fixtures, once rules 1 and 2 have not returned, `ahead`
is non-empty: a moving car is always moving towards a live call that is still
ahead of it, and a car that is not moving has `dir === null`, for which `ahead`
is all of `live`. The student is told to write the fallback and nothing grades
it. Write it, do not spend three minutes justifying it, and say plainly that it
is there so the expression is total.

**4. Dropping `cut-calls-ahead` costs more than `spec.md` says.** (W3, owner
`nothing`.) The spec says it is "graded by c-2-2 alone". c-2-2 grades the
*direction filter*. The *ordering* half is graded by c-2-1, because `both-sides`
at tick 0 is the only state in any fixture where `ahead` holds two calls. If you
take session 2's named drop candidate you lose grading on both halves.

**5. An upside-down shaft passes.** (W10, owner `nothing`.) c-1-2 asserts that
eight elements with `data-testid` `floor-1` .. `floor-8` exist; nothing asserts
document order, and nothing reads the `tick` readout past its seeded `0`. The
shipped markup renders floor 8 at the top, which is right - just do not claim a
test is holding it there.

**6. `cut-step-doors` can be faked inside session 1.** (W8, owner `nothing`.)
c-1-5 prints all three numbers it wants - `served-6` `4`, `served-count` `1` -
so a literal `served: [{ floor: 6, calledAt: 0, servedAt: 4 }]` satisfies it.
Session 2's folds separate the literal from the transition on four different
floors, and `mutation.json`'s collateral column confirms it. If you see a
literal, say: "that answers this one page. Session 2 runs the same function nine
times on a scenario you have not seen."

## Files in this pack

- `session-1.md` - Setup, the shaft, and one tick
- `session-2.md` - Dispatch and the trace
- `troubleshooting.md` - the errors students actually hit, with the fix
