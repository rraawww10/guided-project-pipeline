# Guided Project Automation

# 

## 1. What it is

A pipeline that turns a tech stack into a ready-to-teach course project:
working code, a student starter version, and an instructor guide.

Humans decide. AI drafts. Scripts check.

## 2. Why

Today, one project takes days of manual work. Testing it by hand takes ~40 minutes
and must be repeated after every fix.

Target: 1 project per day. Human time drops to ~2 hours of reviewing, not building.

**Measured, pipeline-test-04 (Tenpin, 2 sessions):** about 5 hours of pipeline
wall-clock end to end — 5 min for the five ideas, 122 min for four Gate 1 rounds,
160 min for the code phase, 20 min for handover. One project per day is met with
room to spare, and that run took four Gate 1 rounds; two of them were lost to a
pipeline defect since fixed.

The human time in that figure is the four gate decisions plus a timed dry run,
and it was not clocked, so the ~2 hours is still a target rather than a
measurement. What is measured is the claim it rests on: Gate 2 replaced hand-testing
with reading `results.json`, 12 requirements listed by id with the test that
proved each.

## 3. Who does what

| Role | Job |
| --- | --- |
| Human | Gives the tech stack. Approves ideas. Approves at 4 gates. |
| AI | Proposes ideas. Writes specs, tests, code, guides. |
| Script | Checks everything the AI produces. |

Two rules that never change:

- **The human gives the stack. The AI does not choose it.**
- **The AI gives the ideas. The human approves them. The AI does not pick.**

## 4. The flow

```
  0  Human gives stack + limits            human
  1  Idea generator (5 options)            AI
  2  GATE 0 — pick one idea                human
 ----------------------------------------------- PLAN
  3  Spec writer                           AI  → spec linter
  4  Ambiguity check                       AI  → read at Gate 1
  5  Test writer                           AI  → red-first check
  6  GATE 1 — approve plan + tests         human
 ----------------------------------------------- CODE
  7  Builder                               AI  → test runner
  8  Verifier (browser tests)              AI  → coverage + mutation
  9  GATE 2 — read pass/fail list          human
 ----------------------------------------------- HANDOVER
 10  Cutter (make student version)         script
 11  Guide writer                          AI  → guide linter
 12  Deploy check                          script
 13  Dry run (timed, by a person)          human
 14  GATE 3 — approve the pack             human
 ----------------------------------------------- LIVE
 15  Nightly check + feedback intake       script
```

## 5. The steps

| # | Step | What it does |
| --- | --- | --- |
| 0 | Stack input | Human states the stack, number of sessions, minutes per session. |
| 1 | Idea generator | AI proposes 5 project ideas that fit that stack. One page each. |
| 2 | **Gate 0** | Human picks one, or asks for 5 more. |
| 3 | Spec writer | Splits the project into sessions. Each session lists what to build, what students will type, and how long it takes. |
| 4 | Ambiguity check | A **different** AI lists sentences with two possible meanings. It only lists. It does not fix. |
| 5 | Test writer | Writes the tests from the spec. A **different** AI from the builder. |
| 6 | **Gate 1** | Human approves the spec, the ambiguity list, and the tests. |
| 7 | Builder | Writes the working code, session by session, until tests pass. |
| 8 | Verifier | Writes a browser test that clicks through every screen, then runs it. |
| 9 | **Gate 2** | Human reads the pass/fail list. ~2 minutes instead of ~40. |
| 10 | Cutter | Removes the marked parts to make the student starter version. No AI. |
| 11 | Guide writer | Writes the instructor guide: what to build, in what order, what to explain. |
| 12 | Deploy check | Fresh install from scratch. Proves it runs on another machine. |
| 13 | Dry run | A person who did not build it teaches one session from the guide, with a timer. |
| 14 | **Gate 3** | Human approves. Checks nothing continues without this. |
| 15 | Live | Nightly re-run of the saved browser test. Instructor feedback goes back to step 3. |

## 6. Rules the build must enforce

These exist because each one is a way the pipeline quietly fails.

1. **Tests are written before the code, by a different AI.** The builder cannot edit them. The tests folder is read-only to it.
2. **Red-first.** Every new test must fail before the code is written. A test that passes early proves nothing.
3. **The verifier is checked by a script.** It must cover every requirement, and it must go red when we deliberately break the code. Otherwise a useless test looks green.
4. **The cutter uses no AI.** The same code must always produce the exact same student version.
5. **The student version must fail exactly the tests students are meant to fix.** No more, no less.
6. **Leak scan.** Solutions must not appear in comments, README, migrations, seed data, or git history.
7. **Builder stops after 15 tries** and files a ticket marked either *code problem* (stays in phase 2) or *spec problem* (goes back to step 3).
8. **Any later edit re-enters the pipeline** and re-passes the gates downstream of it. Never hand-edit the student version.
    - A **code** fix re-enters at step 7 and re-passes Gates 2 and 3.
    - A **spec** fix — which is what instructor feedback almost always is — re-enters at step 3 and re-passes Gate 1 as well, because the spec is frozen at Gate 1 and `pipeline revise` is the only way to reopen it.

    Built as stated: `pipeline feedback <slug>` records the note and prints that feedback re-enters at step 3. An earlier draft of this rule said step 7 for both, which contradicted step 15 in §5.

## 7. Repo layout

One directory per project, so several can be in flight at once, and the scripts
live outside them:

```
pipeline/             all check scripts + the orchestrator CLI
projects/<slug>/
  ideas/              idea-01.md … idea-05.md
  idea.md             the one picked at Gate 0
  spec.md             prose, for the person at Gate 1
  spec.json           the machine contract every script reads
  ambiguity.md        the ambiguity list, bound to the spec hash it read
  verify/             the test suite - read-only to the builder
  app/                full working code, with markers
  skeleton/           generated only, never hand-edited
  pack/               README.md, session-N.md, troubleshooting.md
  .pipeline/          state, gates, the frozen spec, and each rejected round
  *.json              one report per checker - lint, gate1, results, mutation,
                      skeleton-check, leak-scan, guide-lint, deploy
```

Named differently from the first draft of this section, which said `course/` with
`spec/`, `tests/`, `e2e/`, `solution/`, `student/`, `guide/`, `gates/` and
`tools/`. What changed and why:

| Draft | Built | Why |
| --- | --- | --- |
| `course/` | `projects/<slug>/` | more than one project exists at a time |
| `spec/S01.yaml` | `spec.md` + `spec.json` | the person at the gate and the scripts need different things from the same spec; splitting them stopped the scripts parsing prose |
| `tests/` + `e2e/` | `verify/` | one suite, one test per requirement. Two trees meant two coverage stories and no single answer to "is this requirement graded" |
| `solution/` | `app/` | it is the working project, and the word "solution" leaked into filenames the leak scan then had to allow |
| `student/` | `skeleton/` | same meaning |
| `guide/` | `pack/` | it is more than the guide - README, per-session plans, troubleshooting |
| `gates/` | `.pipeline/` | gates, retries, locks, the frozen spec hash and the rejected rounds are one state machine, and splitting them let them disagree |
| `tools/` | `pipeline/` | it is an installable module with a single CLI entry point, not a folder of loose scripts |

IDs: session `S03`, requirement `S03-AC01`, student task `S03-T01`. **Supported as
written** — the linter accepts `S03-AC01` or `c-3-1` for a requirement, and
`S03-T01` or `cut-<kebab>` for a student task. Shipped projects happen to use the
`c-3-1` / `cut-<kebab>` forms.

Marker in the solution code — **supported as written**, and the cutter accepts
`CUT` in place of `STUDENT` and an id-only closing marker:

```
# >>> STUDENT S03-T01 START
#     goal: <one line>
   ...answer code...
# <<< STUDENT S03-T01 END
```

The `goal:` line sits inside the block and is removed with it. What the student
reads is the task's `hint` from `spec.json` — the wording a person approved at
Gate 1, not a comment that can drift from it. One rule the cutter enforces:
never put a function's only `return` inside a marker pair, or the skeleton stops
compiling and there is no red test to fix.

## 8. What we build first

One session. Not the whole pipeline. Humans pass work between steps by hand.

**Order: scripts first, AI second.** The scripts are what make the AI trustworthy.

| Week | Build |
| --- | --- |
| 1 | All check scripts: spec linter, red-first check, marker check, cutter, cut validator, leak scan |
| 2 | Idea generator, spec writer, test writer, builder — run by hand |
| 3 | Verifier + coverage check + mutation check |
| 4 | Guide writer, deploy check, then the timed dry run |

## 9. Done when

1. The cutter run twice gives an identical file, byte for byte.
2. The red-first check catches a fake test (`assert True`).
3. The mutation check catches a fake browser test (one that only checks the page loads).
4. The leak scan catches an answer left in git history.
5. The dry run finishes one session inside its time limit, using only the student version and the guide.

Four of these five feed the pipeline something deliberately broken and require it to notice.
A pipeline that has never caught anything has not been proven to work.

### Status — all five met

Run `python3 -m pipeline.selftest` to re-check 1 to 4. It asserts its own count
against `README.md`, so the count moves when checks are added.

| # | Where it is proven | Notes |
| --- | --- | --- |
| 1 | selftest, "cutting twice gives the same skeleton" | the cutter uses no AI, so this is determinism rather than a caught defect |
| 2 | selftest feeds `assert True` and a test with no assertion at all | also checks `pytest.raises` is not a false positive |
| 3 | selftest drives `mutation.classify_run` with the shape a page-loads-only test produces: the mutant runs, the harness is provably live, nothing goes red | the honestly-graded run is checked to still pass, or the catch would prove nothing. End to end, the same artifact is also caught earlier — at step 5 red-first sees `page.goto('/')` with no assertion |
| 4 | selftest plants a real answer line, commits it, deletes the file, commits the deletion — then requires the scan to name the task and the commit and fail on history alone | the tree is clean at that point, which is the case the file scan cannot see |
| 5 | pipeline-test-04 session 1: 40 minutes against a 40-minute cap, taught by someone who did not build it, using only the skeleton and the pack | recorded in `.pipeline/state.json` under `dry_run` |

Two of these were unproven until late: 3 and 4 had never caught anything. `scan_git_history`
ran in production but every test called it with history checking switched off, and mutation
reported `ungraded_tasks: []` on every real run. Both now fail loudly if the detection
regresses, which is the only condition under which citing them means anything.

## 10. Not in scope for v1

- No orchestration engine, no queues, no dashboard
- One session only
- No frontend browser tests yet (API level only)
- No nightly checks yet (nothing is live)

### What was actually built against this scope

Three of the four were overtaken. Recorded because the scope line is what a
reader will check the build against:

| Scope line | Where it landed |
| --- | --- |
| No orchestration engine | **Held.** The orchestrator is plain code with a single CLI. Phases are run one at a time and each stops at its gate; no agent manages another agent. |
| One session only | **Exceeded.** Every shipped project is 2 or 3 sessions. The dry run in §9.5 still covers one session, which is all this scope asks for. |
| No frontend browser tests | **Exceeded.** `verify/` is Playwright plus httpx, one test per requirement, so screens are graded as well as endpoints. |
| No nightly checks | **Partly.** `pipeline watch` replays every shipped suite and is written, but it runs on demand — there is no schedule, because nothing is live yet. |

Still not built, and deliberately:

- **No publish step.** The deploy check proves a fresh copy installs, builds and
  answers HTTP on a temporary local port, then stops the server. Nothing is
  pushed to a host, so there is no URL to hand anyone.
- **No checker proves a named drop candidate is real.** A session over its cap
  discloses the overrun and names what to trim, but nothing verifies the trim is
  a block a student would otherwise type. Seen twice; a rule needs the cut list
  crossed with the guide's plan.