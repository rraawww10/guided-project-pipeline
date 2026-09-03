# Ambiguity report - pipeline-test-05

**Verdict:** 3 blocking, 7 worth a look

**Spec reviewed:** the `spec.md` / `spec.json` pair whose hash `lint.json` records as
`9466cbb44b2be79267fbd8a21780f56d33a2c15c800a191fb6a8e98555c7bf32`. Nothing was
edited during this pass.

**Round:** this is the first pass. `.pipeline/state.json` has `gate1: null`, no
`breaker` entry in `step_runs` and there is no `.pipeline/round-*/` directory, so
there is no earlier `ambiguity.md`, `gate1.json` or `why.md` to reconcile against.
Every finding below is new by construction, not "new to this round".

**What I checked before writing.** I re-derived all four `runUntil` traces
(`both-sides`, `overtake`, `passing`, `quiet`) and the five-click `above` walk from
the ordered procedure alone. Every row, every `servedAt` and every row count in the
spec's pinned tables is reproducible, and every session-2 number in a criterion
reads off them correctly. I also re-ran the spec's own leave-one-out table: all
five cuts turn at least one of their own criteria red when opened alone, the
all-open skeleton fails exactly the criteria that declare cuts (c-1-1, c-1-2, c-1-6
and c-2-5 pass), and the five cut signatures are pairwise distinct so E110 is
correctly quiet. The three risks Gate 0 carried forward are all answered: the
policy is a single ordered procedure with pinned traces, the criteria pin per-call
served ticks rather than whole arrays, and `nextTarget` is split inside session 2.

The findings below are what survived that. Two of them are grading holes of the
kind the lessons file calls "a cut graded against one input cannot be told from a
constant" - not empty-cut holes, which `mutation` covers here, but *wrongly filled*
cut holes, which nothing downstream sees.

## Blocking

### B1 - `overtake`'s call order lets `cut-calls-ahead` be `ahead = live` and stay green
- **Where:** spec.md, the seed table for `overtake` and `both-sides`; `cut-calls-ahead`; c-2-2
- **Owner:** nothing
- **The line:** "`overtake` is the fifth and it is not decoration: it is the only fixture on which "the nearest call ahead" and "the nearest call anywhere" disagree, so without it `cut-calls-ahead` cannot be told apart from a car that always chases the closest caller."
- **Reading one:** the student writes the cut as the hint states it - filter `live`
  by `dir`, then order by distance with the lower floor on a tie.
- **Reading two:** the student writes `ahead = live` - no direction filter and no
  ordering, i.e. the `dir === null` case of the hint applied unconditionally. This
  is the single most likely partial implementation of that hint.
- **Why it matters:** reading two passes all twelve criteria. I traced it.
  `live = state.pending.filter(...)` preserves array order, and `overtake`'s calls
  are seeded `{floor: 8, tick: 0}` *then* `{floor: 5, tick: 2}`, so at tick 2
  `ahead[0]` is the floor-8 call under both readings and the trace is
  byte-identical to the pinned one - `c-2-2`'s "tick 2 holding floor 6 with
  direction `up`" passes. `both-sides`, `passing`, `quiet` and the `maxTicks` run
  are identical too. The same accident hides the tie rule: `both-sides` is seeded
  floor 2 before floor 6, so insertion order and "distance tie, lower floor" both
  answer floor 2, and the spec's claim that "`both-sides` is also a distance
  tie ... which is what grades the tie rule" holds only against an implementation
  that sorts and then breaks the tie the *wrong* way. So both rules inside the cut
  whose whole justification is `overtake` are ungraded, and this is the headline
  cut of session 2. No downstream checker sees it: `mutation` opens the cut
  entirely, which does go red (`ahead = []` reverses at tick 2), so mutation
  reports ok; `skeleton-check` only sees all-open; E110 sees distinct signatures;
  the Builder writes the hint correctly so `test-runner` stays green. It ships as a
  session whose student can hold the opposite dispatch policy and be graded correct.
- **Suggested wording:** seed `overtake`'s calls as `{floor: 5, tick: 2}` then
  `{floor: 8, tick: 0}`, and `both-sides`' as `{floor: 6, tick: 0}` then
  `{floor: 2, tick: 0}` - both pinned traces are unchanged for a correct
  implementation, while `ahead = live` now targets floor 5 at tick 2 (c-2-2 red)
  and floor 6 first from floor 4 (c-2-1's `servedAt` values swap, red). The table's
  column header must then read "calls" rather than "in the order the building
  registered them", or say that the array order is deliberately not the
  registration order.

### B2 - no criterion in the suite pins a `direction` of `down`
- **Where:** spec.md, c-2-1 / c-2-2 / c-2-6 and `cut-dispatch-target`; also `cut-step-move`
- **Owner:** nothing
- **The line:** "`direction` is `'up'` for a target above the car and `'down'` for one below."
- **Reading one:** `step` moves the car by `car.direction`, so a wrong `direction`
  sends the car the wrong way and the trace collapses.
- **Reading two:** `step` moves the car by `Math.sign(car.target - car.floor)` -
  also a fair reading of "one floor closer to `car.target` in its `car.direction`",
  which names both the outcome and the mechanism. Then `direction` is a decorative
  field on the row.
- **Why it matters:** the only `direction` values any criterion asserts are `up`
  (c-2-2, tick 2) and `null` (c-2-6, the idle row). Under reading two a student
  who writes `direction: 'up'` unconditionally in `cut-dispatch-target` produces
  the pinned trace for every fixture except the `direction` column of the
  downward rows, which nothing reads - all twelve criteria green. Under reading
  one the same error runs the car off the top of the shaft and c-2-1 goes red. So
  which student errors the suite catches depends on an implementation choice the
  spec leaves open, and the two readings are indistinguishable to every checker:
  they agree on every fixture, so `test-runner` and `skeleton-check` cannot
  separate them, and `mutation` opens the whole cut rather than mis-filling it.
  Session 1 makes this worse rather than better - `manualStart` aims at
  `calls[0]`, which is above the car in both `above` (2 to 6) and `passing`
  (1 to 5), so no session-1 criterion ever sees a downward-moving car either.
- **Suggested wording:** add to c-2-2 "and the `rows` entry for tick 5 holding
  floor 8 with `direction` `down`" - it is already in the pinned `overtake` table -
  and state in the `cut-step-move` prose that the car advances by `car.direction`,
  with `car.target` only deciding when the doors open.

### B3 - `sc-shaft` seeds `useState` from `manualStart` but gets its scenario asynchronously
- **Where:** spec.md, Screens, `sc-shaft`; c-1-2; spec.json screens[0].states
- **Owner:** test-runner
- **The line:** "`sc-shaft` at `/scenarios/[id]`, built in session 1, a client component holding one `SimState` in `useState` seeded from `manualStart`." and "The page reads its scenario from `GET /api/scenarios` and picks the matching `id`."
- **Reading one:** a client component that fetches in an effect. Then there is no
  scenario at mount, `useState` cannot hold a `SimState` on the first render, and
  the page needs a fourth state the spec does not list - and since `no-scenario`
  is the only "not in the seed" element declared, the obvious implementation
  renders "No scenario with id above" for the first frame of every valid page.
- **Reading two:** a server component that awaits `GET /api/scenarios` and passes
  the matched `Scenario` into a client child, which then really can do
  `useState(manualStart(scenario))`. That means a server-side fetch of the app's
  own route, which needs an absolute base URL.
- **Reading three:** import `data/scenarios.json` directly and skip the endpoint,
  which contradicts "reads its scenario from `GET /api/scenarios`" but is what
  makes the first render synchronous.
- **Why it matters:** the shaft page is session 1's only screen and four of its six
  criteria drive it, so this is the first thing the Builder must decide and the
  spec supports three different answers with different shipped shapes. The
  `states` list in spec.json ("tick 0", "car moving", "doors open", "no calls at
  all", "unknown scenario id") has no loading entry and no `data-testid` is
  reserved for one, so the Test Writer has nothing to write a loading assertion
  from either. It is owned rather than unowned because it surfaces at step 6: on
  the async reading, c-1-2's "the exact text `2` in `car-floor`" is red unless the
  assertion waits, and the Builder cannot edit the test, so the loop forces a
  synchronous first render. The residual the loop will not catch is the
  `no-scenario` flash, which is why this is blocking rather than worth a look.
- **Suggested wording:** state that `/scenarios/[id]` resolves its `Scenario` on
  the server before rendering and passes it to the client component, that
  `no-scenario` renders only when the id is absent from the seed, and that no
  loading state is reachable in a test.

## Worth a look

### W1 - `cut-dispatch-target`'s `ahead`-empty branch is unreachable
- **Where:** spec.md, the policy rule 4, and `cut-dispatch-target`'s hint
- **Owner:** nothing
- **The line:** "With `ahead` empty it reverses: `target` is the floor in `live` closest to the car, again lower floor on a tie."
- **Reading one:** the branch is a live rule the student must get right.
- **Reading two:** the branch never executes, so anything satisfies it.
- **Why it matters:** reading two is provably the case. A car is `moving` only
  towards the floor of a live call, that call stays live and stays ahead until the
  car lands on it, and on landing the car is `doors` and then `idle` - and an
  `idle` car has `dir === null`, for which `ahead` is all of `live`. So whenever
  rules 1 and 2 have not already returned, `ahead` is non-empty. Every reversal in
  the pinned traces (`both-sides` tick 3, `overtake` tick 5) goes through the
  `dir === null` path, not this one. The cost is that a third of a 7.7-minute cut
  is dead code the student is told to write and no test can correct, and that the
  policy's stated headline - "reverse only when nothing is pending ahead" - is
  never exercised as written. Nothing downstream sees a branch that is never
  taken; if I am wrong about reachability the failure mode is a crash on
  `ahead[0]`, which `test-runner` would catch, so the exposure is bounded.
- **Suggested wording:** either delete the fallback from rule 4 and the hint and
  say instead that `ahead` is non-empty whenever rules 1 and 2 did not return,
  because a car only ever moves towards a live call; or start one scenario's car
  `moving` so the branch is reachable and grade it.

### W2 - `cut-step-doors` is graded by one criterion on one served call
- **Where:** spec.md, Session 1, `cut-step-doors`, c-1-5
- **Owner:** nothing
- **The line:** "Graded by `c-1-5` alone - the only criterion that reads `served-6` and `served-count`."
- **Reading one:** the student writes the serve-and-close transition.
- **Reading two:** the student writes
  `{ ...state, tick: state.tick + 1, pending: [], served: [{ floor: 6, calledAt: 0, servedAt: 4 }], car: { mode: 'idle', floor: car.floor } }`
  - a literal, which is exactly the shape of habit-tracker's `cut-week-dates`
  lesson.
- **Why it matters:** c-1-5 is the only criterion that observes the doors
  transition inside session 1, and it observes it once, on one scenario, with one
  served call whose three numbers are printed in the criterion. `mutation` does
  not cover this (the empty cut is red, so mutation is satisfied) and neither does
  `skeleton-check`. It is *worth a look* rather than blocking only because the
  full suite does separate the literal: c-2-1, c-2-2, c-2-3 and c-2-6 all fold
  `step` through `runUntil` and assert different floors and different
  `servedAt` values, so a literal cannot survive session 2. What ships is a
  session 1 a student can sign off on with a constant, and note that spec.json's
  `cuts` lists for the session-2 criteria do not declare their real dependency on
  `cut-step-move` and `cut-step-doors`, so nothing records that this is what
  covers it.
- **Suggested wording:** give c-1-5 a second observation - `/scenarios/passing`
  clicked 5 times shows `5` in `served-5` and `1` in `served-count` - or state
  explicitly that `cut-step-doors` is graded within session 1 by one fixture and
  regraded by the session-2 criteria.

### W3 - `maxTicks` reached and the run completing on the same row
- **Where:** spec.md, `runUntil`, and `cut-run-until`'s hint; c-2-4, c-2-6
- **Owner:** nothing
- **The line:** "The run ends **complete** on a dispatched car that is `idle` with `pending` empty, with that final row appended. It ends **incomplete** the moment `trace.rows` reaches `maxTicks`."
- **Reading one:** the completion test wins, so `quiet` with `maxTicks` 1 answers
  one row and `complete` true.
- **Reading two:** the bound wins, so the same call answers one row and
  `complete` false.
- **Why it matters:** it does not change any graded value - `maxTicks` defaults to
  100 and c-2-4 stops `both-sides` at row 4, five rows short of its natural end,
  so no criterion reaches the tick where the two conditions coincide. That is also
  why nothing downstream can see it: both readings are green everywhere. It is
  listed because "behaviour when a collection is empty or a bound is hit is
  unstated" is the second most frequent Gate 1 class in `lessons.md`, and one
  sentence closes it.
- **Suggested wording:** add "a row that both completes the run and reaches
  `maxTicks` is `complete` true - the bound only reports a run that had further to
  go".

### W4 - two stated display rules that no criterion grades
- **Where:** spec.md, Screens table (`floor-1` .. `floor-8`, `tick`); c-1-2, c-1-6
- **Owner:** nothing
- **The line:** "one row per floor, floor 8 at the top down to floor 1 | `floor-1` .. `floor-8` | the floor number"
- **Reading one:** the shaft renders floor 8 first in the DOM.
- **Reading two:** the shaft renders floor 1 first. c-1-2 asserts only that eight
  elements with those testids exist, so an upside-down lift is green.
- **Why it matters:** the same gap covers the `tick` readout: c-1-2 pins it at `0`
  and no criterion reads it again, and c-1-6 clicks three times without asserting
  it, so a page whose tick display never advances passes. Both belong to
  shipped-written markup, so no student types them and the prose is unambiguous -
  the Builder will very likely get both right. But this is `lessons.md`'s most
  frequent rejection class (a rule the spec states that no criterion grades, six
  times), and no checker reads DOM order or an unasserted element.
- **Suggested wording:** add to c-1-2 "with `floor-8` appearing before `floor-1` in
  document order", and to c-1-6 "and the exact text `3` in `tick`".

### W5 - the skeleton keeps three locals whose only readers are inside the cuts
- **Where:** spec.md, both Marker placement blocks; `cut-step-move`, `cut-step-doors`, `cut-calls-ahead`, `cut-dispatch-target`
- **Owner:** typecheck
- **The line:** "if (state.car.mode === 'moving') { const car = state.car; <cut-step-move> }"
- **Reading one:** the marker layout is fine - the return sits outside every pair,
  which is the rule the lessons file cares about, and it does here in all three
  functions.
- **Reading two:** the generated skeleton declares `const car` twice in `step` and
  `const dir` in `nextTarget` with every reader removed, plus `let ahead` and
  `let next` assigned once and never reassigned. On a tsconfig with
  `noUnusedLocals` that is TS6133 on three declarations and the student's tree does
  not compile - the same class of outcome as TS2355, arriving from a different
  rule.
- **Why it matters:** it is contingent on the tsconfig the Builder generates, which
  is why it is worth a look and not blocking. The owner is honest but weak:
  `cutter.typecheck` is the fail-open second line, so if the toolchain cannot be
  reached it reports no error and this lands in the student skeleton with every
  gate green. Gate 1 should list it under `verify_later` and someone should read
  `typecheck_fail_open` in `skeleton-check.json` at step 8.
- **Suggested wording:** state that the cut bodies must read `state.car` and
  `state.pending` directly, so no narrowing local sits outside a marker pair; or
  state that the skeleton's tsconfig leaves `noUnusedLocals` off.

### W6 - the idea's payoff is a visible trace; the spec ships JSON only
- **Where:** idea.md Theme and session 2 "Runs"; spec.md Out of scope, `ep-simulate`
- **Owner:** pack-writer
- **The line:** "A trace screen. The session-2 trace is JSON from `POST /api/scenarios/simulate`; rendering it would cost a second screen build that session 2 has no minutes for."
- **Reading one:** the trace is a machine artifact and the tests are what read it.
- **Reading two:** the trace is the reason the project is worth two sessions. The
  idea says "the policy is arguable and the trace makes the argument visible - a
  student who serves the nearest call first can see, in the table, the passenger
  on floor 7 who never gets picked up", and the spec's own closing section leans
  on the same idea ("the trace exists to make the argument visible").
- **Why it matters:** the drift is declared and its reason - minutes - is the right
  one, so this is not a scope complaint. But session 2 now ends with a student
  reading a JSON body from a POST they have to construct by hand, and nothing in
  the spec says how. That lands squarely on the Pack Writer at step 9: if the
  guide cannot show a student the trace in a way that makes the policy arguable,
  the session's stated teaching goal is not delivered, and a person reads that at
  Gate 3.
- **Suggested wording:** name in session 2 how the student sees the trace - the
  exact request the guide will have them send and where its answer is read - so
  the Pack Writer is not inventing the session's payoff at step 9.

### W7 - session load: the estimate is low on exactly this shape, and session 1 is outside W114's reach
- **Where:** spec.md, Session load; `cut-step-move`; lint.json session_minutes
- **Owner:** pack-writer
- **The line:** "The heaviest cut in session 2 takes 38% of its cut minutes, under the 45% cap."
- **Reading one:** both sessions fit - 38.8 and 36.5 against a 40 minute cap, no
  linter warning.
- **Reading two:** the sentence is true and reports only session 2. `lint.json`
  records `largest_cut_share` 0.56 for session 1, and `_check_cut_share` skips any
  session with fewer than three cuts, so W114 could not have fired there whatever
  the number was. Session 1 also carries the whole project setup.
- **Why it matters:** six consecutive projects have overrun a 40 minute cap and
  `lessons.md` puts the cause in one place - a single cut with several ordered
  rules in it. `cut-step-move` is scored at 1 stated decision, and its hint states
  two outcomes (landing on `car.target` versus stopping short) plus a preservation
  rule for `pending` and `served`; that is the `cut-parse-line` shape the model
  reads low. The spec is otherwise honest here: it discloses the historical
  underestimate itself, and both drop candidates are real blocks a student types,
  which is the trap `lessons.md` records for pipeline-test-03. Nothing before the
  step 13 dry run measures teaching time, so the last owner that can act is the
  Pack Writer at step 9 - and it can only disclose, not fix.
- **Suggested wording:** none needed for the spec's numbers, which match
  `lint.json` exactly. If anything moves, split `cut-step-move` so the landing
  case and the stopping-short case are stated as one rule each, or state session
  1's cut share and why the 45% cap does not apply to a two-cut session.
