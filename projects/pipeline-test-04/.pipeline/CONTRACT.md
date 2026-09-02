# Artifact contract

Every step reads and writes files under `projects/<slug>/`. Nothing is passed
agent-to-agent in conversation. If a file is not on disk, the step did not happen.

The names below are this pipeline's. `requirements_doc.md` uses a different set
for the same artifacts; both are accepted where it matters (ids and markers), and
the directories keep these names so the shipped projects stay valid:

| requirements_doc.md | here |
|---|---|
| `ideas/` | `ideas/` |
| `spec/` + ambiguity notes | `spec.md`, `spec.json`, `ambiguity.md` |
| `tests/`, `e2e/` | `verify/` |
| `solution/` | `app/` |
| `student/` | `skeleton/` |
| `guide/` | `pack/` |
| `gates/` | `.pipeline/state.json` + `.pipeline/approved/` |
| `tools/` | `pipeline/` |
| session `S03` | session `n` (or `"id": "S03"`, checked against `n`) |
| requirement `S03-AC01` | `c-3-1` **or** `S03-AC01` |
| student task `S03-T01` | `cut-<kebab>` **or** `S03-T01` |

```
projects/<slug>/
  stack.json                  step 0   person           the stack, sessions, minutes
  ideas/idea-01..05.md        step 1   Idea Generator
  ideas.json                  step 1   idea check       SCRIPT
  idea.md                     step 2   person           the one picked at Gate 0
  spec.md                     step 2   Spec Writer      human-readable spec
  spec.json                   step 2   Spec Writer      machine contract
  lint.json                   step 2   spec linter      SCRIPT  + session minutes, spec hash
  ambiguity.md                step 3   Spec Breaker     every finding names its Owner
  gate1.json                  step 4   gate 1 rule      SCRIPT  the stopping rule's verdict
  app/                        step 5   Builder          the working project
  verify/                     step 5   Test Writer      written BEFORE app/ - Builder cannot write here
  redfirst.json               step 5   red-first check  SCRIPT
  mutation.json               step 8   mutation check   SCRIPT
  leak-scan.json              step 10  leak scan        SCRIPT
  guide-lint.json             step 11  guide linter     SCRIPT
    test_*.py
    coverage.json                                       criterion id -> test node id
  results.json                step 6   test runner      SCRIPT
  skeleton/                   step 8   cutter           SCRIPT
    .cut-manifest.json
  skeleton-results.json       step 8   cutter           SCRIPT
  pack/                       step 9   Pack Writer      instructor session guide
  deploy.json                 step 10  deploy check     SCRIPT
  .pipeline/state.json        all      orchestrator     phase, retries, step_runs, gates
  .pipeline/breaker-begin.json step 2  orchestrator     the spec hash the Breaker opened against
  .pipeline/ambiguity-meta.json step 3 orchestrator     the spec hash the report reviewed
  .pipeline/SPEC_FROZEN       step 4   orchestrator     the approved spec hash - the spec is read-only
  .pipeline/approved/         step 4   orchestrator     the approved bytes, kept
```

## Student task markers - two forms

Both are cut by `pipeline/cutter.py`. The first is what the shipped projects use;
the second is `requirements_doc.md`'s:

```ts
// >>> CUT cut-api-todos-list
  body = await store.all()
// <<< CUT cut-api-todos-list
```

```python
# >>> STUDENT S03-T01 START
#     goal: put every todo into the body and answer 200
    body = await store.all()
# <<< STUDENT S03-T01 END
```

The `goal:` line sits inside the block and is removed with it. What the student
reads is the task's `hint` from `spec.json` - the wording a person approved at
Gate 1, not a comment that can drift from it.

## The spec is frozen at Gate 1

`pipeline gate <slug> 1 approve` hashes `spec.json` and `spec.md` together,
copies both (plus `lint.json`, `ambiguity.md`, `gate1.json`) into
`.pipeline/approved/`, and writes the hash to `.pipeline/SPEC_FROZEN`.

From that moment:

* the write guard refuses any edit to `spec.md` or `spec.json`, **with or
  without a subtree lock** - Phase 1 sets no lock at all, which is how a
  finished Spec Writer was able to wake up an hour later and copy a rejected
  round over the live files;
* every command in the code and pack phases checks the hash first and refuses to
  run on a mismatch, because `app/` and `verify/` were built against the
  approved spec;
* `pipeline revise <slug>` is the only way to reopen it, and it archives the
  round and resets Gate 1 so the new spec is approved on its own merits.

Check it any time with `pipeline spec-status <slug>`.

## ambiguity.md - the Owner line

Every finding carries `- **Owner:** <checker>`, naming the downstream checker
that would catch it if the spec shipped as written. One of `spec-linter`,
`return-safety`, `typecheck`, `cutter`, `skeleton-check`, `test-runner`,
`deploy-check`, `pack-writer`, `nothing`.

`pipeline gate1-check` parses them and applies the stopping rule: **reject when
a blocking finding is owned by `nothing`; approve when every remaining finding
sits in a column a downstream checker owns.** A missing or unrecognised owner
reads as `nothing`, so the check fails closed.

The report is bound to the spec it read. A clean `pipeline lint` opens the pass
against that hash and clears any earlier report; `pipeline breaker <slug> end`
records the hash and refuses if the spec changed during the pass. `pipeline
next` and Gate 1 both treat a report whose hash does not match the spec on disk
as not done.

## spec.json

The only file downstream scripts parse. `spec.md` is for the person at Gate 1.
The linter checks they agree.

```json
{
  "slug": "kebab-case",
  "title": "string",
  "track": "react | node | fullstack | ai",
  "sessions_planned": 4,
  "stack": ["next", "react", "typescript"],
  "source": "path/to/reading-material.md or null",
  "code_checks": ["utc-dates"],
  "endpoints": [
    {"id": "ep-todos-list", "method": "GET", "path": "/api/todos",
     "request": null, "response": "Todo[]", "status": [200]}
  ],
  "screens": [
    {"id": "sc-list", "route": "/", "elements": ["todo list", "add input"],
     "states": ["empty", "loaded", "error"]}
  ],
  "sessions": [
    {
      "n": 1,
      "title": "string",
      "goal": "one sentence",
      "teaches": ["useState", "controlled inputs"],
      "builds": ["ep-todos-list", "sc-list"],
      "criteria": [
        {"id": "c-1-1",
         "check": "GET /api/todos returns 200 with a JSON array of Todo",
         "target": "ep-todos-list",
         "cuts": ["cut-api-todos-list"]}
      ],
      "cuts": [
        {"id": "cut-api-todos-list",
         "file": "app/api/todos/route.ts",
         "hint": "Return every todo from the store as JSON"}
      ]
    }
  ]
}
```

### Id conventions, enforced by the linter

| Kind      | Pattern              |
|-----------|----------------------|
| endpoint  | `ep-<kebab>`         |
| screen    | `sc-<kebab>`         |
| criterion | `c-<session>-<k>`    |
| cut       | `cut-<kebab>`        |

## Cut markers

The Builder writes these into the final code. The cutter removes what is between
them. Any comment style works.

```ts
// >>> CUT cut-api-todos-list
  const todos = await store.all()
  return Response.json(todos)
// <<< CUT cut-api-todos-list
```

becomes, in the skeleton:

```ts
  // TODO(cut-api-todos-list): Return every todo from the store as JSON
```

Markers must be balanced, must not nest, and every `cut` id declared in
`spec.json` must appear exactly once in the code. The cutter fails otherwise.

**Never put a typed function's only `return` inside the markers.** The skeleton
then has a function that returns nothing, does not compile, and the student's
whole app stops building - no red test, no build at all. Declare a typed
fallback above the markers and cut the assignment that feeds it:

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

The fallback must not accidentally pass the test - a 501 and `ok: false` fail
the criterion, which is what the skeleton needs. `cutter.scan_return_safety`
refuses to generate a skeleton otherwise, and it needs no toolchain, so it
catches this on a fresh clone where `tsc` cannot run.

## code_checks - constraints a test suite cannot see

Optional. A list of named static checks, run over `app/` at step 6, so a
violation lands in the Builder/test-runner loop instead of shipping.

| Name | What it enforces |
|---|---|
| `utc-dates` | No local-time `Date` accessors and no reading the real clock. For any project doing date arithmetic: `new Date("2026-08-26").getDay()` is Wednesday in IST and Tuesday west of Greenwich, so a weekday derived with local accessors passes here and fails for students |

The linter rejects an unknown name (`E120`). Omitting the key runs nothing. This
is a fixed registry, not a pattern engine - a spec cannot supply its own regex.

## What the test process is given

The test runner boots the target and runs `verify/` with exactly two things in
the environment:

| Variable | Meaning |
|---|---|
| `BASE_URL` | where the booted app is answering |
| `APP_DIR` | the directory the app was started from - `app/` or `skeleton/` |

`APP_DIR` exists because the same suite runs from three different working
directories: the project root against `app/`, the project root against
`skeleton/` (the cutter copies `verify/` into the skeleton), and the skeleton
itself when a student runs pytest by hand. No relative path to the app's own
files is correct for all three.

**The pipeline sets both variables for its own two runs only.** A student running
pytest by hand inside their copy has no `APP_DIR`, so a suite that indexes
`os.environ["APP_DIR"]` dies on a `KeyError` in exactly the run nothing in the
pipeline exercises. Resolve it with a fallback:

```python
APP_DIR = Path(os.environ.get("APP_DIR", os.getcwd()))
STORE = APP_DIR / "data" / "habits.json"
```

`os.getcwd()` is right for the student because they run pytest from inside the
skeleton, which *is* the app directory. Both pipeline runs pass the variable, so
they never take the fallback.

If the app writes to a file, **every test in every session resets it.** A suite
that passes once and fails on the second run in the same working copy is broken:
the nightly watchdog replays it forever.

## Runtime state must not ship

`data/` is deliberately **not** excluded from the skeleton - a seed file the
student needs usually lives there. What must not ship is the *live* copy that
step 6's tests leave mutated.

The project's own `app/.gitignore` is the declaration. The cutter and the deploy
check both honour it: a gitignored file is runtime state and is left out of
`skeleton/` and out of the step-10 fresh copy, while a tracked file beside it is
copied. So a project with a mutable store keeps them apart:

```gitignore
data/habits.json          # the live store - never ships
!data/habits.seed.json    # the seed - always ships
```

Supported patterns are a path, a basename glob, a trailing-slash directory, and
`!` to un-ignore, with the last match winning. No `.gitignore` means nothing is
excluded. The static return-safety scan still reads every source file, ignored or
not - a bad cut marker is a bad cut marker wherever it lives.

## coverage.json

Written by the Verifier. Joins spec criteria to real tests.

```json
{
  "c-1-1": {"test": "verify/test_api_todos.py::test_list_returns_array"},
  "c-1-2": {"test": "verify/test_ui_list.py::test_renders_one_row_per_todo"}
}
```

Every criterion in `spec.json` must have an entry. The test runner keys
`results.json` by criterion id so Gate 2 reads criteria, not test names.
