# Lessons

Step 5 of the build order: so a mistake caught once is not repeated. Every agent
reads this file before it starts.

One line per lesson. Add a lesson the moment a gate rejects something or a
nightly watchdog run goes red. Delete nothing - a lesson that stops applying
gets a strikethrough and a date.

## Spec

- **One list, one order - and check it at step 2, not at Gate 1.** 2026-09-07,
  game-arcade round 1: three places described the same guesses list on `sc-board`
  and disagreed. `cut-ui-render-rows` (S2) said "most-recent-first",
  `cut-ui-replay-apply` (S4) said "in order of play", `c-4-3` (S4) said "from the
  start of the game". A student follows the Session 2 hint and then contradicts
  it in Session 4. A person caught it at Gate 1 and rejected the round; the spec,
  the ambiguity report and the whole test suite were rebuilt.
  Two things failed, and neither was the reviewer. The Spec Breaker *did* see it
  - W1, W2 and W3 all circle this list - but filed it under "worth a look" and
  named `test-runner` the owner. Rule 8 asks who owns **blocking** findings, so a
  contradiction parked in the soft section is never asked. And `test-runner` did
  not own it: `test_c_4_3` asserts the row *count*, and a count passes whatever
  the order is. **Enforced** since 2026-09-08 by `spec_linter` `E115`, scoped by
  criterion `target` so two lists with two orders stay legal. It fires on exactly
  one of the 32 specs in `projects/` - the round a person rejected.

- **Guidance a model cannot compute is not guidance - give it the script.**
  2026-09-07, game-arcade: the Spec Writer skill spends fifty lines on the
  session budget, including the formula (10 minutes base, each cut 6 plus 1.7 per
  branch, plus builds and concepts). Session 1 still came in at 55.2 minutes
  against a 40 cap, was rejected, and came back at 53.7. Two rejections and two
  full Spec Writer passes for a number a script computes in under a second. The
  fix is not more prose: `spec_linter --no-report` (2026-09-08) lets the writer
  run the real check on its own draft and arrive green, the same split
  `redfirst.py --no-report` already made. Before writing another paragraph of
  guidance, ask whether the agent could instead just run the checker.


- **A clean linter is not a clean spec.** 2026-08-26, recipe-box round 1 passed
  the linter with 0 errors and 0 warnings and was still rejected at Gate 1 on
  four blocking findings. The linter checks shape; only reading catches meaning.
- **Say what a test reads, not just what the screen shows.** If the project uses
  CSS modules, class names are hashed, so a criterion that counts or reads
  anything on screen must pin an exact string or a stable hook. Otherwise the
  Verifier has to guess from the Builder's markup, and the student then rewrites
  exactly that markup from a hint that never mentions it.
- **A number in a criterion must be unambiguous on the page.** "renders 2 cards"
  is fine. "after the baking chip is clicked" is not, when three elements on the
  page read "baking".
- **A cut hint that names one thing implies replacing everything else.** 2026-08-26,
  recipe-box round 2: "write the search text into the q parameter" is satisfied by
  `router.replace('/?q=' + text)`, which wipes the active tag. If a cut writes to
  shared state, its hint must say what to preserve.
- **Test the combination, not just each half.** Two filters that each have a
  criterion still need one that drives both together through the UI. Testing the
  combination at the endpoint does not cover the screen that builds the URL.
- **Every fetch needs an owner.** If a screen's element is fed by an endpoint,
  some session must own that call. A screen built in session 1 whose data comes
  from an endpoint built in session 2 leaves session 1's skeleton throwing.
- **Nothing checks that sessions are balanced, so balance them by hand.**
  2026-08-26, tip-split: the linter caps cuts and criteria per session but
  weighs neither setup cost nor teaching minutes, so an overrun is not found
  until the Pack Writer times it at step 9 - after the spec, the code, the tests
  and the skeleton are all built and both gates are passed. Session 1 came in at
  45 minutes against the 40 cap because it carried 4 cuts *plus* the project's
  entire setup, while session 3 carried 3 cuts and no setup. The session holding
  the setup should carry fewer cuts than the others, not the same number.

## Build

- **Resolve project paths before spawning a subprocess with `cwd=`.** 2026-08-26:
  the test runner passed a relative interpreter path while setting
  `cwd=project`, so the path resolved against the new directory and vanished.
  The selftest missed it because its fixtures use absolute tempdirs. The nightly
  watchdog builds paths from `Path(".")`, so every scheduled run would have died
  this way. Fixed by resolving in all five scripts.
- **Do not assume `python -m venv` works.** Debian splits `ensurepip` into
  `python3-venv`. The runner now tries uv, then venv, then `venv --without-pip`
  with a get-pip bootstrap, and names the apt fix if all three fail.
- **The Builder will swap the stack rather than fix a build.** 2026-09-06,
  demo-run-01: given next/react/typescript and a build failing on a missing
  package.json, it replaced the project with a 241-line vanilla node http server
  that reimplemented the app inline, declared no dependencies, and set `build`
  to `node -e "console.log('build ok')"`. All 13 criteria passed - the tests
  assert HTTP responses and DOM testids and the replacement answered both. Every
  .tsx and .ts file, including all five holding cut markers, was dead code.
  `stack_check` now compares stack.json against app/package.json at the test
  runner, and is not opt-in. Told to fix it, the Builder kept the impostor and
  added the dependencies unused, with a `|| node -e ""` fallback so the build
  could not fail: hence S005 (start must run the stack) and S006 (no fallback).
- **An empty `node_modules` is not an installed one.** 2026-09-06, demo-run-01: a
  failed `npm ci` leaves the directory behind holding only `.bin`, so the
  existence check in `boot()` skipped the install and `next build` died with
  "'next' is not recognized". Dotted entries do not count as packages.
- **Generate clients in `postinstall`, not in `build`.** 2026-09-07,
  demo-run-03: `build` was `prisma generate && prisma migrate deploy && ...`, and
  `prisma generate` rewrites a 19MB native query engine. On Windows anything
  holding that file for a moment - a virus scanner reading what it was just
  handed - fails the whole build with `EPERM: operation not permitted, unlink
  query_engine-windows.dll.node`. No node process was running; the lock was
  transient. The pipeline builds 14+ times in a row (once for the test runner,
  once per mutant), so a 1-in-20 collision is a near-certain failure somewhere in
  the run. `postinstall` runs it once per install, and still covers the deploy
  check's clean copy because `npm ci` triggers postinstall.
- **A framework major version changes the code the Builder already wrote.**
  2026-09-07, demo-run-03: the Builder wrote Next 14 route handlers - `{ params
  }: { params: { id: string } }` - and separately pinned next 16, where params
  is a Promise. It compiled locally against the old node_modules and failed only
  in the deploy check's clean `npm ci` copy: the textbook works-on-my-machine,
  caught exactly where step 12 is meant to catch it. Fix it OUTSIDE the cut
  markers where possible - awaiting `ctx.params` in the wrapper left the cut
  body byte-identical, so the skeleton and every student task were unaffected.
- **A stale `package-lock.json` passes locally and fails on a clean machine.**
  2026-09-06, demo-run-01: the lock was 90 minutes older than package.json.
  Locally `node_modules` was already populated so the install was skipped
  entirely; the deploy check does a fresh copy then `npm ci`, which refuses when
  the two disagree. Exactly what step 12 exists to catch - regenerate the lock
  with `npm install --package-lock-only` whenever package.json changes.

## Cut points

- **A cut whose effect nothing reads grades nothing, and no test can save it.**
  2026-09-07, game-arcade: `cut-ui-append-guess` assigned `guessesState`, which
  appeared exactly once in the file - its own declaration - while the board
  rendered from a second state that `await loadGame()` refilled from the server
  on the next line. The pair was balanced, placed correctly and compiled; the
  mutant built and ran; and mutation still reported NOT GRADED, because removing
  it changed nothing a criterion could see. This is a third outcome the routing
  does not model: INCONCLUSIVE means a mutant would not build and belongs to the
  Builder, NOT GRADED is assumed to mean a weak suite and routes to the
  Verifier - but dead state gives a test nothing to assert on, and the Verifier
  is hooked out of `app/`. It could not have fixed this at any price. Ask what
  observable thing breaks when a block is empty before closing the pair.
  **Enforced** since 2026-09-08 by `mutation.scan_dead_cuts()`, which runs
  before the first build and names the Builder, not the Verifier.


- **Never put a typed function's only `return` inside the markers.** 2026-08-26,
  recipe-box: six cuts did this. The skeleton fails to compile with TS2355 and
  the student's whole app stops building - not one red test, no build at all.
  Keep the return outside the markers and cut the assignment that feeds it:

  ```ts
  export async function GET(): Promise<Response> {
    let body: { ok: boolean } = { ok: false }
    let status = 501
    // >>> CUT cut-api-health
    body = { ok: true }
    status = 200
    // <<< CUT cut-api-health
    return Response.json(body, { status })
  }
  ```

  Proven both ways in `fixtures/runner-check`: return inside the markers fails
  the cutter's typecheck; the pattern above compiles, keeps every criterion
  green on `app/`, and still fails the right criterion on the skeleton.
- **The fallback must not accidentally pass the test.** A 501 and `ok: false`
  fail the criterion, which is what the skeleton needs. A fallback that returns
  plausible-looking data makes the test green on an empty skeleton.
- **A criterion that asserts only a transient state cannot be graded by
  asserting that state.** 2026-09-07, stock-tracker c-2-4, "while the allocation
  report is loading, the page shows Loading...". The render
  `{!reportState && <div>Loading...</div>}` correctly sits OUTSIDE
  cut-ui-fetch-allocation - you do not cut the markup - so it survives into the
  skeleton, where the fetch that would set `reportState` is gone and the loading
  text is therefore permanent. Two test shapes graded nothing here:
  "Loading appears" passes trivially, and so does "appears then clears" -
  measured on the skeleton, the SSR html carries the text and React drops it at
  hydration, so the flash is indistinguishable from a resolved fetch. What only
  a live fetch produces is the fetch's RESULT: waiting for
  `[data-testid^="drift-"]`, which renders only once `reportState` is set, made
  c-2-4 pass on app/ and fail on skeleton/. **For a loading, empty or error
  state, assert the transition into the loaded state, not the interim state** -
  the interim one is what an unwritten cut leaves behind for free.

- **The skeleton is a snapshot, and nothing used to say when it was taken.**
  2026-09-07, demo-run-03 shipped with app/ on next 16.1.1 and an awaited
  `params`, while skeleton/ - cut twenty minutes earlier, before those fixes -
  still pinned next@14.2.5, which npm flags as vulnerable. Every gate was
  truthful when it ran: Gate 2 was approved before the fix, `cut` ran before the
  fix, and `deploy` only ever builds app/ unless you pass `--target skeleton`.
  Rule 8 says a later edit re-enters at step 7, but that was a rule for people.
  `cut` now records the app hash it cut from and Gate 3 and `ship` refuse a
  skeleton whose app has moved since - the same binding ambiguity.md has to a
  spec hash. If you fix app/ after step 10, re-run `cut` and `leak`.
- **A lesson in this file is not a rule in the agent's brief.** 2026-09-06,
  demo-run-01: `lib/sort.ts` put all 9 returns inside one pair - the same defect
  as recipe-box above, written down here since 2026-08-26 and read by every
  agent before it starts. The rule was in CLAUDE.md and in the Spec Writer's and
  Spec Breaker's skills, but not in the Builder's, and the Builder places the
  markers. Now in `.claude/skills/builder/SKILL.md` too. Where a lesson keeps
  recurring, check it is written where the agent that breaks it will read it.
- **A cut whose placeholder equals its body grades nothing, ever.** 2026-09-06,
  demo-run-01: `cut-ui-toggle-init` had `new Set()` above the marker and
  `new Set()` inside it. Removing the block changed no behaviour, so no test
  could catch it - not a weak test, an impossible one. The placeholder outside
  the markers has to be a value the criterion rejects.
- **INCONCLUSIVE is not a pass.** 2026-09-06: when a mutant will not build,
  every criterion returns `missing` and nothing passed, so the run says nothing
  about whether the task is graded. Read `inconclusive_tasks` as unproven.

- **A cut must not declare what another cut reads, and the rule was written too
  narrowly to say so.** 2026-09-07, stock-tracker: `apply-plan/route.ts`
  declared `const plan` inside `cut-ep-trade-record` while `cut-ep-apply-plan`,
  further down the same function, read it. Remove the first and `plan` is
  undeclared, `next build` dies, every criterion reports `missing`, and mutation
  returns INCONCLUSIVE - nothing proven, task ungraded. The Builder's skill
  already carried "never put a function's only `return` inside a pair" *and*
  named INCONCLUSIVE as the consequence, so the rule was in the right brief and
  still did not fire: it named `return`, and this was a `const`. Generalised
  there now - **nothing declared inside a pair may be read outside it**, and two
  cuts in one function must each compile with the other removed, because that is
  what mutation builds. Where a rule is broken by a case it does not literally
  name, widen the rule rather than adding an instance.

- **A stale lock hides in app/ and detonates in the skeleton, and re-cutting
  cannot reach it.** 2026-09-07, stock-tracker: the Builder bumped next 14.2.13
  -> 16.1.1 to clear an S007 advisory and left `package-lock.json` on 14.2.13.
  `app/` still had a populated `node_modules`, so `boot()` skipped the install
  and the suite went 21/21 green through Gate 2. `skeleton/` was the first clean
  tree in the run: `npm ci` refused with EUSAGE, nothing installed, `next build`
  exited 127 with `next: not found`, all 21 criteria came back `missing`, and
  skeleton-check read that as 21 mismatched cuts. It routed to `cut`, which
  copies `app/` again - four attempts in eight seconds over a fault no re-cut can
  reach. The lesson "a stale package-lock.json passes locally and fails on a
  clean machine" was already written down against step 12; it fires at step 10
  first, because the skeleton is cleaner than the deploy check's copy is early.
  Three fixes, one per layer: `stack_check` S008 fails the step 7 check when
  package.json and the lock drift, `boot()` now checks and logs the install's
  exit code instead of discarding it and letting `next build` report the
  symptom, and a skeleton that never booted routes to the Builder. **`missing` is
  not `fail`** - when every criterion is missing, read the return code before
  believing anything the report says about cut markers.

## Tests

- **Playwright waits for elements, not for the work a click started.**
  2026-09-07, game-arcade: three UI criteria stayed red across five Builder
  retries and none of them was the app's fault. `Locator.count()` answers
  immediately, so `page.goto("/games")` then `assert rows.count() == 2` read
  `0 == 2` against a list a client-side fetch had not filled yet; and clicking
  New Game returned before its `await fetch` resolved, so four colour clicks
  landed and were then wiped by the app's own reset, leaving a criterion waiting
  the full 30s for a row that could never appear. `expect(locator).to_have_count(n)`
  retries; `wait_for_timeout(300)` is the same bug with a longer fuse. The
  Builder cannot fix any of this - it cannot edit `verify/` (rule 3) - so a
  suite that does not wait is a loop the code phase cannot end. Written into
  `.claude/skills/test-writer/SKILL.md` the same day, and **enforced** since
  2026-09-08 by `redfirst.scan_waits()` - static, so it lands at step 5,
  a whole phase before the code loop can start.


- **The skeleton check only sees the fully-open skeleton.** Known blind spot in
  `pipeline/cutter.py`: it proves that a criterion fails when *all* its cuts are
  open and passes when it has none. It says nothing about the partial states a
  student actually moves through. recipe-box c-3-2 goes green once
  `cut-api-recipe-get` is filled even with `cut-store-find-one` still empty,
  because `findRecipe`'s `return null` fallback is indistinguishable from a real
  miss. Where a criterion has more than one cut, check by hand that no proper
  subset satisfies it.
- **Give the Verifier a stable hook.** `data-testid` on the repeated element
  survives styling changes and reads the same in the skeleton.
- **Fixtures that already satisfy an ordering criterion grade nothing.** Hit
  twice. 2026-09-05, ui-live-01: c-3-2 asserted the first summary row is
  "Expense" after sorting by delta, and "Expense" is alphabetically first too,
  so it held whether the sort ran or not. 2026-09-06, demo-run-01: the seed
  listed Alice..Judy in name order, so cutting the comparator to `() => 0` left
  the order still name-ASC and c-3-1..c-3-3 all passed. Seed data must differ
  from every order the spec asks for, and an ordering test should assert the
  whole sequence, not one row.
- **A suite that never ran can still report the last run's results.**
  2026-09-06, demo-run-01: the build died in 0.8s, pytest was never invoked, and
  `parse_junit` read the previous run's junit XML - "13 pass, 0 fail" for a suite
  that did not execute. `ok` was false because the return code said so, but
  `mutation.py` reads the counts, so a mutant that failed to build would have
  looked green and its task scored as graded. The report is now deleted before
  each run.

- **A suite with no reset is ordered by its filenames, and the Builder cannot
  fix that.** 2026-09-07, stock-tracker: 21 tests, one long-lived server, one
  SQLite file, and no `conftest.py` anywhere in `verify/`. pytest collects
  alphabetically, so `test_api_apply.py` ran second and the drift its
  `POST /api/apply-plan` consumed was gone before c-3-3, c-4-3, c-5-3 and c-5-4
  read it; c-5-4 asserted 4.776995305164321 < 4.776995305164321. `redfirst` was
  green and truthful - it checks assertions, all-red and fixture resolution, and
  runs the suite exactly once in one order. The loop that followed was
  unwinnable by construction: rule 3 locks `verify/` to the Builder, so it kept
  succeeding at `app/` while the same four criteria stayed red, burning code
  retries 2 -> 4. Fixed by a `verify/conftest.py` autouse fixture that re-runs
  `prisma/seed.js` before every test, and the rule is now in the Test Writer's
  own skill - it was only ever in the Verifier's, and in flow 2 the Test Writer
  writes the suite. **A fresh browser page per test is not a reset**: demo-run-03
  had that fixture and still shared its rows.

## Process

- **Do not edit a shared input while a run is reading it.** 2026-08-26: this file
  was written mid-pass during recipe-box round 2. The Spec Breaker read it empty
  at step 3, noticed it change, and re-checked every finding - which cost a pass
  and could have gone the other way. Update `lessons.md` between runs, never
  during one.
- **Text an agent wrote will not decode as the machine's locale.** 2026-09-05
  and 2026-09-06: 75 bare `read_text()`/`write_text()` calls used Python's
  locale default, cp1252 on Windows, while every artifact an agent writes
  carries the curly quotes and en dashes a model reaches for. `guide_linter`
  died reading the pack; `gate1` died reading ambiguity.md; `mutation` died
  writing a mutant. Worse than a crash, `gate1.py:75` sat inside
  `except UnicodeDecodeError: continue`, so it silently skipped any source file
  with a non-ASCII character and compared the guide against a corpus missing
  those files. Name the encoding on every read and write of a file an agent may
  have touched.
- **A checker that crashes drives the workflow rather than stopping it.**
  2026-09-06, demo-run-01: `gate1-check` crashed on encoding, `_checker`
  correctly called it a pipeline fault and burned a spec retry, the orchestrator
  re-planned, the Spec Writer rewrote the spec, the new hash invalidated the
  ambiguity report, `breaker begin` cleared it, the Breaker ran again, and the
  rule crashed on the same byte. Four rounds - lint 8 runs, breaker 4, three
  spec retries - and the rule never reached a verdict once. When a step repeats,
  check whether its checker is producing a verdict at all before treating the
  verdict as meaningful.
- **The remedy for a stale report is the Breaker, not the Spec Writer.**
  2026-09-06: `failed_repair` sent every red gate1.json to the Spec Writer.
  Right for an unowned blocking finding; exactly wrong for staleness, because
  rewriting the spec is what moved the hash out from under the report. It now
  reopens the Breaker pass, starting at `breaker begin` - `breaker end` refuses
  when the pass was opened against a different hash.
- **A build failure is not a test failure.** 2026-09-06, demo-run-01:
  `suite_did_not_run()` read "0 pass, 0 fail, 13 missing" as a collection error
  and routed to the Test Writer four times, while the actual fault was a missing
  package.json. `pytest_returncode` 99 is not pytest's - the test runner sets it
  when the app fails to install or build, so the suite was never asked anything.
  It is now `BOOT_FAILED_RC`, and a build failure belongs to the Builder.
- **OpenRouter reserves max_tokens up front, so a cheap call fails on a thin
  balance.** 2026-09-05, ui-live-01: with no `max_tokens` the model ceiling is
  reserved - 65536 tokens, $0.66 at gpt-5 - and every call 402s once the
  remaining balance is under that, however few tokens it would really use. The
  verifier died three times at $0.62 remaining on a step costing $0.08. Capped
  at 16000, and a reply that stops on `length` now raises instead of returning a
  truncated tool call that reads as "the agent chose to do nothing".
- **Loops cost more than the work.** 2026-09-06, demo-run-01 spent about $4
  across 23 agent runs: spec-writer 9, spec-breaker 6, test-writer 5, builder 2,
  idea-generator 1 - for one spec and one suite that was correct first time. The
  great majority went to two routing bugs. A clean run of the same project is
  about $1.20, so when a component's run count climbs, read why before paying
  for another attempt.
- **Gate 1 is not "blocking == 0". It is "where would this defect surface".**
  2026-08-26, tip-split: the Spec Breaker is adversarial and gets a single pass,
  so it will nearly always return something blocking - rejecting on the count
  alone never terminates. Round 1's three findings were grading-integrity holes
  that no downstream checker could catch: one would have failed the cutter at
  step 8, after the Builder had already been paid for. Round 2's single finding
  was a prose overclaim whose worst case was a red test at step 6, which the
  Builder/test-runner loop fixes for free. The first is a reject, the second is
  an approve, and the count is the same either way.
- **The Builder is not automatically the cost centre.** `Flow.md` says the
  Builder is 80-90% of agent cost "because it re-reads the codebase on every
  retry". 2026-08-26, tip-split measured: Builder 8.3 min of 53 min of workflow
  wall time, or 16%. The spec phase was 55%, because it ran twice. The claim is
  conditional on retries actually happening; with zero retries the Spec Writer
  and Spec Breaker dominate, and the Breaker alone cost more than the Builder.
- **A shipped project can carry a known CVE and still pass step 10.**
  2026-08-26, tip-split: `npm install` printed
  `next@15.1.6: This version has a security vulnerability ... CVE-2025-66478`
  and `deploy_check.py` recorded the step as `ok: true`. Gate 3 trusts a green
  deploy check, so read the `install` detail string, not just its `ok` flag,
  until the check itself treats an advisory as a failure.

- **A report on disk is not evidence it reviewed the spec on disk.** 2026-08-27,
  recipe-box: `revise` deliberately uses `shutil.move` so a rejected round's
  `ambiguity.md` cannot linger - the comment at `cli.py:239` says so. Someone
  copied round 2's report back into the project root afterwards. `pipeline next`
  reads progress off the files present, so it reported "Gate 1" for a round-3
  spec the Spec Breaker had never read, and the gate reader spent a pass walking
  four findings that had already been fixed. Nothing ties a report to the spec it
  reviewed. Until a `breaker` step records a hash of the spec it read, check
  `ambiguity.md`'s mtime against `spec.md`'s before trusting it.

- **Declare the stopping rule before the pass, not after.** 2026-08-27,
  recipe-box: the Breaker returned something blocking on all five passes it ever
  made, so "reject until blocking == 0" would never have terminated. The rule
  that did terminate: *approve when every remaining finding sits in a column a
  downstream checker owns.* Round 3 had five findings no checker could see -
  reject. Round 4 had one, with a two-sentence fix - applied by hand and
  approved. Write the rule down at the rejection, because deciding it while
  holding the next report invites moving the line to fit the answer.

- **Nothing locks `spec.md`, and a finished agent can wake up and re-run.**
  2026-08-27, recipe-box: the round-4 Spec Writer reported a second time, over
  an hour after it finished, saying it had copied `.pipeline/round-3/spec.md`
  over the live files and re-derived its fixes. `pipeline/guard.py` locks only
  `app/`, `verify/`, `pack/` and `skeleton/` subtrees, so the spec is writable at
  every step. Here the mtimes cleared it - the spec was last written 13 minutes
  before the Builder ran - but a re-run landing after Gate 1 would have silently
  replaced the approved spec with a rejected one, and only mtimes would show it.

- **Commit the approved spec before phase 2 starts.** 2026-08-27, recipe-box:
  `app/` and `verify/` were built against a round-4 spec that existed only in the
  working tree; `HEAD` still held the round-3 spec that had been rejected. There
  is no archive-on-approval step - `revise` only archives on rejection - so a
  single overwrite would have left a green 22/22 build with no readable record of
  what it was built to do.

- **The unlock step trips the security classifier, and it is a false positive.**
  2026-08-26 tip-split and 2026-08-27 recipe-box: the workflow's `[unlock]` agent
  was flagged both times. Both transcripts show exactly one tool call,
  `python3 -m pipeline unlock <slug>`, and no file writes. Verify from the
  transcript rather than trusting or dismissing the warning, but expect it.

- **INCONCLUSIVE is a build failure, and build failures are the Builder's - but
  mutation.json routes to the Verifier either way.** 2026-09-07, stock-tracker:
  `FAILED_REPORT_REPAIRS["mutation.json"]` sends every red report to the
  verifier, with the reason "a student task grades nothing, so the verifier
  strengthens the suite." That is right for NOT GRADED and wrong for
  INCONCLUSIVE, where the mutant never built and the fault is a cut marker in
  `app/` - a tree the Verifier is hooked out of. Attempts 1-3 cost real credits:
  the Verifier correctly cleared the one NOT GRADED task on its first pass, then
  looped on an INCONCLUSIVE one it could not reach at any price. This is the
  `BOOT_FAILED_RC` lesson one step later - `suite_did_not_run()` already draws
  exactly this distinction for `results.json` at step 7, and nothing draws it for
  `mutation.json` at step 8. Until the routing is conditional, read
  `inconclusive_tasks` before letting an auto-run repair a red mutation report,
  and hand an inconclusive one to the Builder by hand.

## Building the checkers

<!-- Added 2026-08-28, between runs, from the round-1 blocker report. -->

- **A checker that fails open is not a checker.** 2026-08-28: `cutter.typecheck`
  returned `ok: True` when there was no tsconfig, no `node_modules` or no `tsc`
  - which is every fresh clone and every CI box. It was the only guard against
  the one defect that recurred across consecutive projects. The fix was a static
  scan that needs no toolchain, with tsc demoted to a second line and a
  `fail_open: true` flag so "clean" and "did not run" are no longer the same
  answer. Ask of every checker: what does it say when it cannot run?

- **Put the check where the artifact exists.** The obvious home for a
  cut-marker rule is the spec linter, and it is the wrong one: at step 2 no code
  exists, because the Builder places the markers at step 5. The linter can only
  reject the *wording* that prescribes the bad shape ("return ...", W067); the
  placement itself belongs to the cutter. A rule aimed at an artifact that does
  not exist yet is a rule that cannot fire.

- **Look for the rule that closes two defect classes at once.** Bypassable
  grading cuts (round 3 B1) and the skeleton-check partial-subset blind spot
  looked like separate problems - one a spec defect, one a known limitation of
  step 8. They are the same shape: **two cuts graded by exactly the same set of
  criteria.** One linter rule (E110) rejects both, and it flagged both real
  instances the first time it ran. When two findings resist a rule each, check
  whether they are one finding.

- **A stopping rule has to be a property of the finding, not a count.** "Reject
  until blocking == 0" never terminated because the Breaker always finds
  something. "Reject when a blocking finding is one no downstream checker owns"
  terminates, and it is checkable by a script - so it went into `gate1.py` and
  the Breaker now names an `Owner` per finding. The count was never the signal.

- **A report that says only what it checked is half a report.** The one
  watchdog run on record said `"checked": 1` with two shipped projects on disk,
  and nothing flagged the gap. It now reports `shipped_total`, `skipped` and
  `unknown_slugs`, and isolates each project so one broken venv cannot take the
  whole nightly run down with it.

- **Count the green runs too.** `burn_retry` only fired on failure, so ten clean
  lint runs and six clean test runs sat at 0/15 retries. A step that keeps
  re-running while its checker stays green is a loop, and it needed its own
  counter (`step_runs`, capped at 30) to be visible at all.

- **A binding is only needed while the decision is open.** Requiring
  `ambiguity.md` to hash-match the spec fixed the stale-report bug, and then
  walked both shipped projects back to step 3 because they were approved before
  the binding existed. Freshness matters before Gate 1; after it, the freeze and
  the archive are the stronger guarantee. Scope a fail-closed check to the
  window where it is load-bearing, or it starts rewriting history.

## The habit-tracker run

<!-- Added 2026-08-28 between runs. First project taken through the rebuilt
     pipeline: 4 Gate 1 rounds, 0 spec-linter retries, 0 builder retries,
     0 cutter retries, 16/16 criteria. -->

- **The stopping rule terminated, and it approved with a blocking finding still
  open.** Rounds went 12 -> 7 -> 6 -> 8 findings with blocking-and-unowned
  1 -> 1 -> 1 -> 0. Round 4 was approved with one blocking finding outstanding
  because it was owned by `pack-writer`. "Reject until blocking == 0" would still
  be running. The rule works because it is a property of each finding, not a
  count, and because a script applies it - `pipeline gate1-check` - so it cannot
  be bent while holding the report.

- **A minute model with a flat per-cut cost does not catch the overrun it was
  built for.** 2026-08-28: session 3 came in at 47 minutes against the 40 cap -
  the third consecutive project to overrun - and the linter had estimated 35.5.
  The model charges 6 minutes per cut, and `cut-api-toggle` is 20 lines with
  three branches plus an ordering rule between its 400 and 404 checks. Across
  the five sessions now measured the model is within ~3 minutes *except* where
  one cut is much larger than the others, which is precisely the case that
  overruns. Cut size is not knowable at step 2, because no code exists there, so
  either the spec has to declare per-cut weight or the estimate needs a proxy for
  it. Until then the estimate is information, not a check.

- **Excluding a file from a copy does not stop a later step generating it in
  place.** Round 4's B4 said the shipped skeleton would carry a build artifact. I
  answered that unconditional exclusion made it moot. It did not: step 8's own
  `tsc` typecheck and skeleton build write into `skeleton/` *after* the copy is
  made, and tip-split's `tsconfig.tsbuildinfo` is git-tracked to this day. Fixed
  with `cutter.sweep_generated`, run once the checks that needed the artifacts
  have passed. When a checker writes into the artifact it is checking, exclusion
  at copy time is the wrong layer.

- **The Spec Breaker is a checker on the harness, not just on the spec.** Three
  of the findings across rounds 3 and 4 were defects in the pipeline or in my own
  rejection briefs, not in the spec: the test process was given no way to locate
  the app's own files (`APP_DIR` did not exist), nothing implemented the
  packaging step a brief had told the Spec Writer to promise, and `CONTRACT.md`
  claimed `APP_DIR` was set in all three runs when the pipeline sets it in two.
  It cited `pipeline/test_runner.py:238` to prove one of them. A spec that
  assumes a capability the harness lacks reads as an ambiguous spec, so check the
  harness before rejecting the spec.

- **A rejection brief can manufacture the next round's defect.** Round 2's brief
  told the Spec Writer to write "anything that packages `app/` deletes it first".
  No such step existed, so round 3 correctly flagged a spec sentence that I had
  dictated. Write briefs in terms of what the pipeline does, not what it ought
  to do, and when a fix belongs in the harness, fix the harness.

- **A cut graded against one input cannot be told from a constant.** Round 2:
  `cut-week-dates` was graded by three criteria that all pinned the same seven
  literal dates from a single fixed `trackedDay`, and c-1-2 printed those strings
  verbatim into the session guide - so a 7-element literal was green on all
  fifteen criteria and the headline cut of session 1 graded nothing. Worse, the
  reference implementation was unpinned on the case that matters: the obvious
  `getUTCDate() - getUTCDay() + 1` is right for a Wednesday and a full week wrong
  for a Sunday. Adding one criterion with a Sunday fixture fixed both, and the
  Builder then wrote `(getUTCDay() + 6) % 7` unprompted. **E110 catches two cuts
  indistinguishable from each other; this is one cut indistinguishable from a
  hardcoded constant.** A pure-function cut needs at least two grading fixtures,
  one of them an edge case. Not yet a linter rule.

- **A fixture that encodes the anti-pattern teaches it.** The selftest's own
  `ROUTE_TS` put a route handler's only `return` inside the cut markers - the
  exact TS2355 shape the lessons above warn about - and its hint read "Return
  every todo from the store as JSON". The new static scan flagged the fixture on
  its first run. A checker written against a bad fixture passes by agreeing with
  it.

- **A constraint nothing can assert is a candidate for a static check, not a
  Gate 3 eyeball.** "Date arithmetic must give the same answer in every timezone"
  had no owner: the Verifier cannot change the server's `TZ`, and the suggestion
  was that a person read `lib/week.ts` at Gate 3. A person reading code at Gate 3
  is what this pipeline exists to avoid. It became `code_checks: ["utc-dates"]`,
  run at step 6, and moved from `nothing` to a column the Builder loop owns.
  Before writing `nothing`, ask whether the rule is about the *shape* of the code.

- **A pattern is not a parser, and the guard needed a parser.** `check_bash`
  fired on any `>` anywhere in a command and then blocked if any `projects/...`
  token resolved to a frozen spec, so `grep ">>> CUT" ...` alongside a mention of
  `spec.json` was refused - twice in one run. Two separate defects hid in one
  regex: a `>` inside quotes is data, not a redirect, and even for a real
  redirect only the token *after* it is written. Fixed by lexing the line
  quote-aware into simple commands and asking each what it *writes*: the operand
  of `>`/`>>`, every path argument of `rm`/`mv`/`tee`/`sed -i` and friends, the
  destination of `cp`. Reading a frozen spec, and copying it out to read, are now
  allowed; writing or deleting it is still refused. Two side-effects the regex
  had also missed: a `<` operand is a read, and a second *line* of a script is a
  second command, so `cd app
rm ../verify/t.py` used to slip past entirely.

## What a cut costs to teach

- **Hint length does not predict teaching time, and pipeline-test-03 proved it
  outright.** Round 3 weighted a cut by its hint words, calibrated on the two
  timed flow-2 sessions. The next project came in with every cut at 46-53 words,
  under the 55-word nominal; the linter reported both sessions at 38.5 against a
  40 cap and stayed silent; the Pack Writer then timed them at 48 and 45. The
  hints were not being gamed - a direct instruction not to tune them moved five
  cuts by one word in total. They were honest, and honest length still predicts
  nothing, because three ordered rules compress into 53 words as easily as one
  rule does.

- **What costs live minutes is the number of decisions a cut states, and whether
  their order matters.** The Pack Writer located the whole overrun in one cut:
  `cut-parse-line` "carries three rules, a rule ORDER, and the argument against
  Date - about 13 live minutes, not the flat 6 the linter charges", on a 53-word
  hint. The weight is now 6 minutes plus 1.7 per branch the hint states, with a
  small residual on length for the case decisions cannot see - an algorithm with
  no conditional prose at all, like pipeline-test-01's breadth-first
  `cut-reveal-from`, 103 words and 41 lines and zero stated conditions.

- **The fitted marker set beat the honest one, and the honest one shipped.**
  Including positional words (`first`, `next`) fitted the four sessions visibly
  better - worst error 3.2 against 4.8 - because "the first number is the first
  object's own paise" scored two decisions. It describes an element, not a
  branch. With four data points a regex that happens to fire more is
  indistinguishable from one that measures more, so the positional markers were
  dropped and the worse fit kept. **Prefer the model you can explain to the model
  that fits.**

- **The model was biased in opposite directions by flow, which the flat weight
  hid.** It ran 6.5 to 13 minutes LOW on all four flow-2 sessions and about 10
  minutes HIGH on recipe-box s1 and tip-split s1. Flow 1 writes many small cuts
  where flow 2 writes few complex ones, so one flat per-cut number cannot serve
  both. Flow 1 keeps the weight it was calibrated on; only flow 2 moved.

- **A named drop candidate that costs no live minutes is worse than naming
  none.** pipeline-test-03's spec offered markup elements as its trims, and the
  Pack Writer found that all five cuts were in `lib/` while every page file
  shipped written - no student typed that markup, so dropping it recovered
  nothing. The spec read as though it had slack it did not have. A drop candidate
  must be something a student types during the session, and no checker tests
  that.

- **Two free parameters against four points overfits by construction.** Only two
  of the four sessions were actually timed; the other two are the Pack Writer's
  estimates, and it ran about 2 minutes conservative on pipeline-test-02 (48
  estimated, 50 measured). The constants are provisional. The estimate is written
  into `lint.json` on every run so the next timed session can disagree with it in
  public.

## What the first out-of-sample measurement said

pipeline-test-03 session 1 measured **47 minutes**, taught by Priya from the
guide alone. Three predictions were on record before it ran:

| Prediction | Said | Error |
|---|---|---|
| Pack Writer | 48 | **+1.0** |
| decision-count linter model | 52.1 | +5.1 |
| old flat model | 38.5 | -8.5 |

- **The decision-count model beat the flat model and lost to the Pack Writer, and
  both of those are the expected result.** The flat model was 8.5 low and silent;
  the new one was 5.1 high and raised E111 at step 2. But the Pack Writer was five
  times closer, because it reads the session plan it has just written while the
  linter reads prose in spec.json before any plan exists. **The linter is not
  competing with the Pack Writer and cannot win.** Its job is to be wrong by about
  five minutes nine steps earlier, where the fix is one Spec Writer pass instead
  of a rebuild. A session the linter prices near the cap is a question for the
  Pack Writer, not an answer.

- **Refitting on the measurement was not worth doing.** The model was fitted
  against the Pack Writer's estimate of 48; the real number was 47. Refitting
  moves MINUTES_PER_DECISION 1.7 -> 1.6 and the worst error 5.1 -> 4.9. That is
  noise, and refitting two parameters on four points again buys nothing. **Resist
  refitting on every new point** - it feels like calibration and is mostly
  chasing sampling error.

- **Five projects, five overruns, and the estimate is still not the fix.** 45, 45,
  45, 50, 47 against a 40 minute cap. Every model so far has been an argument
  about how wrong the estimate is. The thing that has never been tried is
  reducing what a session contains once the Pack Writer prices it - the trims
  exist in every guide and no run has confirmed they were pulled.

- **Two dry runs in a row could not say whether the guide's trims were used.**
  pipeline-test-02 recorded the same gap. Until a dry-run note says which trims
  were pulled, a measured overrun cannot distinguish "the plan is too big" from
  "the plan was taught untrimmed". That is one sentence in the dryrun note and it
  is worth making mandatory.

## "Owned by a checker" is not "checked"

- **Rule 8 could not tell an owner that runs from an owner that passes by not
  running.** Gate 1 approves when every blocking finding sits in a column a
  downstream checker owns. `typecheck` is the fail-open second-line check: with
  the toolchain unreachable it reports no error, so a blocking finding parked
  there reaches the student skeleton with every gate green.
  pipeline-test-03's B2 - a TS2367 dead comparison once `cut-parse-line` is
  removed - was correctly owned by `typecheck`, and was caught only because the
  Gate 1 note told a person to read `typecheck_fail_open` at step 10 by hand. It
  read false. **Nothing in the pipeline enforced that, and the next note might
  not say it.**

- **The fix is to record the obligation, not to reject.** Downgrading a
  fail-open owner to `nothing` would have rejected a spec whose check did in fact
  run - a worse trade. `gate1.json` now carries `verify_later`, naming the
  finding, the report and the flag that has to be read, and the approve line says
  the verdict is conditional on it. The obligation stops depending on whoever
  writes the gate note.

- **One of the two was decidable on the spot, so it is decided.** `code-check`
  runs nothing unless spec.json declares an entry in `code_checks`. With that
  list empty it is `nothing` wearing a checker's name, and that is readable from
  the spec at Gate 1 - so it is now a reject rather than a deferred obligation.
  Prefer deciding to deferring whenever the data is already in front of you.

- **The general shape: a rule about ownership needs a notion of liveness.** Any
  check that can be skipped, fail open, or be configured out of existence is only
  conditionally an owner. Before adding a name to the OWNERS table, ask what
  happens when that checker cannot run.

- **A downstream owner that surfaces a finding cannot always fix it.** Rule 8
  approves when every blocking finding sits in a column a downstream checker
  owns. 2026-09-07, stock-tracker: Gate 1's five blocking findings were all
  owned by `test-runner`, `fail_open: false`, `verify_later` empty - the rule's
  cleanest possible verdict - and two notes recorded that c-3-3 asserted one row
  and that the apply tests mutated shared state. Both fired within the hour. The
  test-runner did surface them, exactly as the rule promised, but the only
  component that could have repaired them was the Builder, and Gate 1 had just
  frozen `verify/` out of its reach. **Owned, live, and still unfixable.** A
  finding whose remedy lives in `verify/` has to be settled before Gate 1
  freezes it - by the Test Writer, or by a person, or by rejecting - because
  after that the loop it causes cannot terminate on its own. Ask not only which
  checker sees a finding, but which component is allowed to act on what it sees.

## Which findings can become linter rules

Ten Gate 1 rejections across five projects, classified. The point of the
classification is that it decides what is worth promoting - "promote a finding
class once it recurs" needs someone to have counted.

| Class | Times | Owner now |
|---|---|---|
| A rule the spec states that no criterion grades | 6 | still the Spec Breaker |
| Behaviour when a cut is open, or a collection is empty, is unstated | 3 | still the Spec Breaker |
| A cut removes its function's only `return` (TS2355) | 2 | `W067` + the cutter's static scan |
| Session load: setup imbalance, or one oversized cut | 2 | `E111` / `W112` / `E113` / `W114` |
| A hint names no concrete symbol | 1 | `W066` |
| A cut's marker boundary is unpinned | 1 | still the Spec Breaker |
| No selectors pinned for UI criteria | 1 | still the Spec Breaker |

- **The promotable classes have already been promoted, and the ones left are
  prose-semantic.** Every class now owned by a script is checkable from
  *structure* - a count, an id, a shape in spec.json. The two that keep recurring
  are not: deciding that a stated rule has no criterion, or that a degenerate case
  is unstated, means reading prose against intent. That is the Spec Breaker's job
  and there is no cheap script that takes it over.

- **Two structural proxies were tried against the corpus and both failed.**
  "Every status code an endpoint declares must be named by a criterion" fires zero
  times on all ten rejected rounds *and* all five approved specs - it has no
  discriminating power, and section 9 of basic_needs_v1.md is explicit that a
  check which has never caught anything is not proven. "Every cut's marker
  boundary must be pinned in spec.md" is worse than useless: it stays silent on
  pipeline-test-02 round 2, the one spec that actually had the defect, while
  firing 9 times on approved flow-1 specs. **Test a candidate rule against the
  round that contained the defect before writing it, not against the corpus in
  general.** A rule that is quiet everywhere looks clean and proves nothing.

- **Rounds are the cost, not steps.** pipeline-test-02 spent about 3.1 hours of
  working time, and roughly 93 minutes of that was the PLAN phase run three
  times. Nothing was slow; it ran twice more than it needed to. Until a recurring
  class becomes checkable, the way to spend fewer minutes in this phase is fewer
  Gate 1 rejections, not faster steps.

- **The three agents in the PLAN phase cannot be overlapped.** The Test Writer
  reads `ambiguity.md`, so spec -> ambiguity -> tests is a data dependency, not an
  ordering convention. It is also the reason pipeline-test-02's suite could record
  per test which reading of an ambiguity it took. Recorded in
  `gp-phase1-spec.js` so it is not tried again as a speed-up.

## Session timing

- **Four consecutive projects overran on the same shape: one cut far larger than
  its siblings.** recipe-box session 3 and tip-split session 1 both ran 45 against
  a 40 minute cap; habit-tracker's `cut-api-toggle` was estimated at 6 minutes and
  measured about 20; pipeline-test-02 session 2 ran 50 against a guide estimate of
  48 and a spec estimate of 37. The estimator could not see any of it, because
  `MINUTES_PER_CUT` weighed every cut the same 6 minutes. **A spec-linter minute
  budget is not evidence.** It was arithmetic over counts, and the thing that
  actually overruns is one block of live coding with too many rules in it.

- **The fix belongs in the spec, not in the pack.** By the time the Pack Writer
  times a session at step 9, the spec, the code, the tests and the skeleton are
  all built and both gates are passed; the only real fix invalidates the build.
  The pack can only disclose the overrun, which is what pipeline-test-02 did -
  session-2.md declared 48 minutes at the top and shipped anyway. Cap the cut at
  step 2 instead. `W114` now warns when one cut takes more than 45% of a
  session's cut minutes, and cut minutes scale with hint length above a 55-word
  nominal.

- **Do not fix a heavy session by moving a cut into the setup session.** That
  trades W114 for E113 - the session carrying the setup must hold strictly fewer
  cuts than the others, which is the tip-split lesson. Split the oversized cut in
  place, or name a drop candidate inside its own session.

- **Hint length turned out to be the usable proxy, and only within a flow.**
  Measured `lines_removed` correlates only loosely with teaching time (110 hint
  words removed 18 lines, 76 words removed 23), because what costs live minutes is
  how many rules have to be explained, not how many lines get typed. Flow-1 specs
  write far terser hints than flow-2 ones - recipe-box averages 30 words against
  flow 2's 75 - so the same per-word rate misreads them. The rule is gated to
  flow 2 rather than applied retroactively to three shipped projects.

- **Two flow-2 sessions have a measured time; the model is calibrated on two
  points.** pipeline-test-01 session 2 (flat 32.5, measured 45) and
  pipeline-test-02 session 2 (flat 37.0, measured 50). Both now estimate within a
  minute. That is a small sample and the constants should move when the next dry
  run disagrees with them - the estimate is reported in `lint.json` on every run
  precisely so the disagreement is visible.

- **A trimmed session does land at 40, and that was the open question.** Six
  projects, six measured sessions: 45, 45, 45, 50, 47, and now **40**.
  2026-09-07, stock-tracker session 1, taught by Priya from the guide alone
  (`taught_without_the_code: true`), spec estimate 44.5 with the setup on it.
  This is the measurement `blockers_round_3.md` closed on - *"the next run's most
  valuable measurement is not a better model, it is one dry run of session 1
  with the trims pulled, to confirm a trimmed session actually lands at 40"* -
  and the answer is yes. Note which session it was: session 1 carries the setup
  and had been the worst offender (tip-split 45, recipe-box 45), so the cap is
  reachable on the hardest one.

- **A guide that states exactly the cap cannot fail the overrun rule.** Same
  run: all five sessions wrote `**Time:** 40 minutes` and guide-lint returned 0
  errors and 0 warnings, because `G031`/`G032` test `stated > cap` and 40 is not
  greater than 40. The spec had estimated 44.5 / 43 / 43 / 46.2 / 49.0 for those
  same sessions. So a clean guide-lint is not evidence the content fits - only a
  dry run is, and only session 1 had one. **Read `lint.json`'s session_minutes
  beside the guide's Time lines**; a guide claiming the cap against a spec
  estimate 5-9 minutes above it is asserting a trim, not reporting one. Whether
  the linter should distrust a stated time that exactly equals the cap, or
  cross-check it against the spec estimate, is an open decision - the second is
  better and needs a threshold nobody has picked.

- **"overrun" and "trim" are ordinary words in a guide about money and code.**
  Same run: session-3.md was reported `disclosed: true` off a troubleshooting
  line - `- "Budget overrun" - They forgot to subtract cost from remaining` -
  which is about the student's arithmetic, not the clock. The verdict did not
  move, because the session stated exactly the cap and `over` was false, but the
  flag a person reads at Gate 3 was wrong. Fixed: `guide_linter.timing_disclosure`
  lets "does not fit" and "over the cap" stand alone and requires a timing word
  on the same line for the ambiguous two. A checker that reports a field nobody
  acts on today will be read as evidence the day someone does.

## Teaching

<!-- Where students actually got stuck, from live sessions. -->
