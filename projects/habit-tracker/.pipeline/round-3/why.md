# Round 3

Gate 1: rejected
Note: GATE 1 REJECTED - round 3. The domain logic is accepted: the Spec Breaker could
not break it, and every number was verified by hand. Three of round 3's six
findings were defects in the PIPELINE, not the spec, and all three are now fixed
in the harness. Round 4 is the smallest brief yet: restate three mechanisms in
terms of what the harness now actually provides, and fix three wordings.

=== THE HARNESS CHANGED - RESTATE THESE, DO NOT INVENT AROUND THEM ===

H1. (was A1, blocking, owned by `nothing`) The test process is now given
    `APP_DIR` as well as `BASE_URL`. It is the absolute path of the directory the
    running app was started from - `app/` on the real run, `skeleton/` on the
    skeleton run. Round 3 was right that the old mechanism was unresolvable: the
    suite only knew the web address, and it runs from three different working
    directories.

    Restate the determinism paragraph in those terms, e.g.: "The store lives at
    `data/habits.json` inside the running app's own directory, which the test
    process reads from `APP_DIR`. Every test in every session deletes
    `$APP_DIR/data/habits.json` before it runs and lets `readStore()` copy
    `data/habits.seed.json` back." Do not describe a path relative to the test
    file or to the project root - neither is correct for all three runs.
    `c-3-4`, which reads the file's bytes, resolves it the same way.
    See `.pipeline/CONTRACT.md`, "What the test process is given".

H2. (was B2, owned by `nothing`) Round 2's brief told you to write "anything that
    packages app/ deletes it first". That step did not exist - my error in that
    brief, not yours. It exists now, by a different mechanism: the cutter and the
    deploy check both honour `app/.gitignore`. A gitignored file is runtime state
    and is left out of `skeleton/` and out of the step-10 fresh copy; a tracked
    file beside it still ships.

    So state it as the declaration it now is. Require `app/.gitignore` to contain
    `data/habits.json` and `!data/habits.seed.json`, and say that this is what
    keeps the live store out of every shipped copy while the seed ships. Delete
    the "anything that packages" sentence.
    See `.pipeline/CONTRACT.md`, "Runtime state must not ship".

H3. (was B3, owned by `nothing`) The UTC-arithmetic rule now has a checker. Add
    to the top level of spec.json:

        "code_checks": ["utc-dates"]

    It runs over `app/` at step 6 and fails the step on any local-time `Date`
    accessor (`getDay`, `setDate`, `toLocaleDateString`, ...) or any read of the
    real clock (`new Date()` with no arguments, `Date.now()`). So the constraint
    the idea called make-or-break is now owned by `code-check` instead of by
    nothing, and the Builder fixes a violation in the normal loop. Mention in
    spec.md that the rule is enforced this way, so the Pack Writer and the
    instructor know. The linter rejects an unknown check name, so use exactly
    `utc-dates`.

=== SPEC FIXES ===

S1. (B1, owned pack-writer) The spec says "only the cuts declared in a session
    are opened in that session's skeleton". There is ONE skeleton and all eight
    cuts are open in it - `pipeline/cutter.py` generates a single tree. Reword to
    describe what exists: one skeleton with every cut open, and the session
    ordering is how the instructor walks the student through it, not separate
    artifacts.

S2. (B4, owned by `nothing`) The toggle's accepted date set is written down
    twice: seven literal dates in the Endpoints prose and in spec.json, and
    `weekDates(store.trackedDay)` in the cut hint. Nothing separates them, so
    they can drift. Pick one and make the other refer to it. The derived form is
    the better source of truth now that `c-1-6` drives more than one
    `trackedDay` - seven literals would contradict the Sunday fixture.

S3. (B5, owned by `nothing`) `c-3-1`, `c-3-3` and `c-3-5` depend on
    `cut-store-find-habit` without naming it, and `c-3-2` depends on
    `cut-api-habit-get` without naming it. The skeleton check reads those lists,
    so an under-declared cut weakens the proof. Declare every cut each criterion
    really depends on.

    CAREFUL: this edit is exactly the kind that can collapse two cuts onto the
    same grading signature and trip linter E110. After declaring them, re-check
    that no two cuts are graded by an identical set of criteria. If a pair
    collapses, add or adjust a criterion so one of them is graded alone.

=== CONFIRMED GOOD - DO NOT REGRESS ===

Verified by the round-3 Spec Breaker and to be preserved exactly: streak
arithmetic against the seed (5/0/0/1); every toggle criterion's expected streak
(c-3-1 2, c-3-2 0 with two done days, c-3-3 3 then 0, c-3-5 1); 2026-08-26 is a
Wednesday and 2026-08-30 that Monday-first week's Sunday; all eight cuts on
distinct criteria signatures with E110 clear; no proper subset of any multi-cut
criterion satisfying it; all eight fallbacks declared and every return outside
the markers; session minutes 37 / 38.5 / 35.5 against the 40 cap with the setup
session carrying strictly fewer cuts; three sessions; four seed habits with the
three required streak cases; all five of idea.md's out-of-scope items carried
over; c-1-6's second and third trackedDay fixtures; the toggle's accepted-date
range and malformed-date behaviour; the readStore / findHabit / writeStore
coherence; the { error } shape; the resolved error screen state; duplicate
doneDates decided; the 404 and 400 paths; concrete UI selectors.

Linter must stay at 0 errors.
