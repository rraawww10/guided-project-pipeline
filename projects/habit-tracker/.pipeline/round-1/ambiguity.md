# Ambiguity report - habit-tracker

**Verdict:** 3 blocking, 9 worth a look

Read in the mandated order: `spec.md` and `spec.json` alone, then `idea.md`, then
`learning/lessons.md`. The spec is internally tidy and would lint clean - I
checked the caps by hand (session minutes 38.5 / 38.5 / 35.5, setup session
carries 2 cuts against 3, every cut referenced, every endpoint and screen built,
no two cuts sharing a criteria signature so E110 will not fire). Per the first
lesson in `learning/lessons.md`, that is not the same as a clean spec. I also
walked every multi-cut criterion for the proper-subset hole: none of the eight
cuts can be left empty with all of its criteria green, which is the one thing
this spec gets right that recipe-box did not.

The three blocking findings below are all in the same region: how a date string
becomes a weekday, and how the toggle route gets its mutation onto disk.

## Blocking

### A1 - The spec bans `new Date()` in `lib/` and then asks `lib/week.ts` to find a Monday

- **Where:** spec.md, Out of scope (line 32) against Data model (line 37) and the
  `cut-week-dates` hint; spec.json session 1 cuts[0].hint
- **Owner:** nothing
- **The line:** "Reading `new Date()` anywhere in `app/` or `lib/`." set against
  "No `Date` object crosses a module boundary." and the hint "Step back from
  `trackedDay` to that week's Monday and forward from there; read no clock, so
  the same `trackedDay` always gives the same 7 strings."
- **Reading one:** the ban is on the zero-argument clock read only. "No `Date`
  object crosses a module boundary" only makes sense if `Date` objects may exist
  *inside* a module, so `weekDates` is allowed to do
  `new Date(trackedDay)` / `getDay()` / `setDate()` and format back to
  `YYYY-MM-DD`. The cut is about five lines.
- **Reading two:** the ban is literal - the constructor may not appear in `lib/`
  at all. Then `weekDates` has to derive the weekday of an arbitrary
  `YYYY-MM-DD` string by hand (day-count from a fixed anchor, or Zeller), plus
  its own day-before / day-after arithmetic across month and year ends, because
  `lib/streak.ts` needs to step backwards day by day too. That is 25+ lines of
  civil-date arithmetic and a different session entirely.
- **Why it matters:** two consequences, neither of which any downstream checker
  sees. (a) Session 1 is estimated at 38.5 teaching minutes against a 40 cap;
  reading two makes `cut-week-dates` the hardest cut in the project and the
  estimate wrong, and nothing before the Pack Writer at step 9 weighs that
  (`lessons.md`, "Nothing checks that sessions are balanced"). (b) Under reading
  one the obvious implementation is timezone-dependent and the hint never says
  otherwise: `new Date("2026-08-26")` parses as UTC midnight, so `getDay()`
  returns Wednesday in IST but Tuesday anywhere west of Greenwich, which shifts
  the computed Monday to `2026-08-25` and turns `c-1-2` and `c-1-5` red. The
  pipeline runs in one timezone, so the Builder's own suite goes green and the
  defect lands only on students. `typecheck`, `cutter`, `skeleton-check` and
  `deploy-check` are all indifferent to which reading shipped, and `test-runner`
  cannot see a bug that only fires in another `TZ`.
- **Suggested wording:** in Out of scope, replace the bullet with "Reading the
  real clock - no `new Date()` with no arguments, and no `Date.now()`, anywhere
  in `app/` or `lib/`. Constructing a `Date` from the seed's `trackedDay` string
  is allowed." Then add one clause to the `cut-week-dates` hint: "use the UTC
  accessors (`getUTCDay`, `setUTCDate`) or plain string arithmetic, so the answer
  does not change with the machine's timezone."

### A2 - `writeStore(store)` in the toggle hint has no `store`, and mutating what `findHabit` returned need not reach it

- **Where:** spec.md, Session 3 cut points, `cut-api-toggle`; spec.json session 3
  cuts[1].hint; against spec.md Data model (`readStore`) and the
  `cut-store-find-habit` hint
- **Owner:** test-runner
- **The line:** "when it gives a habit set its `doneDates` to
  `toggleDate(habit.doneDates, date)`, save the file with `writeStore(store)`,
  then set `body` to `habitWeek(habit)` and `status` to 200" - where the habit
  came from "`findHabit(habitId)`", whose own hint reads "assign the one habit
  from `readStore().habits` whose `id` equals the `habitId` argument to `found`".
- **Reading one:** `readStore()` parses `data/habits.json` fresh on every call.
  Then `findHabit` returns a habit belonging to a store object that the route
  never holds, `store` is not a binding that exists in
  `app/api/habits/[id]/toggle/route.ts`, and even if the route calls `readStore()`
  itself to get one, the object it mutates is not in that store - so
  `writeStore(store)` serialises the *unmodified* data and the toggle does not
  persist.
- **Reading two:** `readStore()` memoises and returns one module-level store
  object. Then the habit `findHabit` returns is the same object the route's
  `store` contains, mutate-then-write works exactly as the hint describes - and
  the "delete the file to reset the world" trick in the Reading-order paragraph
  stops working within a single server process, because the cached store outlives
  the deleted file.
- **Why it matters:** the spec never says whether `readStore` caches, and the
  toggle hint is only implementable under the caching reading. The Builder either
  writes the hint literally and fails to compile (`store` undeclared) or fails
  `c-3-2`, which is the one criterion that checks persistence with a following
  GET - so step 6 will surface it. The cost is that the fix belongs in the hint,
  and the Builder cannot edit hints: it will quietly write coherent code
  (`const store = readStore(); const habit = store.habits.find(...)`) that no
  longer matches the sentence the student is given, which is the recipe-box
  round-2 failure shape.
- **Suggested wording:** in the Data model, add "`readStore()` re-reads and
  re-parses `data/habits.json` on every call and returns a fresh object." Then
  make the hint self-consistent: "read the store with `readStore()` into `store`,
  find the habit inside `store.habits` with `findHabit`'s lookup applied to
  `store`, set its `doneDates` to `toggleDate(habit.doneDates, date)`, then
  `writeStore(store)`" - or give `findHabit` the signature
  `findHabit(store, habitId)` and say so in the Data model.

### A3 - Only session 3's tests are told to reset the store, but sessions 1 and 2 assert seed-state numbers

- **Where:** spec.md, Session 3, "Reading order for a test run"; against `c-1-3`,
  `c-1-4`, `c-1-5`, `c-2-1`, `c-2-3`, `c-2-4`
- **Owner:** test-runner
- **The line:** "Every criterion in session 3 mutates `data/habits.json`, so each
  test deletes that file first and lets `readStore()` copy
  `data/habits.seed.json` back. The numbers above are all measured from the seed
  state."
- **Reading one:** the reset belongs to session 3's tests only, as written. Every
  session-3 test then *leaves* `data/habits.json` mutated when it finishes -
  `c-3-5` leaves `meditate` done on `2026-08-26`, `c-3-2` leaves `drink-water`
  without it. The next run of the suite starts from that file, so `c-1-3`
  ("streak ... 0 for id meditate") and `c-1-4` / `c-2-1` (`Streak: 5` for
  drink-water) are red on the second run in the same working copy, and red in any
  order that is not strictly ascending.
- **Reading two:** every test in every session deletes `data/habits.json` first,
  and the paragraph is just where it happens to be written down.
- **Why it matters:** the whole point of the fixed `trackedDay` is "the same test
  run gives the same answer forever", and reading one gives a suite that passes
  once and then fails - the exact class of defect the constraint exists to
  prevent. `test-runner` will catch it during the step-6 loop (the second
  invocation goes red) and the Builder adds the resets for free, so it does not
  escape, but a Gate 1 sentence is cheaper than a retry and removes the risk that
  a favourable ordering hides it.
- **Suggested wording:** replace the paragraph's first clause with "Every
  criterion is measured from the seed state, so every test in every session
  deletes `data/habits.json` before it runs and lets `readStore()` copy
  `data/habits.seed.json` back."

## Worth a look

### B1 - `cut-habit-page`'s hint says what to do for done days and nothing for not-done days

- **Where:** spec.md, Session 2 cut points, `cut-habit-page`; against spec.md
  Screens and `c-2-3`
- **Owner:** pack-writer
- **The line:** "each with `data-date` set to that entry's date string and
  `data-done` set to `\"true\"` only where the entry is done"
- **Reading one:** `data-done={d.done ? "true" : "false"}` - what the Screens
  section requires ("`data-done` set to `\"true\"` or `\"false\"`").
- **Reading two:** set the attribute only on done cells and omit it otherwise,
  which is what "only where the entry is done" literally licenses. `c-2-3`
  demands "false on the other 5 cells", so the attribute must be present and
  read `"false"`; a student following the hint to the letter gets a red test with
  no sentence to reread.
- **Why it matters:** the hint is the only thing the student sees. This is the
  "a cut hint that names one thing implies replacing everything else" lesson.
  The Builder's own code will be right because it reads the Screens section, so
  step 6 stays green; the mismatch only shows when a person reads the guide.
- **Suggested wording:** "...and `data-done` set to the string `\"true\"` on a
  done entry and the string `\"false\"` on every other entry."

### B2 - Declared screen states with no testid and no criterion, including `habit-missing`

- **Where:** spec.json screens[0].states, screens[1].states and
  screens[1].elements[3]; spec.md Screens
- **Owner:** nothing
- **The line:** "`data-testid=\"habit-missing\"` when the endpoint answers 404",
  with `states` of loading / loaded / error on `sc-board` and loading / loaded /
  not-found / error on `sc-habit`.
- **Reading one:** loading and error are real states a test could read, so they
  need hooks the spec has not named.
- **Reading two:** only `loaded` is graded and the rest are prose, so the Builder
  picks any markup at all - including none.
- **Why it matters:** four of the seven declared states have no criterion, and
  `habit-missing` is the one with a named testid and still no criterion (`c-2-2`
  tests only the endpoint's 404). Nothing downstream reads a state that no
  criterion mentions, so `sc-habit` can ship with no not-found branch and grade
  green. Not blocking - the Builder can proceed - but it is a hole in what the
  project claims to teach.
- **Suggested wording:** add to Screens: "The loading state of each screen shows
  `data-testid=\"loading\"` and the error state `data-testid=\"error\"`", and add
  a `sc-habit` criterion: "screen /habits/no-such-habit displays an element with
  data-testid habit-missing", cut by `cut-habit-page`.

### B3 - Session 1 says it teaches the grid, but neither of its cuts touches JSX

- **Where:** spec.md, Session 1 Teaches and Cut points; spec.json session 1
  teaches[2]
- **Owner:** nothing
- **The line:** "rendering a grid from two nested arrays" as a session-1 teaching
  point, with `cut-week-dates` in `lib/week.ts` and `cut-streak-count` in
  `lib/streak.ts` as the only cuts.
- **Reading one:** the grid is demonstrated live and given to the student
  complete; the student's own work in session 1 is two pure functions.
- **Reading two:** the student writes the nested map, which nothing in the spec
  cuts.
- **Why it matters:** `c-1-4` and `c-1-5` target `sc-board` but are graded by
  library cuts, so the student types no JSX at all in session 1 and the nested
  map arrives only in session 2 for a single row. The linter counts cuts and
  minutes, not whether a taught concept is ever practised, so this ships as
  written. Session 1 is at 38.5 of 40 minutes, so this is a swap, not an
  addition: `cut-week-dates` could move to the board's day-cell map and leave
  `weekDates` given.
- **Suggested wording:** either drop the third `teaches` entry from session 1, or
  move one cut into `app/page.tsx` so the grid is the thing the student writes.

### B4 - "refreshes only that habit's row" is not testable as written

- **Where:** spec.md, Session 3 Goal and `c-3-5`; spec.json session 3 goal
- **Owner:** nothing
- **The line:** "so a click on a day cell flips that day in `data/habits.json`
  and refreshes only that habit's row on screen `/`"
- **Reading one:** replace one item in React array state, as `cut-board-click`'s
  hint says.
- **Reading two:** refetch `GET /api/habits` after the POST and replace all four
  rows - which also leaves "the drink-water row's habit-streak text at
  `Streak: 5`" and so passes `c-3-5` identically.
- **Why it matters:** the session's third teaching point is "replacing one item
  inside React array state" and no criterion can distinguish it from a refetch,
  so a student who refetches is green. The hint pins the intent, so nothing
  breaks; the criterion just does not grade what the session claims to teach.
- **Suggested wording:** extend `c-3-5` with a clause a refetch fails, e.g.
  "...and screen / issues exactly one request to /api/habits over the whole
  interaction", or accept the refetch and drop the "only" from the goal.

### B5 - Whether the day cells on `/habits/[id]` are clickable is never decided

- **Where:** spec.md, Outcome (lines 11-14) against Session 3 Builds and
  `cut-board-click`
- **Owner:** nothing
- **The line:** "Clicking a cell flips that day between done and not-done, writes
  the change to `data/habits.json`, and updates that row's cell and streak.
  Screen `/habits/[id]` shows the same week and streak for one habit."
- **Reading one:** the click behaviour is a property of a day cell, so the cells
  on both screens toggle; `/habits/[id]` just is not the screen any criterion
  clicks.
- **Reading two:** only `/` toggles - the only click cut is `cut-board-click` in
  `app/page.tsx`, session 3 builds only `ep-habit-toggle`, and `sc-habit` is
  described as "shows".
- **Why it matters:** under reading one the Builder ships an interaction with no
  criterion, no cut and no hint on the single-habit page, and a student staring at
  a clickable cell that the guide never mentions. Harmless to grading either way.
- **Suggested wording:** add to Out of scope: "Toggling from `/habits/[id]`. Its
  cells are display only; `/` is the only screen that writes."

### B6 - Three of the seven library functions have signatures, four do not

- **Where:** spec.md, Data model, Library modules (lines 80-84)
- **Owner:** typecheck
- **The line:** "`lib/store.ts` exports `readStore`, `writeStore`, `findHabit`
  and `habitWeek`" - given after `weekDates(trackedDay)`,
  `streakOf(doneDates, trackedDay)` and `toggleDate(dates, date)` are each spelled
  out with their parameters.
- **Reading one:** infer them from the hints: `findHabit(habitId)` and
  `habitWeek(habit)` are called that way in `cut-api-habit-get` and
  `cut-api-toggle`, so `habitWeek` must fetch `trackedDay` itself.
- **Reading two:** `habitWeek(habit, trackedDay)` or `habitWeek(store, habit)`,
  which is the shape the caller would actually have on hand.
- **Why it matters:** the hints are written against one-argument calls, so a
  Builder choosing a different arity ships hints that do not compile in the
  student's editor. `tsc` over the skeleton catches the arity mismatch at step 8,
  which is why this is not blocking - but note it is the same underspecification
  that makes A2 possible.
- **Suggested wording:** spell all four out, as the other three modules already
  are: "`readStore(): Store`, `writeStore(store: Store): void`,
  `findHabit(habitId: string): Habit | null`, `habitWeek(habit: Habit):
  HabitWeek`, which reads `trackedDay` from the store itself."

### B7 - A session-3 criterion is graded by a session-2 cut

- **Where:** spec.json, `c-3-2`.cuts; spec.md Session 3, `c-3-2` and the Session
  2 note "The lookup earns a criterion the route does not share in session 3
  (`c-3-2`)"
- **Owner:** skeleton-check
- **The line:** "Cuts: `cut-toggle-dates`, `cut-api-toggle`,
  `cut-store-find-habit`."
- **Reading one:** the skeletons are cumulative, so by session 3
  `cut-store-find-habit` is already filled and listing it is documentation of a
  dependency, not a hole.
- **Reading two:** each skeleton opens the cuts its criteria name, so session 3's
  skeleton re-opens a session-2 cut the student already completed.
- **Why it matters:** it is the only cross-session cut reference in the spec, and
  the spec leans on it for session 2's grading-independence argument. Under
  reading two the student is asked to write `findHabit` twice; under reading one
  session 2's independence claim rests on a criterion that is not in session 2.
  Step 8's skeleton check compares the skeleton's reds against the declared cuts,
  so a mismatch surfaces there rather than shipping.
- **Suggested wording:** state the convention once in the Sessions preamble: "A
  criterion may name a cut from an earlier session as a dependency; only the cuts
  declared in a session are opened in that session's skeleton."

### B8 - `c-2-4` pins `Streak: 0`, which is what an unimplemented streak displays

- **Where:** spec.md, Session 2, `c-2-4`; spec.json session 2 criteria[3]
- **Owner:** skeleton-check
- **The line:** "a data-testid habit-streak element whose text is exactly
  `Streak: 0`"
- **Reading one:** `read-pages` is the gap case, so 0 is the meaningful answer and
  the criterion is fine.
- **Reading two:** 0 is also the value a broken `streakOf`, an empty
  `cut-streak-count` and any plausible skeleton fallback all produce, so the
  criterion is satisfiable without the streak working.
- **Why it matters:** session 2 asserts a streak on screen exactly once and picks
  the one habit whose streak is the trivial value; nothing in the session pins a
  non-zero streak through the UI. This is the "the fallback must not accidentally
  pass the test" lesson, and step 8's skeleton check is what would catch a
  fallback that renders `Streak: 0` - so it does not escape, but choosing a
  different habit makes the criterion stronger for free.
- **Suggested wording:** point `c-2-4` at `/habits/stretch`, asserting
  `Stretch` and `Streak: 1`, and keep `c-2-3` on `read-pages` for the
  false-cell coverage.

### B9 - Only a missing `date` is a 400; a malformed or out-of-week date is a 200

- **Where:** spec.md, Endpoints (line 94) and `cut-api-toggle`; spec.json
  `c-3-4`
- **Owner:** nothing
- **The line:** "`ep-habit-toggle` answers 404 for an unknown habit id and 400
  when the body carries no `date` string."
- **Reading one:** the only 400 is a missing or non-string `date`; `"hello"` or
  `"2026-01-01"` is a valid request and gets written into `doneDates`.
- **Reading two:** `date` must be a `YYYY-MM-DD` string inside the tracked week,
  since Out of scope says "Any week other than the tracked week", and anything
  else is a 400.
- **Why it matters:** under reading one the store accumulates junk dates that no
  screen can ever remove, since the only way to untoggle a date is to click its
  cell and only the seven tracked dates have cells. No criterion covers it, so
  whichever way the Builder reads it ships. Low cost either way - it takes a POST
  by hand to reach.
- **Suggested wording:** add to the Endpoints paragraph: "A `date` that is not a
  `YYYY-MM-DD` string, or that falls outside the tracked week, is also a 400."
  Then add the malformed case to `c-3-4`.
