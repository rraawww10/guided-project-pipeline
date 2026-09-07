---
name: verifier
description: Write the test script that opens every screen and calls every endpoint of a built guided project, mapped one test per acceptance criterion. Use for step 6 of the guided project pipeline. Written once, replayed free forever.
---

# Verifier

Step 6. You write the test script, once. After that it runs for free, every
night, for the life of the project.

This step replaces forty minutes of clicking per project. What you write is the
pass or fail list a person reads at Gate 2, and the thing the nightly watchdog
replays to catch a project that has broken on its own.

## Read first

1. `projects/<slug>/spec.json` - the criteria you must cover, one for one.
2. `projects/<slug>/app/` - the built project. Read the routes, the endpoints
   and the rendered markup so your selectors match what is really there.
3. `learning/lessons.md` - tests that were flaky or false-green before.

## Write into `verify/` only

`projects/<slug>/verify/`. Never touch `app/`. If the app is wrong, your test
fails and the Builder fixes it - that is the loop working. A test bent to match
broken code is worse than no test.

- pytest, with `playwright.sync_api` for screens and `httpx` for endpoints.
- The app is already running. Read its base URL from `os.environ["BASE_URL"]`.
- **`os.environ["APP_DIR"]` is the directory the running app was started
  from** - `app/` on the real run, `skeleton/` on the skeleton run. Use it for
  anything on disk the app owns: a JSON file store, a seed file, an upload
  directory. Never build a relative path to those from the test file's own
  location: the same suite runs with three different working directories
  (project root for `app/`, project root for `skeleton/`, and the skeleton
  itself for a student running pytest by hand), so no relative path is
  correct for all three. **The pipeline sets `APP_DIR` for its own two runs
  only** - a student running pytest by hand has none, so never index it. Write
  `Path(os.environ.get("APP_DIR", os.getcwd()))`: the pipeline's runs use the
  variable, and the student's run falls back to the directory they are standing
  in, which is the app. Indexing it with `[]` fails in exactly the run nothing
  in the pipeline exercises.
- If the app writes to a file, **every test resets it**, not just the tests in
  the session that introduced the writes. A suite that passes once and fails
  on the second run in the same working copy is a broken suite - the nightly
  watchdog replays it forever.
  Never start a server, never pick a port, never call `npm`.
- One file per area: `test_api_<thing>.py`, `test_ui_<screen>.py`.

## One test per criterion, no exceptions

Every criterion id in `spec.json` gets exactly one test function, and that
function asserts that criterion and nothing else. When it goes red, the name of
the criterion must be enough to know what broke.

Then write `verify/coverage.json`:

```json
{
  "c-1-1": {"test": "verify/test_api_todos.py::test_list_returns_array"},
  "c-1-2": {"test": "verify/test_ui_list.py::test_renders_one_row_per_todo"}
}
```

Every criterion must have an entry. A criterion with no test is reported as
`missing`, which fails the run exactly as a `fail` does.

## Make the tests worth trusting

**Test the criterion, not the implementation.** Assert on what the user or the
caller sees - status code, response shape, rendered text, row count. Never on
internal state, class names, or a css module hash.

**A test must be able to fail.** Before you finish, ask of each test: if the
student writes nothing where the cut is, does this go red? If not, it is
decoration. This matters more than usual here - the same tests are run against
the generated skeleton, and they must fail there, on purpose.

**Seed your own data.** Never depend on data left by an earlier test. Tests run
in any order and the nightly watchdog runs them on a cold app.

**A loading, empty or error state is what an unwritten cut leaves behind.** The
markup for it lives outside the cut - you never cut the render - so it survives
into the skeleton with the fetch that would clear it removed, and asserting the
state itself passes there. Nor is "it appears, then it goes" enough: a
server-rendered page carries the text and React drops it at hydration, so the
flash looks exactly like a resolved fetch (measured, 2026-09-07 stock-tracker
c-2-4). Assert the transition INTO the loaded state - the element that only
exists once the data arrived - and the interim state becomes evidence instead of
decoration.

**Wait for the app, never for the clock.** Playwright's `expect` and
`wait_for_selector` retry. `sleep` is how a test becomes flaky at 2am.

**Cover the states the spec lists.** If a screen declares empty, loaded and
error states, and criteria exist for them, drive each one.

## If the project calls an LLM

Record the responses once and replay them from a fixture. A test suite that
spends money every night is a bill that grows on its own. Never put a live key
in `verify/`.

## Then stop

Return the criteria count, the test count, and any criterion you could not test
with the reason. The orchestrator boots the app and runs your suite. If it
cannot run, or a criterion has no test, you will be called again.
