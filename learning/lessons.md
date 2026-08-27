# Lessons

Step 5 of the build order: so a mistake caught once is not repeated. Every agent
reads this file before it starts.

One line per lesson. Add a lesson the moment a gate rejects something or a
nightly watchdog run goes red. Delete nothing - a lesson that stops applying
gets a strikethrough and a date.

## Spec

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

## Cut points

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

## Tests

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

## Process

- **Do not edit a shared input while a run is reading it.** 2026-08-26: this file
  was written mid-pass during recipe-box round 2. The Spec Breaker read it empty
  at step 3, noticed it change, and re-checked every finding - which cost a pass
  and could have gone the other way. Update `lessons.md` between runs, never
  during one.
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

## Teaching

<!-- Where students actually got stuck, from live sessions. -->
