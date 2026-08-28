# Round 2

Gate 1: rejected
Note: GATE 1 REJECTED - round 2. Converging: 12 findings -> 7. Round 3 is a small,
bounded revision, not a rewrite.

Every round-1 finding was fixed and none was re-litigated - keep all of that.
The linter was clean at 0 errors / 0 warnings with sessions at 37 / 38.5 / 35.5
against the 40 cap, the setup session at 2 cuts against 3, and all eight cuts on
distinct grading signatures. Keep every one of those properties.

The four items in group 1 are the reason for the rejection: they are all grading
integrity, and no downstream checker sees any of them. Group 2 is cheap and
worth doing in the same pass.

=== GROUP 1 - GRADING INTEGRITY (the reason for the reject) ===

M1. (A1, blocking, owned by `nothing`) `cut-week-dates` is graded against
    exactly one input, and it is a Wednesday. trackedDay is fixed at 2026-08-26,
    every call site passes store.trackedDay, and c-1-1 / c-1-2 / c-1-5 all pin
    the same seven literal strings - which c-1-2 prints verbatim into the session
    guide. So `dates = ["2026-08-24", ..., "2026-08-30"]` is green on all fifteen
    criteria: the headline cut of session 1 can be answered with a constant and
    the student is told they are done. Neither the cutter nor skeleton-check can
    tell arithmetic from a literal.

    The second half is worse. The obvious Monday formula
    `d.setUTCDate(d.getUTCDate() - d.getUTCDay() + 1)` is right for a Wednesday
    and a full week wrong for a Sunday, because getUTCDay() is 0 on Sunday and
    the Monday-first correction is `- ((day + 6) % 7)`. With one Wednesday as the
    only fixture, nothing pins it, and the broken formula ships as the answer the
    instructor teaches from.

    Add a session-1 criterion that drives a second and third trackedDay. The
    tests already own data/habits.json, so they can write the fixture:
      c-1-6 - with data/habits.json written so trackedDay is 2026-08-30, a
      Sunday, GET /api/habits returns every habit's days[].date as 2026-08-24
      through 2026-08-30 in that order; and with trackedDay 2026-09-06 it returns
      2026-08-31 through 2026-09-06.  Cuts: cut-week-dates.
    Session 1 has 5 criteria against a cap of 6, and criteria cost no teaching
    minutes, so this fits. This is NOT week navigation - the app still renders
    exactly one week - so it does not reopen the Out of scope bullet.

M2. (B1, owned by `nothing`) The fallback list covers five of the seven cuts.
    `found` in findHabit and the body of onCellClick have no declared fallback.
    If `found` is not pinned, `found = store.habits[0]` compiles, and a student
    who fills cut-api-habit-get alone sees c-2-1, c-2-3 and c-2-4 go green with
    findHabit still empty - the recipe-box c-3-2 hole exactly, and skeleton-check
    cannot see it because those criteria fail on the 501 in the all-open
    skeleton. The whole grading-independence argument for session 2 rests on
    findHabit returning null when unwritten, and nothing downstream re-derives
    that. Declare all seven fallbacks. Suggested: "... `found` starts as `null`,
    and onCellClick's body below the marker is empty so a click changes nothing."

M3. (B3, owned by `nothing`) The single-habit page has no defined behaviour for a
    status that is neither 200 nor 404, so `!res.ok` turns c-2-5 green with
    cut-api-habit-get empty. Add to the cut-habit-page hint: "Only a 404 sets
    `missing`; any other non-200 status leaves the page in its pre-response
    state, and nothing grades that."

M4. (B4, owned by `nothing`) data/habits.json is gitignored but the skeleton is a
    file copy, not a checkout, so step 6's mutated store ships in the skeleton. A
    student's first `npm run dev` shows drink-water on a streak of 0 while the
    guide says 5, and no checker looks. Add to the Data model: "data/habits.json
    is absent from every shipped copy of the project - anything that packages
    app/ deletes it first - so the first read of a fresh copy always re-seeds."

=== GROUP 2 - CHEAP, SAME PASS ===

S1. (A2, blocking, owned test-runner) "Every test deletes data/habits.json" never
    says where that file is, and the Python suite is handed only BASE_URL while
    the app runs from either app/ or skeleton/. That sentence is load-bearing for
    all fifteen criteria, since every number is declared as measured from the
    seed state. In the Sessions preamble, name the location and the resolution:
    "The store lives at data/habits.json relative to the running app's own
    directory, which readStore() resolves through process.cwd(). Every test in
    every session deletes that file - resolved from the target the suite is
    running against, app/ or skeleton/ - before it runs, and lets readStore()
    copy data/habits.seed.json back."

S2. (B2, owned test-runner) c-3-4 compares the store file "before and after" a
    sequence whose first request creates it, so as written it is unsatisfiable.
    Reword: "...; and after one GET /api/habits has materialised
    data/habits.json from the seed, that file is byte-for-byte identical before
    and after the 4 requests."

S3. (B5, owned test-runner) "in place of" is asserted for the cells and not for
    the name or the streak. Extend c-2-5: "... renders 0 elements with
    data-testid day-cell, and renders no habit-name and no habit-streak element."

=== CONFIRMED GOOD - DO NOT REGRESS ===

From the round-1 review, all still standing: fixed deterministic tracked week; no
real clock (and now the UTC-accessor clause); strong seed cases; clear data
contract; three sessions; setup session carries fewer cuts (2 against 3); all
eight cuts on distinct grading signatures; strong toggle testing; the 404 and 400
paths; concrete UI selectors; no network or database dependency; session 2's cut
separation; session 3's add / remove / toggle-twice coverage.

Added in round 2 and also worth keeping: every criterion number verified against
the seed; the toggle's accepted-date range and malformed-date behaviour; the
readStore / findHabit / writeStore relationship made coherent; the { error }
shape; the error screen state resolved; duplicate doneDates decided.
