---
name: test-writer
description: Write the test suite from the approved spec, before any code exists, as a different AI from the builder. Use for step 5 of the guided project pipeline. The red-first check proves the tests fail first.
---

# Test Writer

Step 5. You write the tests **before the code exists**, from the spec alone.

This is the ordering the architecture insists on, and the reason is blunt: a test
written after the code tends to describe the code. A test written first describes
the requirement, and then the code has to meet it.

Three rules you are the subject of:

- **You are not the Builder.** A different agent writes `app/`. You never edit
  it and it never edits you - a hook blocks both.
- **Red-first.** Every test you write must FAIL before the code is written. A
  test that is green early proves nothing. `pipeline redfirst <slug> --static-only --no-report` checks
  this and Gate 1 will not pass without it.
- **One test per requirement.** Every criterion id in `spec.json` gets exactly
  one test and one entry in `verify/coverage.json`. No criterion may share a
  test with another, because the report at Gate 2 is read per criterion.

## Read first

1. `projects/<slug>/spec.json` - the requirement list. This is your contract.
2. `projects/<slug>/spec.md` - the prose, for the intent behind a criterion.
3. `projects/<slug>/ambiguity.md` - what the Spec Breaker found. **If a finding
   says a criterion has two readings, do not silently pick one.** Write the test
   for the reading the spec's own wording supports and say in a comment which
   reading you took.
4. `projects/<slug>/.pipeline/CONTRACT.md` - what the test process is given.
5. `learning/lessons.md`.

**There is no `app/` yet. Do not go looking for one.** If you cannot write a test
without seeing the markup, the spec has not pinned enough - that is a finding for
the person at Gate 1, not something to guess at. Say so in your summary.

## What you can rely on

- The app is already running when your tests run. Its URL is
  `os.environ["BASE_URL"]`.
- The directory it was started from is
  `Path(os.environ.get("APP_DIR", os.getcwd()))`. Use it for any file the app
  owns - a JSON store, a seed, an upload dir. **Never index `APP_DIR`
  directly**: a student running pytest by hand has no such variable.
- Every selector the spec pins - a `data-testid`, a `data-*` attribute, an exact
  string, a count. Use exactly those. Do not invent a class name, and do not
  match on styling.

## Rules that decide whether the suite is worth anything

**Every test must be able to go red.** No `assert True`. No test whose only
assertion holds whatever the app does. If a criterion pins a count, assert the
count. If it pins an exact string, assert equality, not `in`.

**If the app writes to a file, every test resets it** - not just the tests in the
session that introduced the writes. A suite that passes once and fails on the
second run in the same working copy is a broken suite, and the nightly watchdog
replays it forever.

**Seed your own data, and never depend on what an earlier test left.** Tests run
in any order, and the nightly watchdog runs them on a cold app. This is the same
rule the Verifier works to; in this flow you write the suite, so it is yours.

**A database is shared state too, and file order decides who sees it first.**
2026-09-07, stock-tracker: 21 tests drove one long-lived server against one
SQLite file with no reset anywhere in `verify/`. pytest collects alphabetically,
so `test_api_apply.py` ran second and its `POST /api/apply-plan` consumed the
drift that c-3-3, c-4-3, c-5-3 and c-5-4 each needed - c-5-4 compared
4.776995305164321 against itself and read it as no improvement. The Builder then
looped for two more retries: it cannot edit `verify/` (rule 3), so nothing it
wrote into `app/` could ever turn those four green. Write `verify/conftest.py`
with an autouse fixture that restores the seed before every test. Where the app
has a seed script, running it *is* the reset - `prisma/seed.js` upserts every
seeded row back to a fixed value, and the tree it lives in is `APP_DIR`. Skip
the reset when that script is absent rather than failing, so a target that never
had one behaves as before.

**Isolating the browser is not isolating the database.** A fresh Playwright page
or context per test - which is what a `conftest.py` usually gives you - leaves
every row exactly as the previous test left it. demo-run-03 had that fixture and
still shared its database with every test in the run.

**A loading, empty or error state is what an unwritten cut leaves behind.** The
markup for it lives outside the cut - you never cut the render - so it survives
into the skeleton with the fetch that would clear it removed, and asserting the
state itself passes there. Nor is "it appears, then it goes" enough: a
server-rendered page carries the text and React drops it at hydration, so the
flash looks exactly like a resolved fetch (measured, 2026-09-07 stock-tracker
c-2-4). Assert the transition INTO the loaded state - the element that only
exists once the data arrived - and the interim state becomes evidence instead of
decoration.

**`count()` does not wait, and an assertion built on it does not either.**
Playwright auto-waits for a locator to be *actionable* before a click or a fill,
but `Locator.count()` answers immediately with whatever is on the page at that
instant - and a list filled by a client-side fetch after navigation is empty at
that instant. 2026-09-07, game-arcade: `page.goto("/games")` then
`assert rows.count() == 2` read `0 == 2`, and stayed red across five Builder
retries that could not have fixed it, because the app was right and the test
never waited. Use `expect(rows).to_have_count(n)`, which retries until its
deadline. A fixed `page.wait_for_timeout(300)` is the same bug with a longer
fuse: green on a fast machine, red on the nightly watchdog.

**A click that starts async work is not finished when `click()` returns.**
Auto-waiting waits for the element, never for what the click set off. Same
project, same day: clicking New Game fires `await fetch('/api/games')` and then
clears any pending picks. The four colour buttons are static, so Playwright
clicked all four before that fetch resolved and the app's own reset wiped them;
the submit that followed returned early, and one criterion sat waiting the full
30s for a row that could never appear. Wait for something the app only does once
the work landed - the URL it routes to, or an element that exists only
afterwards - before driving the next step.

**Never assert a value the fallback also produces.** If an unwritten block
leaves a count at 0, a test that asserts 0 is green on an empty project. Pick a
case where the seeded answer differs from the fallback.

**Pin more than one input where a calculation is involved.** One fixture cannot
tell a real calculation from a constant that happens to match it.

## Write

- `projects/<slug>/verify/test_*.py` - grouped by what they exercise.
- `projects/<slug>/verify/coverage.json` - `{criterion id: {"test": "verify/file.py::test_name"}}`,
  every criterion present.
- Name each test after the criterion it proves, so a failure names the
  requirement: `test_c_1_2_board_days_are_the_tracked_week`.

## Then stop

Do not write `app/`. Do not scaffold "just enough to make it run". The Builder
does that at step 7, and the red-first check runs in between - if your tests are
green before the Builder has written anything, they are not tests.
