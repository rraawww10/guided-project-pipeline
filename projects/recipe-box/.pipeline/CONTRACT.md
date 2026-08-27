# Artifact contract

Every step reads and writes files under `projects/<slug>/`. Nothing is passed
agent-to-agent in conversation. If a file is not on disk, the step did not happen.

```
projects/<slug>/
  idea.md                     step 1   person
  spec.md                     step 2   Spec Writer      human-readable spec
  spec.json                   step 2   Spec Writer      machine contract
  lint.json                   step 2   spec linter      SCRIPT
  ambiguity.md                step 3   Spec Breaker
  app/                        step 5   Builder          the working project
  verify/                     step 6   Verifier         tests - Builder cannot write here
    test_*.py
    coverage.json                                       criterion id -> test node id
  results.json                step 6   test runner      SCRIPT
  skeleton/                   step 8   cutter           SCRIPT
    .cut-manifest.json
  skeleton-results.json       step 8   cutter           SCRIPT
  pack/                       step 9   Pack Writer      instructor session guide
  deploy.json                 step 10  deploy check     SCRIPT
  .pipeline/state.json        all      orchestrator     phase, retries, gate decisions
```

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
