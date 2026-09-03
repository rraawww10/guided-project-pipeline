# Ambiguity report - pipeline-test-05

**Verdict:** 1 blocking, 12 worth a look

**Spec reviewed:** the `spec.md` / `spec.json` pair whose hash `lint.json` and
`.pipeline/breaker-begin.json` both record as
`2779e2855142364fec0ed1c5c2306a7312d2d83120ae108e0a55ed581e626816`. Nothing was
edited during this pass.

**Round:** this is round 2. `.pipeline/round-1/` holds a rejected round, so I read
`spec.md` and `spec.json` on their own first, then `idea.md`, then round 1's
`ambiguity.md`, `gate1.json` and `why.md`, then `learning/lessons.md`. Every
finding below says whether it is new, a re-raise, or an item round 1 recorded as
deliberately kept.

**What I checked before writing.** I re-derived all four `runUntil` traces and the
five-click `above` walk from the ordered procedure alone, against the *new* seed
order. Every row, every `servedAt` and every row count in the pinned tables is
reproducible, and every number in a session-2 criterion reads off them correctly.
Round 1's two must-fix items are genuinely fixed and I confirmed the fixes bite:

- **B1 fixed.** With `overtake` seeded floor 5 before floor 8, `ahead = live` now
  targets floor 5 from floor 6 at tick 2, so `c-2-2`'s tick-2 row reads `down` and
  goes red. With `both-sides` seeded floor 6 before floor 2, the same reading
  targets floor 6 first from floor 4 and `c-2-1`'s two `servedAt` values swap, red.
  A tie broken by the higher floor is red on `c-2-1` for the same reason. The
  correct traces are unchanged by the reorder, exactly as the spec claims.
- **B2 fixed.** `c-2-2` now asserts the tick-5 row as floor 8 `direction` `down`,
  which is the only downward-moving row any criterion observes, so
  `direction: 'up'` unconditionally in `cut-dispatch-target` is red.

I also re-ran the leave-one-out by hand: all five cuts turn at least one of their
own declared criteria red when opened alone, and the all-open skeleton fails
exactly the criteria that declare cuts (`c-1-1`, `c-1-2`, `c-1-6` and `c-2-5`
pass). So **no finding here needs `mutation` as its owner** - there is no cut that
can be left empty with every criterion green. What is left is the harder class
`lessons.md` counts six times: rules the spec states that no criterion grades.

**On `code-check`.** `spec.json` declares `code_checks: ["utc-dates"]`, so that
owner is live rather than empty, and the spec assigns clock determinism to it
correctly. I considered it for W4 below, which is genuinely a constraint on the
*shape* of the code, and rejected it: the registry is fixed, `utc-dates` does not
look at `Math.sign`, and naming a check that cannot see the defect would be
`nothing` wearing a checker's name. W4 is owned by `nothing` and said so plainly.

**The delta this round.** W1 to W5 are new or newly-changed. W6 to W12 are round
1's seven worth-a-look findings, all recorded in `why.md` as deliberately kept;
they are restated at their round-1 classification so the approved record does not
lose them, not re-argued.

## Blocking

### B1 - `sc-shaft` seeds `useState` from `manualStart` but gets its scenario asynchronously
- **Where:** spec.md, Screens, `sc-shaft`; c-1-2; spec.json screens[0].states
- **Owner:** test-runner
- **The line:** "`sc-shaft` at `/scenarios/[id]`, built in session 1, a client component holding one `SimState` in `useState` seeded from `manualStart`." and "The page reads its scenario from `GET /api/scenarios` and picks the matching `id`."
- **Re-raise:** round 1's **B3**, at the identical classification - blocking, owner
  `test-runner`. `why.md` says "B3 is blocking but owned by test-runner - the
  Builder/test-runner loop hits it at step 7 for free. Do not pre-fix it," so it is
  already adjudicated and was deliberately left. The two quoted sentences are
  byte-identical to the spec round 1 read; the only change nearby is the added
  "Both the screen and the endpoint it fetches are built in session 1", which
  answers a different question. I have no new evidence, so I am not moving the
  severity or the owner in either direction - restating it unchanged is the point.
- **Reading one:** a client component that fetches in an effect. There is no
  scenario at mount, so `useState` cannot hold a `SimState` on the first render,
  and since `no-scenario` is the only "not in the seed" element declared, the
  obvious implementation renders "No scenario with id above" for the first frame of
  every valid page.
- **Reading two:** a server component that resolves the scenario and passes it to a
  client child, which then really can do `useState(manualStart(scenario))` - but
  that means a server-side fetch of the app's own route and an absolute base URL.
- **Reading three:** import `data/scenarios.json` directly and skip the endpoint,
  which contradicts "reads its scenario from `GET /api/scenarios`" but is the only
  thing that makes the first render synchronous with no server component.
- **Why it matters:** four of session 1's six criteria drive this page, so it is the
  first thing the Builder must decide, and the spec supports three shapes. It stays
  owned because it surfaces at step 6: on the async reading `c-1-2`'s "the exact
  text `2` in `car-floor`" is red unless the assertion waits, the Builder cannot
  edit `verify/`, and the loop forces a synchronous first render. The residual the
  loop cannot see is the `no-scenario` flash on a valid id, which is why round 1
  called it blocking and why I keep that.
- **Suggested wording:** state that `/scenarios/[id]` resolves its `Scenario` on the
  server before rendering and passes it to the client component, that `no-scenario`
  renders only when the id is absent from the seed, and that no loading state is
  reachable in a test.

## Worth a look

### W1 - the seed reorder changed what `/scenarios/overtake` shows in session 1
- **Where:** spec.md, the seed table for `overtake`, `manualStart`, and Screens/`sc-shaft`
- **Owner:** pack-writer
- **The line:** "`manualStart` on either of them simply aims at whichever call the array holds first."
- **New this round, and introduced by the B1 fix.** In the spec round 1 read,
  `overtake`'s `calls[0]` was `{floor: 8, tick: 0}`; it is now `{floor: 5, tick: 2}`.
  Round 1 could not have found this because the line it depends on did not exist.
- **Reading one:** the sentence is a harmless note - no criterion drives `overtake`
  on the shaft page, so the aim does not matter.
- **Reading two:** it does matter to what a person sees. `manualStart(overtake)`
  now starts a moving car at floor 4 aimed at floor 5, so one click lands it on
  floor 5 with the doors open at tick 1 - and the floor-5 call has `tick: 2`, so the
  doors branch serves nobody, `served-count` stays `0`, `served-5` never appears,
  and the car goes `idle` with the call still pending. Under the old order the car
  climbed to floor 8 and the pickup worked.
- **Why it matters:** it is not a grading defect - `c-1-3` to `c-1-6` drive `above`,
  `passing` and `quiet` only, and all four still hold. It is a demo defect. The
  shaft page is the only screen in the project and `/scenarios/overtake` is a live
  route in session 1's skeleton; a guide that walks the five scenarios shows a lift
  that opens its doors on an empty landing, which teaches the opposite of what
  session 1's `cut-step-doors` says. The owner is the Pack Writer at step 9 because
  that is the last place a person looks at the page before Gate 3 - and it is a
  conditional ownership: if the guide never opens `/scenarios/overtake`, nothing
  sees it at all.
- **Suggested wording:** add to the `manualStart` paragraph that the shaft page is
  only walked on `above`, `passing` and `quiet` in session 1, because `overtake`'s
  first call is registered for tick 2 and the manual page has no dispatcher to
  wait for it.

### W2 - the call order inside `calls` is now load-bearing for grading, and no criterion pins it
- **Where:** spec.md, the seed table and the array-order paragraph; c-1-1; `cut-calls-ahead`
- **Owner:** nothing
- **The line:** "**The `calls` column is deliberately not registration order.**"
- **New this round.** The invariant it names did not exist in the spec round 1 read,
  so this is not a re-raise of B1 and not an escalation of anything. Round 1's
  suggested wording asked for exactly the reorder plus a relabelled column, and
  `why.md` scoped the fix to "reorder the two seed rows ... Do not add a criterion
  for this". I am **not** asking for a new criterion, and I am deliberately *not*
  making this blocking - see below.
- **Reading one:** the order is stated and defended in its own paragraph, so
  `data/scenarios.json` will carry it.
- **Reading two:** the order is the one thing in the seed no test can tell apart. A
  Builder, or anyone tidying the file later, sorts `overtake`'s calls into
  registration order - floor 8 at tick 0 before floor 5 at tick 2, which is what
  round 1's spec said and what a reviewer would call the obvious order - and every
  one of the twelve criteria stays green, because the pinned traces are unchanged
  for a correct implementation. That is the fix's own selling point working against
  it.
- **Why it matters:** `c-1-1` pins the order of the five *scenarios* and the *keys*
  each carries, and nothing pins the order of the elements inside `calls`. So the
  entire grading value of the B1 fix rests on a prose-only invariant that no
  checker reads: not `spec-linter` (nothing compares the seed table to the app's
  data file), not `test-runner` (both orders are green by construction), not
  `mutation` (it opens the whole cut, which is red either way). A second, smaller
  gap sits behind it: the spec never says whether the scenario in `ep-simulate`'s
  body comes from `GET /api/scenarios` or from a literal in the test, and the
  answer decides whether the app's seed order or the test's own order is what
  grades `cut-calls-ahead`. I am filing this as worth a look rather than blocking
  because the Builder is not being asked to guess - the spec states the order and
  spends a paragraph defending it - so the exposure is later drift rather than a
  choice at build time. It is the one item on this list I would ask a person to
  confirm by eye at step 6: read `app/data/scenarios.json` and check the two
  reordered rows.
- **Suggested wording:** extend `c-1-1` (no new criterion) with "with `overtake`'s
  `calls` in the order floor 5 then floor 8 and `both-sides`' floor 6 then floor 2",
  and say that the test posts the scenario exactly as `GET /api/scenarios` returns
  it.

### W3 - `cut-calls-ahead`'s note claims the tick-2 row grades both halves of the cut; it grades one
- **Where:** spec.md, `cut-calls-ahead`'s cut-point note; c-2-1, c-2-2
- **Owner:** nothing
- **The line:** "Because the seed lists `overtake`'s floor-5 call first, dropping either half of this cut - the direction filter or the ordering - moves the tick-2 row."
- **New this round** - the sentence was added by the B1 fix.
- **Reading one:** both the direction filter and the distance ordering are graded by
  `c-2-2`'s tick-2 row, so `cut-calls-ahead` is covered by one criterion.
- **Reading two:** only the direction filter is. I traced the two halves
  separately. Drop the ordering and keep the filter: on `overtake`, `ahead` never
  holds more than one call at any tick (at tick 2 the only live call above floor 6
  is floor 8), so no `overtake` row moves and `c-2-2` stays green - the mis-fill is
  caught instead by `c-2-1`, where `both-sides` at tick 0 has `dir === null`,
  `ahead` holds two calls, and an unordered `ahead[0]` is floor 6 rather than floor
  2. Drop the filter and keep the ordering: `c-2-2` catches it and `c-2-1` does not.
- **Why it matters:** the substance is fine and is in fact better than the spec
  says - each half has its own grading fixture, which is what `lessons.md` asks for
  ("a pure-function cut needs at least two grading fixtures"). What is wrong is the
  coverage record: "Graded by `c-2-2` alone, and that is the whole point" is true
  for the empty cut and false for the wrongly-filled one, and `c-2-1`'s `cuts` list
  does not name `cut-calls-ahead`, so nothing on disk records that `c-2-1` is the
  only thing holding the ordering rule. If a later round ever trims `c-2-1` on the
  strength of that sentence, the ordering becomes ungraded and no checker notices.
  Nothing downstream reads the spec's own prose about its coverage.
- **Suggested wording:** replace the sentence with "dropping the direction filter
  moves `overtake`'s tick-2 row (`c-2-2`); dropping the distance ordering moves
  `both-sides`' first target (`c-2-1`), which is the only place `ahead` ever holds
  two calls."

### W4 - `step` is forbidden to move by `Math.sign(target - floor)`, and no criterion can tell
- **Where:** spec.md, `step`'s `moving` case and `cut-step-move`'s hint; c-2-2 and `cut-dispatch-target`
- **Owner:** nothing
- **The line:** "`step` must not derive its movement from `Math.sign(car.target - car.floor)`, because that makes `direction` a decorative field on the row instead of the value the simulation runs on."
- **Partial re-raise of round 1's B2, deliberately de-escalated.** B2 was blocking /
  `nothing`; `why.md` prescribed two fixes - pin the tick-5 `down` row on `c-2-2`
  and state that `step` advances by `car.direction` - and both were applied. The
  half that is fixed is the important one: the `direction` *value* is now asserted,
  so `direction: 'up'` unconditionally is red. This finding is only the residual,
  and I am filing it as worth a look rather than blocking precisely because the
  round-1 remedy was carried out as written. No escalation is claimed.
- **Reading one:** the prohibition is graded, as the neighbouring sentence implies -
  "which is what `c-2-2`'s tick-5 row grades".
- **Reading two:** the tick-5 row grades `cut-dispatch-target`'s `direction`, not
  `step`'s mechanism. A student who fills `cut-step-move` with
  `Math.sign(car.target - car.floor)` and fills `cut-dispatch-target` correctly
  reproduces every pinned trace exactly, tick-5 row included, and passes all twelve
  criteria while shipping a `step` that ignores `car.direction`.
- **Why it matters:** it is `lessons.md`'s most frequent Gate 1 class - a rule the
  spec states that no criterion grades - and the rule is the stated teaching point
  of session 1's heaviest cut. The blast radius is bounded: a wrong `direction`
  from `cut-dispatch-target` is still red on `c-2-2` under either mechanism, so no
  *grading* hole opens, and the two implementations agree on every fixture, which
  is also exactly why `test-runner` and `skeleton-check` cannot separate them. I
  considered `code-check` and rejected it - see the preamble.
- **Suggested wording:** either accept it and say so ("no criterion distinguishes
  the two mechanisms; the prohibition is a teaching rule for the guide"), or give
  one scenario a car whose `direction` and `target` disagree so the two answers
  differ - which costs a fixture and a criterion, so accepting it is probably right.

### W5 - `maxTicks` is unvalidated, and the claim that it "bounds the run either way" does not hold for a non-number
- **Where:** spec.md, Endpoints, the validation paragraph; `ep-simulate`; c-2-5
- **Owner:** nothing
- **The line:** "Nothing else is validated: `start` is trusted, because no fixture sends a bad one and `maxTicks` bounds the run either way."
- **New to this report, and present in the spec round 1 read.** This sentence is
  unchanged from round 1, which did not raise it - so "there all along and missed",
  not "new this round".
- **Reading one:** the shipped-written predicate deliberately checks only
  `scenario`, and `maxTicks` needs no check because the bound protects the loop.
- **Reading two:** the bound *is* `maxTicks`. Send `{"scenario": {...},
  "maxTicks": "soon"}` and the sentence's own guarantee is gone: depending on how
  `cut-run-until` was folded, the route either answers an empty trace with
  `complete` false or compares `rows.length` against a `NaN` for ever and never
  answers at all. The same is true of a negative number, which the spec never
  mentions.
- **Why it matters:** it is a stated guarantee that is false, in the one paragraph
  the spec marks "shipped written", and it is the degenerate-bound class
  `lessons.md` counts three times. Nothing downstream sees it: `c-2-5` sends three
  bad *scenario* bodies and no bad `maxTicks`, so `test-runner` never exercises it,
  and `deploy-check` does not POST. The honest cost is low - no fixture and no
  student hits it - which is why it is worth a look and not blocking.
- **Suggested wording:** add to the validation paragraph "`maxTicks` is used only
  when it is a positive integer and defaults to 100 otherwise", which keeps the
  predicate single and makes the sentence true.

### W6 - `cut-dispatch-target`'s `ahead`-empty branch is unreachable
- **Where:** spec.md, the policy rule 4, and `cut-dispatch-target`'s hint
- **Owner:** nothing
- **The line:** "With `ahead` empty it reverses: `target` is the floor in `live` closest to the car, again lower floor on a tie."
- **Carried forward: round 1's W1, recorded in `why.md` as deliberately kept.** Same
  classification, worth a look / `nothing`. The line is unchanged, and I re-checked
  reachability against the *new* seed order because the reorder could have changed
  it: it does not. A car is `moving` only towards the floor of a live call, that
  call stays live and stays ahead until the car lands on it, and on landing the car
  is `doors` and then `idle` - and an `idle` car has `dir === null`, for which
  `ahead` is all of `live`. Both reversals in the pinned traces (`both-sides` tick
  3, `overtake` tick 5) still go through the `dir === null` path.
- **Reading one:** the branch is a live rule the student must get right.
- **Reading two:** the branch never executes, so anything satisfies it.
- **Why it matters:** unchanged from round 1 - about a third of a 7.7-minute cut is
  dead code the student is told to write and no test can correct, and the policy's
  headline ("reverse only when nothing is pending ahead") is never exercised as
  written. If I am wrong about reachability the failure mode is a crash on
  `ahead[0]`, which `test-runner` catches, so the exposure is bounded.
- **Suggested wording:** as round 1 - either delete the fallback and say that
  `ahead` is non-empty whenever rules 1 and 2 did not return, or start one
  scenario's car `moving` so the branch is reachable and grade it.

### W7 - the skeleton keeps three locals whose only readers are inside the cuts
- **Where:** spec.md, both Marker placement blocks; `cut-step-move`, `cut-step-doors`, `cut-calls-ahead`, `cut-dispatch-target`
- **Owner:** typecheck
- **The line:** "if (state.car.mode === 'moving') { const car = state.car; <cut-step-move> }"
- **Carried forward: round 1's W5, recorded in `why.md` as deliberately kept.** Same
  classification, worth a look / `typecheck`. Both marker blocks are byte-identical
  to the spec round 1 read.
- **Reading one:** the marker layout is fine - the `return` sits outside every pair
  in all three functions, which it does.
- **Reading two:** the generated skeleton declares `const car` twice in `step` and
  `const dir` in `nextTarget` with every reader removed, plus `let ahead` assigned
  once and never read. On a tsconfig with `noUnusedLocals` that is TS6133 on three
  declarations and the student's tree does not compile - the TS2355 outcome arriving
  from a different rule.
- **Why it matters:** contingent on the tsconfig the Builder generates, which is why
  it is not blocking. The owner is honest but fail-open: `typecheck` reports no
  error when the toolchain cannot be reached, so this can land in the student
  skeleton with every gate green. Gate 1 should keep it under `verify_later` and
  someone must read `typecheck_fail_open` in `skeleton-results.json` at step 8.
- **Suggested wording:** state that the cut bodies read `state.car` and
  `state.pending` directly, so no narrowing local sits outside a marker pair; or
  state that the skeleton's tsconfig leaves `noUnusedLocals` off.

### W8 - `cut-step-doors` is graded by one criterion on one served call
- **Where:** spec.md, Session 1, `cut-step-doors`, c-1-5
- **Owner:** nothing
- **The line:** "Graded by `c-1-5` alone - the only criterion that reads `served-6` and `served-count`."
- **Carried forward: round 1's W2, recorded in `why.md` as deliberately kept.** Same
  classification, worth a look / `nothing`. Line unchanged, no new evidence.
- **Reading one:** the student writes the serve-and-close transition.
- **Reading two:** the student writes a literal `served: [{ floor: 6, calledAt: 0,
  servedAt: 4 }]` with `pending: []` - the shape of habit-tracker's
  `cut-week-dates` lesson - because all three numbers are printed in the criterion.
- **Why it matters:** unchanged. It stays worth a look because the full suite does
  separate the literal: `c-2-1`, `c-2-2`, `c-2-3` and `c-2-6` fold `step` through
  `runUntil` on different floors and different `servedAt` values. What ships is a
  session 1 a student can sign off on with a constant, and spec.json's session-2
  `cuts` lists do not record that this is what covers it.
- **Suggested wording:** as round 1 - give `c-1-5` a second observation, or state
  that `cut-step-doors` is graded within session 1 by one fixture and regraded by
  the session-2 criteria.

### W9 - `maxTicks` reached and the run completing on the same row
- **Where:** spec.md, `runUntil`, and `cut-run-until`'s hint; c-2-4, c-2-6
- **Owner:** nothing
- **The line:** "The run ends **complete** on a dispatched car that is `idle` with `pending` empty, with that final row appended. It ends **incomplete** the moment `trace.rows` reaches `maxTicks`."
- **Carried forward: round 1's W3, recorded in `why.md` as deliberately kept.** Same
  classification, worth a look / `nothing`. Line unchanged.
- **Reading one:** the completion test wins, so `quiet` with `maxTicks` 1 answers one
  row and `complete` true.
- **Reading two:** the bound wins, and the same call answers `complete` false.
- **Why it matters:** unchanged - `maxTicks` defaults to 100 and `c-2-4` stops
  `both-sides` five rows short of its natural end, so no criterion reaches the tick
  where the two conditions coincide, and both readings are green everywhere. I also
  checked the sibling question the same line raises - whether `step` runs after the
  row that hits the bound - and it is unobservable too: `both-sides` serves nothing
  between the fourth row and the fifth state, so `trace.served` is the same either
  way and `c-2-4` does not assert it.
- **Suggested wording:** as round 1 - "a row that both completes the run and reaches
  `maxTicks` is `complete` true; the bound only reports a run that had further to
  go".

### W10 - two stated display rules that no criterion grades
- **Where:** spec.md, Screens table (`floor-1` .. `floor-8`, `tick`); c-1-2, c-1-6
- **Owner:** nothing
- **The line:** "one row per floor, floor 8 at the top down to floor 1 | `floor-1` .. `floor-8` | the floor number"
- **Carried forward: round 1's W4, recorded in `why.md` as deliberately kept.** Same
  classification, worth a look / `nothing`. Both the table row and the criteria are
  unchanged.
- **Reading one:** the shaft renders floor 8 first in the DOM.
- **Reading two:** it renders floor 1 first. `c-1-2` asserts only that eight
  elements with those testids exist, so an upside-down lift is green.
- **Why it matters:** unchanged, and the same gap covers the `tick` readout -
  `c-1-2` pins it at `0`, no criterion reads it again, and `c-1-6` clicks three
  times without asserting it, so a page whose tick display never advances passes.
  Both belong to shipped-written markup, so no student types them; no checker reads
  DOM order or an unasserted element.
- **Suggested wording:** as round 1 - add "with `floor-8` appearing before `floor-1`
  in document order" to `c-1-2`, and "and the exact text `3` in `tick`" to `c-1-6`.

### W11 - the idea's payoff is a visible trace; the spec ships JSON only
- **Where:** idea.md Theme and session 2 "Runs"; spec.md Out of scope, `ep-simulate`
- **Owner:** pack-writer
- **The line:** "A trace screen. The session-2 trace is JSON from `POST /api/scenarios/simulate`; rendering it would cost a second screen build that session 2 has no minutes for."
- **Carried forward: round 1's W6, recorded in `why.md` as deliberately kept.** Same
  classification, worth a look / `pack-writer`. Line unchanged.
- **Reading one:** the trace is a machine artifact and the tests are what read it.
- **Reading two:** the trace is why the project is worth two sessions - the idea says
  "the policy is arguable and the trace makes the argument visible", and the spec's
  own closing section leans on the same claim.
- **Why it matters:** the drift is declared and its reason - minutes - is the right
  one, so this is not a scope complaint. But session 2 still ends with a student
  reading a JSON body from a POST they construct by hand, and nothing in the spec
  says how, which lands on the Pack Writer at step 9 and is read by a person at
  Gate 3.
- **Suggested wording:** as round 1 - name in session 2 the exact request the guide
  will have the student send and where its answer is read.

### W12 - session load: the estimate is low on exactly this shape, and session 1 sits outside W114's reach
- **Where:** spec.md, Session load; `cut-step-move`; lint.json session_minutes
- **Owner:** pack-writer
- **The line:** "Session 1's heaviest, `cut-step-move` at 8.3 of 14.3 cut minutes, is 58% - the 45% cap is not applied to a two-cut session, because two cuts always split at least 50/50, so read that number rather than the absent warning."
- **Carried forward: round 1's W7, and partly addressed.** Same classification, worth
  a look / `pack-writer`. The line I quote is new: the spec now discloses session
  1's share itself and explains why `W114` cannot fire on a two-cut session, which
  is what round 1 asked for. The numbers moved with the rewritten `cut-step-move`
  hint - session 1 is 39.3 minutes and `largest_cut_share` 0.58, and `lint.json`
  agrees exactly (39.3 / 36.5, 0.58 / 0.38). Nothing here contradicts round 1; the
  finding stays open because disclosure is not a fix.
- **Reading one:** both sessions fit - 39.3 and 36.5 against a 40 minute cap, no
  linter warning.
- **Reading two:** 39.3 is 0.7 minutes of headroom on a model `lessons.md` records
  as 5 to 13 minutes low on every flow-2 session ever timed, in the session that
  also carries the whole project setup, with its heaviest cut at 58% of its cut
  minutes and the share check structurally unable to fire.
- **Why it matters:** six consecutive projects have overrun a 40 minute cap and
  `lessons.md` puts the cause in one place - a single cut with several ordered rules
  in it. `cut-step-move`'s hint now states three outcomes (advance along
  `car.direction`, land on `car.target`, stop short) plus a preservation rule and a
  prohibition, which is the `cut-parse-line` shape the model reads low. The spec is
  honest about all of this and both drop candidates are real blocks a student types,
  which is the trap `lessons.md` records for pipeline-test-03. Nothing before the
  step 13 dry run measures teaching time, so the last owner that can act is the
  Pack Writer at step 9, and it can only disclose.
- **Suggested wording:** none needed for the numbers, which match `lint.json`. If
  anything moves, split `cut-step-move` so the landing case and the stopping-short
  case are stated as one rule each.
