# Ambiguity report - habit-tracker

**Verdict:** 1 blocking, 5 worth a look

This is a tight spec. The three streak cases arithmetic out correctly against the
seed (5 / 0 / 0 / 1), every toggle criterion's expected streak is right,
`2026-08-26` really is a Wednesday and `2026-08-30` really is that week's Sunday,
every cut has a distinct criteria signature (no linter E110), no fallback is
reachable by a proper subset of a criterion's cuts, and the eight fallbacks all
keep the return outside the markers. The findings below are about the test
harness the criteria assume, not about the domain logic.

## Blocking

### A1 - Every test must "delete data/habits.json resolved from the target", and nothing tells a test which target it is

- **Where:** spec.md, Sessions preamble (the sentence in bold), and every criterion that depends on seed state - c-1-6, c-3-1, c-3-2, c-3-3, c-3-4
- **Owner:** nothing
- **The line:** "**Every test in every session deletes that file - resolved from the target the suite is running against, `app/` or `skeleton/` - before it runs**"
- **Reading one:** the suite deletes one path, the one for the target it believes it is testing - in practice a literal `app/data/habits.json` relative to the pytest rootdir, because `app/` is what the Verifier develops against.
- **Reading two:** the suite deletes every candidate path unconditionally, because it cannot tell the targets apart, so `app/data/habits.json` and `skeleton/data/habits.json` both go.
- **Why it matters:** the test process is given exactly one piece of information about its target - `BASE_URL` (`pipeline/test_runner.py` line 229 passes `BASE_URL` and nothing else, with `cwd=project`). There is no target name, and the suite runs from three different (cwd, verify-location) combinations: app run = `cwd=project` with `project/verify`; skeleton run = `cwd=project` with `skeleton/verify` (the cutter copies verify into the skeleton); the student = `cwd=skeleton` with `skeleton/verify`. So no single relative path resolves correctly in all three, and the spec asks for a resolution the test author has no input for. Reading one is the dangerous branch and it is invisible: the app suite goes green, and the skeleton suite also "passes" its check, because `expected_skeleton_results` requires *every* criterion to fail on the skeleton (all 16 have cuts) - so a skeleton whose store is never reset, carrying the leftovers the app run left behind, cannot be distinguished from a correct one. The student then fills `cut-week-dates` exactly right and c-1-2 stays red, because the store on disk says `trackedDay: 2026-09-06` from c-1-6's fixture. The other branch of the same mistake - deletes that land nowhere at all - is loud and cheap, because c-1-6 rewrites `trackedDay` and every later criterion goes red at step 6; it is only the app-path-hardcoded branch that ships. c-3-4 has the same dependency for reading, not deleting: it must locate the store to compare its bytes.
- **Suggested wording:** "Every test resets the store before it runs by deleting all of `app/data/habits.json`, `skeleton/data/habits.json` (both relative to the pytest rootdir) and `../data/habits.json` relative to the directory the test file lives in; deleting an absent file is a no-op, so the same three deletions are correct whether the suite runs against `app/`, against `skeleton/`, or from inside a student's copy. A test that reads or writes the store resolves it the same way and uses whichever of those paths exists."

## Worth a look

### B1 - "Only the cuts declared in a session are opened in that session's skeleton" - there is one skeleton and all eight cuts are open in it

- **Where:** spec.md, Sessions preamble, last paragraph before Session 1
- **Owner:** pack-writer
- **The line:** "Only the cuts declared in a session are opened in that session's skeleton; an earlier session's cut is already filled by the student who reached this one."
- **Reading one:** step 8 produces three skeletons, one per session, each with only that session's cuts opened.
- **Reading two:** step 8 produces one `skeleton/` with all eight cuts opened, and `by_session` in the manifest is only a grouping of the hints.
- **Why it matters:** reading two is what `pipeline/cutter.py` does - one `skeleton/` tree, every marker replaced by its TODO, and `expected_skeleton_results` requires all 16 criteria to fail. The grading reasoning in the spec is unaffected (it holds for a student moving forward through the file), but the session-1 student opens a tree that already contains the session-2 and session-3 TODOs and 11 criteria that are red for reasons nothing has taught them yet. That mismatch surfaces at step 9, when the Pack Writer writes per-session guides against a single skeleton and has to invent the story.
- **Suggested wording:** "Step 8 cuts one skeleton with all eight cuts open. A session's guide names only that session's cuts; the later TODOs are visible in the tree and the guide says so, and criteria from later sessions are expected red until their session."

### B2 - "data/habits.json is absent from every shipped copy" names a step that does not exist

- **Where:** spec.md, Data model, the paragraph after the seed
- **Owner:** nothing
- **The line:** "anything that packages `app/` deletes it first - so the first read of a fresh copy always re-seeds, and no student ever opens a board built from a test run's leftovers"
- **Reading one:** the guarantee holds because some pipeline step strips the live store.
- **Reading two:** the guarantee holds because the file happens not to exist when packaging runs.
- **Why it matters:** neither is true. `cutter.walk_source` copies every file under `app/` except `node_modules/.next/.git/dist/build/.turbo`, and `deploy_check.EXCLUDE` is the same list, so `app/data/habits.json` - which exists after step 6, holding whatever the last test left - is copied into `skeleton/` and into the step-10 fresh copy. `.gitignore` does not help; nothing here goes through git. Grading still works if A1 is fixed, because each test deletes the store first, so the damage is limited to the student's first manual look at `/`: September dates, or `meditate` already done. No checker looks at the contents of that file.
- **Suggested wording:** "The suite deletes `data/habits.json` before each test and again after the last test, so `app/` holds no live store at rest and neither the skeleton nor a packaged copy can carry one."

### B3 - Nothing verifies the one constraint the idea called make-or-break: UTC-only date arithmetic

- **Where:** spec.md, Out of scope (the clock rule), Data model (the UTC-accessor rule), and both session-1 cut hints
- **Owner:** nothing
- **The line:** "any date arithmetic uses the UTC accessors (`getUTCDay`, `setUTCDate`) or plain string arithmetic, so no computed date changes with the machine's timezone"
- **Reading one:** the rule is graded somewhere, so an implementation using `getDay()`/`setDate()` will be caught.
- **Reading two:** the rule is prose only, and a local-time implementation is green in a UTC CI box.
- **Why it matters:** reading two is the case. Every criterion runs in the harness's own timezone, the Verifier cannot set the server's `TZ` (`test_runner.boot` fixes the child env), and a `new Date("2026-08-26").getDay()` implementation is right in UTC and a day out west of Greenwich - which is exactly the failure idea.md says "would pass here and fail for students". The blast radius is smaller than it looks, because both date functions are cuts, so the shipped skeleton's live code contains no date arithmetic: what ships wrong is `app/` and whatever model answer the pack writes from it. It is not an ambiguity for the Builder - the spec says it three times - it is a property with no assertion behind it, so it needs a human at Gate 3 rather than a criterion.
- **Suggested wording:** "No criterion can pin this: the suite cannot set the server's timezone. It is a read-the-code check - at Gate 3, `lib/week.ts` and `lib/streak.ts` must contain no local-time accessor (`getDay`, `getDate`, `setDate`, `getMonth`) and no zero-argument `new Date()`."

### B4 - The toggle's accepted date set is hard-coded in one place and derived in another

- **Where:** spec.md, Endpoints (paragraph 2) and spec.json `ep-habit-toggle.request`, against the `cut-api-toggle` hint
- **Owner:** nothing
- **The line:** "`ep-habit-toggle` accepts exactly one set of dates: the seven `YYYY-MM-DD` strings of the tracked week, `2026-08-24` through `2026-08-30`."
- **Reading one:** the route compares `date` against the seven literal strings.
- **Reading two:** the route compares `date` against `weekDates(store.trackedDay)`, which is what the cut hint says.
- **Why it matters:** no criterion separates them - c-3-4's `2026-08-31` is a 400 either way, and no test toggles while a fixture has moved `trackedDay`. So both ship green, but the student's hint names `weekDates(store.trackedDay)`; if the Builder's live code around the cut hard-codes the array instead, the hint points at a function the file does not use, and the one place the project would have reused its own week arithmetic is a literal. Nothing downstream reads the two against each other.
- **Suggested wording:** "The accepted set is always `weekDates(store.trackedDay)` - with the seed that is `2026-08-24` through `2026-08-30`. The route must not hard-code those seven strings."

### B5 - Session-3 criteria under-declare their dependency on session-2 cuts

- **Where:** spec.json, session 3, `c-3-1`, `c-3-3`, `c-3-5` (and `c-3-2` in the other direction)
- **Owner:** nothing
- **The line:** "A criterion may name a cut declared in an earlier session as a dependency."
- **Reading one:** a criterion's `cuts` list is its full dependency set, earlier sessions included - which is how `c-3-2` is written, naming `cut-store-find-habit`.
- **Reading two:** a criterion's `cuts` list is only the cuts it is meant to gate in its own session, and earlier dependencies are named or not as convenient.
- **Why it matters:** the spec does both. The toggle route calls `findHabit` on every success path, so `c-3-1`, `c-3-3` and `c-3-5` fail if `cut-store-find-habit` is empty, yet only `c-3-2` names it; and `c-3-2`'s "a following GET /api/habits/drink-water" needs `cut-api-habit-get`, which it does not name. No checker sees this - `expected_skeleton_results` only asks whether a criterion has any cuts at all, and every criterion here does - so the consequence is confined to what the pack tells a student a red criterion depends on.
- **Suggested wording:** either list the full dependency set on all four (`c-3-1`, `c-3-3`, `c-3-5` gain `cut-store-find-habit`; `c-3-2` gains `cut-api-habit-get`), or drop `cut-store-find-habit` from `c-3-2` and state once that session-3 criteria list only session-3 cuts.
