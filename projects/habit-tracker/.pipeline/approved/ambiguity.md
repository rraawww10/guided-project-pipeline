# Ambiguity report - habit-tracker

**Verdict:** 1 blocking, 7 worth a look

Round 4 closes all six of round 3's findings, and I re-derived the arithmetic
rather than trusting it: `2026-08-26` is a Wednesday, `2026-08-30` is that week's
Sunday, `2026-08-31` is the Monday of the `2026-09-06` week, and the seed gives
streaks 5 / 0 / 0 / 1. Every toggle expectation checks out (`stretch`+08-25 -> 2,
`drink-water`-08-26 -> 0 with 2 in-week done days, `read-pages` 3 then 0). Every
cut has a distinct criteria signature, and for each of the 16 criteria I emptied
each declared cut in turn with the rest filled: all 38 dependencies are
load-bearing and no criterion has a redundant cut, including the two that make it
work (`c-3-2`'s "2 days marked done" clause is what keeps `cut-toggle-dates`
non-redundant there, and `c-3-4`'s 404 is what keeps `cut-week-dates`
non-redundant). I also checked the round-4 claims against the code that has to
honour them: `APP_DIR` really is passed (`pipeline/test_runner.py:238`),
`gitignore_matcher` really does exclude `data/habits.json` and un-ignore
`data/habits.seed.json` in both the cutter and `deploy_check.fresh_copy`, and
`code_check.check_utc_dates` really does scan the member list the spec quotes.
The findings below are all outside the graded paths.

## Blocking

### A1 - The third of the three runs the harness story rests on has no `APP_DIR`

- **Where:** spec.md, Sessions, "How the suite resets the world"; and every criterion that resolves the store - c-1-6, c-3-4
- **Owner:** pack-writer
- **The line:** "No path relative to the test file or to the project root is correct, because the same suite runs from three places - the project root against `app/`, the project root against `skeleton/`, and a student's own copy from inside it - and `APP_DIR` is the only thing that names the right one in all three."
- **Reading one:** `APP_DIR` is always set, so the suite reads it directly (`Path(os.environ["APP_DIR"])`) and the third case works because something sets it there too.
- **Reading two:** `APP_DIR` is set only by the pipeline, so the suite must fall back to something for a hand run - `os.environ.get("APP_DIR", os.getcwd())`, correct when the student runs pytest from inside their copy.
- **Why it matters:** only two of the three runs are pipeline runs. `pipeline/test_runner.py:238` sets `BASE_URL` and `APP_DIR` for the `app/` run and the `skeleton/` run; nothing sets either variable when a student runs pytest by hand inside `skeleton/`, which the spec names as the third place and the contract repeats. Under reading one every test in that run dies on a `KeyError` before it reaches an assertion, and the student loses the fill-the-cut-watch-it-go-green loop the whole skeleton exists for. Both pipeline runs are green either way, so step 6 and step 8 cannot tell the two readings apart. What can: the session guide has to tell the student how to run the suite, and it has to name `BASE_URL` for the same reason - so the pack is where the missing value gets supplied, and a person reads it at Gate 3. Say which of the two it is, or the Pack Writer invents it at step 9 with no way to test the answer.
- **Suggested wording:** "The suite resolves the store as `os.environ.get("APP_DIR", os.getcwd())`, so the pipeline's two runs use the variable and a student running pytest from inside their own copy needs no environment at all beyond `BASE_URL`."

## Worth a look

### B1 - `HabitWeek` has no declared home, and the wrong one fails the client build

- **Where:** spec.md, Data model, the paragraph naming the project layout and the types block that follows
- **Owner:** test-runner
- **The line:** "Inside it sit `app/` (the App Router tree), `lib/` (the four library modules), and `data/` (the seed and the live store)."
- **Reading one:** the types live in `lib/store.ts` beside `readStore`, since that is the module whose functions produce them and `lib/` holds exactly four modules.
- **Reading two:** the types live in a fifth file, `lib/types.ts`, which nothing in the spec mentions and which contradicts "the four library modules".
- **Why it matters:** both screens are client components and both need the `HabitWeek` type. Under reading one they import it from the one module in `lib/` that imports node `fs`, and a `import { HabitWeek } from '@/lib/store'` written without `type` pulls `fs` into the client bundle - "Module not found: Can't resolve 'fs'" - which fails `npm run build`, and step 6 boots the target with `npm run build` before a single test runs. It is cheap to fix in the loop, but it is also cheap to decide here, and the decision also tells the Pack Writer which file the student opens first.
- **Suggested wording:** "The three types live in `lib/store.ts` and are imported with `import type` everywhere outside it, so no client component pulls node `fs` into its bundle."

### B2 - `cut-board-click` says what to do with the response body and never mentions its status

- **Where:** spec.md, Session 3, `cut-board-click`; spec.json session 3 cuts
- **Owner:** nothing
- **The line:** "set the `habits` state to the same 4 rows in the same order with only the clicked habit replaced by the `HabitWeek` in the response body"
- **Reading one:** the handler replaces the row unconditionally, because the only graded path is a 200 and `sc-board` declares one state.
- **Reading two:** the handler replaces the row only on a 200 and otherwise leaves the board alone, mirroring what `cut-habit-page` is told to do with a non-200.
- **Why it matters:** the spec spells this out for the other screen - "any other non-200 status leaves the page in its pre-response state" - and leaves the board silent, so a builder reads the asymmetry as deliberate and ships reading one. Session 3's own skeleton then punishes the obvious fill order: a student who fills `cut-board-click` before `cut-api-toggle` clicks a cell, gets the 501 fallback body `{ "error": "not implemented" }` into `habits` state, and the next render does `.days.map` on `undefined` and takes the whole board out. No criterion covers a non-200 from the click, so step 6 and step 8 are green on both readings and this ships as written.
- **Suggested wording:** "On any non-200 the handler leaves `habits` unchanged, so a click against an unfilled toggle route does nothing visible."

### B3 - `habit-name` on `/` is declared in both files and graded in neither

- **Where:** spec.md, Screens, `sc-board`; spec.json `screens[sc-board].elements`; against all six session-1 criteria
- **Owner:** nothing
- **The line:** "inside each row, `data-testid="habit-name"` with the habit name"
- **Reading one:** the element is required, so the board renders it.
- **Reading two:** the element is decoration, since nothing counts it or reads its text.
- **Why it matters:** every other element on the board is pinned by a criterion - `habit-row` by c-1-4, `habit-streak` by c-1-4 and c-3-5, `day-cell` with both data attributes by c-1-5 - and `habit-name` by none, on either screen's list for `/`. The board's nested map is live code handed over complete, so the one thing that would catch an omission is a person looking at the board, and no step does that before Gate 3. A habit board whose rows are unlabelled would ship 16/16 green. c-2-4 already pins `habit-name` on `/habits/[id]`, so the fix is one clause in an existing session-1 criterion, not a new one.
- **Suggested wording:** extend c-1-4 with "and a data-testid habit-name element whose text is exactly `Drink water`".

### B4 - "exactly these two lines" throws away the entries the other two projects needed

- **Where:** spec.md, Data model, the paragraph after the seed
- **Owner:** nothing
- **The line:** "`app/.gitignore` is where it is declared runtime state, and it must contain exactly these two lines"
- **Reading one:** the file is exactly two lines, and everything else a Next.js project ignores is handled elsewhere.
- **Reading two:** the two lines are the ones that matter for the store, added to the entries `create-next-app` generates.
- **Why it matters:** `node_modules` and `.next` are safe either way because `cutter.SKIP_DIRS` and `deploy_check.EXCLUDE` hard-code them, but nothing hard-codes `*.tsbuildinfo`, which is why both shipped projects carry it in `app/.gitignore` (`projects/recipe-box/app/.gitignore` is three lines: `node_modules`, `.next`, `*.tsbuildinfo`). Under reading one, `app/tsconfig.tsbuildinfo` - written by the step-6 build - is copied into `skeleton/` and into the step-10 fresh copy and committed with them, which is exactly the churn already visible on `fixtures/runner-check/skeleton/tsconfig.tsbuildinfo`. It breaks nothing, and no checker reads that file, so it ships.
- **Suggested wording:** "`app/.gitignore` keeps the generated Next.js entries (`node_modules`, `.next`, `*.tsbuildinfo`) and adds these two lines."

### B5 - What suppresses `habit-name` before the first response: `missing`, or a null habit

- **Where:** spec.md, Session 2, `cut-habit-page` hint and the skeleton-fallbacks table; Out of scope, last bullet
- **Owner:** test-runner
- **The line:** "Keep the `habit-name` element and the `habit-missing` element already in the file: when `missing` is `true` the page draws `habit-missing` and no `habit-name`, no `habit-streak` and no `day-cell`."
- **Reading one:** the live code renders `habit-name` whenever `missing` is `false`, which is literally what the sentence pairs it against.
- **Reading two:** the live code renders `habit-name` only when a habit has actually arrived, and `missing` selects between the habit branch and the not-found message.
- **Why it matters:** the fallback for this cut is `missing` starting as `false`, and "Before the first response arrives a screen draws no rows and no cells" is the state the page begins in with no habit at all. Reading one dereferences a null habit on first render - in the finished app it throws before the fetch resolves and takes c-2-3 and c-2-4 down, and in the skeleton it makes `/habits/no-such-habit` a 500 instead of a page. Step 6 catches the app half, which is why this is not blocking, but the skeleton half is invisible: c-2-3, c-2-4 and c-2-5 are expected red there either way, so `skeleton-check` cannot tell a page that renders quietly from a page that crashes.
- **Suggested wording:** "The page draws `habit-name`, `habit-streak` and the cells only when a habit has arrived, and `habit-missing` only when `missing` is `true`, so the pre-response state and the 404 state both draw neither."

### B6 - "Nothing is cached" is a claim about `readStore`, and the framework caches above it

- **Where:** spec.md, Data model, the `readStore()` paragraph; against c-1-6
- **Owner:** test-runner
- **The line:** "then re-reads and re-parses `data/habits.json` on every call and gives back a fresh object. Nothing is cached, so deleting the file resets the world even inside a running server."
- **Reading one:** the guarantee is a property of the module, and the route handler around it needs nothing declared.
- **Reading two:** the guarantee is a property of the response, so the handler must also be per-request - no build-time evaluation, no cached GET.
- **Why it matters:** step 6 does not run a dev server; `test_runner.boot` runs `npm run build` and then `npm run start`, so any handler the framework decides to evaluate at build time freezes the seed into the response. On Next.js 15 the default is on the spec's side - GET route handlers are uncached - but the version is prose in spec.md, `stack` in spec.json says only `next`, and a Next 14 scaffold would bake `/api/habits` at build time. c-1-6 is the criterion that would go red, so the loop owns it; a sentence naming the requirement saves the retry and tells the Pack Writer why the line is there.
- **Suggested wording:** "Each route handler is evaluated per request - the store is read on every call, never at build time - so a fixture written to `data/habits.json` between two requests changes the next response."

### B7 - Session 3 teaches node `fs` and the student writes no `fs`

- **Where:** spec.md, Session 3, Teaches; spec.json `sessions[2].teaches[1]`
- **Owner:** pack-writer
- **The line:** "**Teaches.** A POST route handler that reads and validates a JSON body; writing the store back to disk with node `fs`; replacing one item inside React array state."
- **Reading one:** the student writes the `fs` call, so one of session 3's cuts opens `writeStore`.
- **Reading two:** `writeStore` is session-1 live code and the student only calls it, so the teaching is a read-along of code that already exists.
- **Why it matters:** reading two is what the spec builds - `lib/store.ts` is session-1 setup, `writeStore` is not cut, and `cut-api-toggle`'s hint reduces the whole claim to "persist the whole `store` with `writeStore(store)`". That is a defensible design, but it is one of the three concepts the linter counted into session 3's 35.5 minutes, and the Pack Writer has to teach it from a file the student never edits. The mismatch surfaces at step 9, where a session guide either spends minutes on unwritten code or quietly drops a declared concept.
- **Suggested wording:** either "writing the store back to disk with node `fs` (read along in `lib/store.ts`; the student's own line is the `writeStore(store)` call)", or drop the concept and let session 3 teach two.
