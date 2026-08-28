# Ambiguity report - habit-tracker

**Verdict:** 2 blocking, 5 worth a look

Read in the mandated order: `spec.md` and `spec.json` alone, then `idea.md`, then
`learning/lessons.md`. Checks I did by hand before writing anything:

- **Arithmetic.** Every number in every criterion is right against the seed. The
  four session-1 streaks (5 / 0 / 0 / 1), `c-3-1` (stretch + 08-25 -> 2),
  `c-3-2` (drink-water - 08-26 -> 0, then 2 done days in the week), `c-3-3`
  (read-pages + 08-26 -> 3, then 0 with 2 done days) and `c-3-5` (meditate +
  08-26 -> 1, drink-water untouched at 5) all compute.
- **Caps.** Session minutes 37 / 38.5 / 35.5 against a 40 cap; the setup session
  carries 2 cuts against 3; 5 criteria per session against a max of 6. No two
  cuts share a criteria signature, so E110 will not fire.
- **Proper subsets.** For all seven cuts and all fifteen criteria I checked, by
  hand, that no proper subset of a criterion's cuts satisfies it - the blind
  spot `lessons.md` names. It holds everywhere *given* the fallbacks the spec
  declares, which is why B1 and B3 below are about the two it does not declare.
- **Round 1.** Every finding from `.pipeline/round-1/ambiguity.md` is addressed
  in this revision, including all nine worth-a-look items. I have not
  re-litigated any of them.

Both blocking findings are in the same place round 1's were: the date arithmetic,
and the file that has to be reset for any of these numbers to mean anything.

## Blocking

### A1 - `cut-week-dates` is graded against exactly one input, and it is a Wednesday

- **Where:** spec.md, Session 1 cut points, `cut-week-dates`; graded by `c-1-1`,
  `c-1-2`, `c-1-5`; spec.json session 1 cuts[0]
- **Owner:** nothing
- **The line:** "`weekDates(trackedDay: string): string[]`, the seven
  `YYYY-MM-DD` strings of that date's Monday-to-Sunday week, Monday first." with
  `c-1-2` - "GET /api/habits returns every habit's days[].date as the strings
  2026-08-24, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29,
  2026-08-30 in that Monday-to-Sunday order."
- **Reading one:** `weekDates` is a function of its argument, so it must derive
  the Monday for any `YYYY-MM-DD` string. That is what the hint teaches and what
  the Outcome calls the project's first distinguishing skill, "date arithmetic
  over `YYYY-MM-DD` strings".
- **Reading two:** `weekDates` only ever receives `2026-08-26`. The seed fixes
  `trackedDay` forever, Out of scope forbids any other week, and every call site
  passes `store.trackedDay`. So
  `return ["2026-08-24", ..., "2026-08-30"]` is green on all fifteen criteria,
  including `c-3-4`'s 400 for `2026-08-31` - and the seven strings the student
  has to return are printed verbatim in `c-1-2`, which is in their session guide.
- **Why it matters:** two defects, and no downstream checker sees either.
  (a) The headline cut of session 1 can be answered with a constant. The cutter
  and `skeleton-check` only prove that the criteria go red when the cut is empty
  (`dates = []`) and green when it is filled; neither can tell arithmetic from a
  literal, so a student who hardcodes is told they are done. (b) Worse, the
  Builder's own reference implementation is unpinned on the one case that
  matters. The obvious `d.setUTCDate(d.getUTCDate() - d.getUTCDay() + 1)` gives
  `2026-08-24` for Wednesday `2026-08-26` and passes everything here, but for a
  Sunday `trackedDay` it returns `2026-08-31` - the *next* Monday, a full week
  wrong, because `getUTCDay()` is 0 on Sunday and the Monday-first correction is
  `- ((day + 6) % 7)`. With one Wednesday as the only fixture, that bug ships as
  the answer the instructor teaches from. Round 1's A1 fixed the timezone half of
  this hazard with the UTC clause; the weekday-zero half is still ungraded.
- **Suggested wording:** add one session-1 criterion whose fixture is a different
  `trackedDay`, which the tests already control because they own
  `data/habits.json`: "`c-1-6` - with `data/habits.json` written so `trackedDay`
  is 2026-08-30, a Sunday, GET /api/habits returns every habit's days[].date as
  2026-08-24 through 2026-08-30 in that order; with `trackedDay` 2026-09-06 it
  returns 2026-08-31 through 2026-09-06. Cuts: `cut-week-dates`." This is not
  week navigation - the app still renders exactly one week - so it does not
  reopen the Out of scope bullet, and session 1 has room for a sixth criterion at
  37 of 40 minutes.

### A2 - "Every test deletes `data/habits.json`" never says where that file is, and the test process is only told `BASE_URL`

- **Where:** spec.md, Sessions preamble; spec.md Data model (`data/habits.json`
  is the live store); `c-3-4`
- **Owner:** test-runner
- **The line:** "**Every test in every session deletes `data/habits.json` before
  it runs** and lets `readStore()` copy `data/habits.seed.json` back." with
  `c-3-4` - "data/habits.json is byte-for-byte identical before and after the 4
  requests."
- **Reading one:** `data/habits.json` is a path the test suite can resolve, so
  each test unlinks it and `c-3-4` reads its bytes twice.
- **Reading two:** there is no such path. The suite is Python under
  `projects/<slug>/verify/`, and the running app lives in either
  `projects/<slug>/app/` or `projects/<slug>/skeleton/` - the same suite is run
  against both targets, at step 6 and again at step 8 - while the only thing the
  suite is handed is `BASE_URL`. `data/habits.json` is therefore two different
  files depending on which target is up, and the spec names neither. A Verifier
  that hardcodes `app/data/habits.json` silently stops resetting anything during
  the skeleton run; one that resets nothing at all is the round-1 A3 defect back
  again.
- **Why it matters:** every number in every criterion is declared to be "measured
  from the seed state", so this one sentence is load-bearing for all fifteen. It
  is also the only thing that keeps the mutated store out of the student's way
  (see B4). Step 6 does catch the total failure - session 3's tests mutate the
  store and session 1's assert `Streak: 5` on drink-water in the same run, so
  contamination is red inside one invocation and the Builder/Verifier loop fixes
  it - which is why the owner is `test-runner` and not `nothing`. But `c-3-4`
  cannot be written at all until someone decides this, and it is a sentence here
  against a retry there.
- **Suggested wording:** in the Sessions preamble, name the location and the
  resolution: "The store lives at `data/habits.json` relative to the running
  app's own directory, which `readStore()` resolves through `process.cwd()`.
  Every test in every session deletes that file - resolved from the target the
  suite is running against, `app/` or `skeleton/` - before it runs, and lets
  `readStore()` copy `data/habits.seed.json` back."

## Worth a look

### B1 - The fallback list covers five of the seven cuts

- **Where:** spec.md, Data model, "Skeleton fallbacks"; against
  `cut-store-find-habit` and `cut-board-click`
- **Owner:** nothing
- **The line:** "Each cut sits below a fallback declared in the same function,
  and every fallback fails the criteria that name the cut: `dates` and `next`
  start as empty arrays, `count` starts at `-1`, a route's `status` starts at 501
  with `body` set to `{ "error": "not implemented" }`, and on `/habits/[id]`
  `missing` starts as `false` with no cells and `streakText` set to
  `Streak: -1`."
- **Reading one:** the list is exhaustive, so `found` in `findHabit` and the body
  of `onCellClick` have no declared fallback and the Builder picks. `found = null`
  and an empty handler are the sane picks, and the `cut-store-find-habit` hint
  ("leave `found` as `null` when no habit ... matches") implies the first.
- **Reading two:** anything that compiles is a fallback. `found = store.habits[0]`
  compiles, and then a student who fills `cut-api-habit-get` alone sees `c-2-1`,
  `c-2-3` and `c-2-4` go green with `findHabit` still empty - because
  `/api/habits/drink-water` would answer with drink-water either way. That is
  exactly the recipe-box `c-3-2` hole in `lessons.md`, and `skeleton-check` cannot
  see it: in the all-open skeleton those criteria fail anyway on the 501.
- **Why it matters:** the spec's whole grading-independence argument for session 2
  rests on `findHabit` returning `null` when it is unwritten. Nothing downstream
  re-derives that. It costs two clauses to pin.
- **Suggested wording:** extend the sentence: "... `found` starts as `null`, and
  `onCellClick`'s body below the marker is empty so a click changes nothing."

### B2 - `c-3-4` compares the store file "before and after" a sequence whose first request creates it

- **Where:** spec.md, Session 3, `c-3-4`; spec.json session 3 criteria[3]
- **Owner:** test-runner
- **The line:** "and data/habits.json is byte-for-byte identical before and after
  the 4 requests"
- **Reading one:** capture the bytes, fire the four requests, capture again. But
  the test has just deleted the file, and `data/habits.json` "appears on the first
  read" - which is the first of those four requests. There is nothing to capture
  at "before".
- **Reading two:** the test issues a priming request first (any GET) so the seed
  copy exists, then measures. That is a fifth request the criterion does not
  mention, and it has to happen before the 404 case.
- **Why it matters:** as written the criterion is unsatisfiable, so the Verifier
  invents the priming step; step 6 shows it as an error rather than a silent pass,
  so it does not escape. Worth a clause because `c-3-4` is the only criterion that
  proves a rejected request writes nothing.
- **Suggested wording:** "...; and after one GET /api/habits has materialised
  `data/habits.json` from the seed, that file is byte-for-byte identical before
  and after the 4 requests."

### B3 - The single-habit page has no defined behaviour for a status that is neither 200 nor 404

- **Where:** spec.md, Screens (`sc-habit`), `cut-habit-page`; against the declared
  501 route fallback
- **Owner:** nothing
- **The line:** "when the `/api/habits/[id]` response status is 404, set `missing`
  to `true`" with the states of `sc-habit` given as "loaded, not-found".
- **Reading one:** only 404. Any other status leaves `missing` false, and the page
  draws no cells - the same nothing it draws before the first response.
- **Reading two:** `if (!res.ok) missing = true`, which reads the same on every
  criterion in `app/`. It is not the same in the skeleton: the route's fallback is
  501, so a student who fills `cut-habit-page` alone gets `c-2-5` green with
  `cut-api-habit-get` still empty, and `c-2-5` names both cuts. Another proper
  subset the skeleton check cannot see, for the same reason as B1.
- **Why it matters:** the spec does say 404 twice, so the Builder will very likely
  land on reading one and every criterion is green either way - which is also why
  nothing downstream would report reading two. One clause removes the option.
- **Suggested wording:** add to the `cut-habit-page` hint: "Only a 404 sets
  `missing`; any other non-200 status leaves the page in its pre-response state,
  and nothing grades that."

### B4 - The live store is gitignored, but the skeleton is a file copy, not a checkout

- **Where:** spec.md, Data model - "`data/habits.json` is the live store. It is
  listed in `.gitignore` and is never committed"
- **Owner:** nothing
- **The line:** "it appears on the first read and is deleted to reset the world"
- **Reading one:** the file only ever exists on a developer's disk, so "never
  committed" is enough to keep it out of what students get.
- **Reading two:** what students get is `skeleton/`, which is produced by walking
  `app/` and copying every file that is not under `node_modules`, `.next`, `.git`
  and friends - `.gitignore` is not consulted. By the time the cutter runs, step
  6's toggle tests have left `app/data/habits.json` on disk in a *mutated* state
  (drink-water without 2026-08-26, meditate with it), and `readStore()` will not
  re-seed over a file that exists. So the shipped skeleton starts life with a
  store that does not match the seed table.
- **Why it matters:** it is mostly masked - the verify suite ships with the
  skeleton and every test deletes the file first (A2), so the student's tests
  still grade against the seed. What is left is a student whose first `npm run
  dev` shows drink-water on a streak of 0 while the guide says 5, and no checker
  looks: `skeleton-check` only needs the criteria to be red, and `deploy-check`
  runs against `app/`.
- **Suggested wording:** add to the Data model: "`data/habits.json` is absent from
  every shipped copy of the project - anything that packages `app/` deletes it
  first - so the first read of a fresh copy always re-seeds."

### B5 - "in place of" is asserted for the cells and not for the name or the streak

- **Where:** spec.md, Screens (`sc-habit`); `c-2-5`
- **Owner:** test-runner
- **The line:** "`data-testid="habit-missing"`, with the text `Habit not found`,
  shown in place of the name, the streak and the cells" against `c-2-5` -
  "displays an element with data-testid habit-missing whose text is exactly
  `Habit not found`, and renders 0 elements with data-testid day-cell"
- **Reading one:** on 404 the page renders `habit-missing` and nothing else, so a
  test may assert `habit-name` and `habit-streak` are absent.
- **Reading two:** only the cell count is graded, so `habit-missing` may sit
  beside an empty `habit-name` and a `habit-streak` reading `Streak: -1` - and
  `cut-habit-page`'s hint even says to "keep the `habit-name` element ... already
  in the file", which reads like it stays rendered.
- **Why it matters:** if the Verifier writes reading one against a Builder who
  built reading two, step 6 goes red and the loop settles it. Cheap to decide
  here instead.
- **Suggested wording:** extend `c-2-5`: "... renders 0 elements with data-testid
  day-cell, and renders no habit-name and no habit-streak element."
