# The Guided Project Pipeline — Complete Explanation

> A factory that turns **a tech stack you name** into a **ready-to-teach course project**:
> working code, a student starter version, and an instructor's guide.

This document explains the whole system from scratch. No prior knowledge assumed.

---

## Table of contents

1. [The one-line idea](#1-the-one-line-idea)
2. [Why it exists](#2-why-it-exists)
3. [The three kinds of worker](#3-the-three-kinds-of-worker)
4. [What comes out at the end](#4-what-comes-out-at-the-end)
5. [The 16 steps, walked through](#5-the-16-steps-walked-through)
6. [The seven agents in detail](#6-the-seven-agents-in-detail)
7. [The checkers (scripts) in detail](#7-the-checkers-scripts-in-detail)
8. [Guardrails that apply everywhere](#8-guardrails-that-apply-everywhere)
9. [The four human gates](#9-the-four-human-gates)
10. [Cut markers and the student skeleton](#10-cut-markers-and-the-student-skeleton)
11. [Files on disk](#11-files-on-disk)
12. [Commands](#12-commands)
13. [The UI](#13-the-ui)
14. [When things go wrong](#14-when-things-go-wrong)
15. [Two flows (versions)](#15-two-flows-versions)
16. [Glossary](#16-glossary)

---

## 1. The one-line idea

**Humans decide. AI drafts. Scripts check.**

Every part of the system is one of those three things, and each is used only where it belongs:

- An **AI agent** is used *only* where judgement is needed — inventing ideas, writing a spec, writing code.
- A **script** checks everything an agent produced. Scripts are plain code: same input, same answer, every time.
- A **human** makes the decisions that no script can make, at four fixed points called **gates**.

The rule that holds it together:

> **Rule 1 — Every agent has a checker.**
> If nothing can check an agent's output, it gets one try and a person reads it.

---

## 2. Why it exists

Building one guided project by hand takes **days**. Testing it by hand takes about **40 minutes**, and has to be repeated after every fix.

The target is **one project per day**, with human time dropping to about **two hours of reviewing rather than building**.

The saving does not come from the AI being fast. It comes from the checks being automatic — you read a pass/fail list instead of clicking through the app yourself.

---

## 3. The three kinds of worker

| | Who | What they do | Can they be wrong? |
|---|---|---|---|
| **Human** | You | Give the stack. Approve at 4 gates. Teach one timed session. | You are the final authority. |
| **Agent** | 7 AI agents | Propose ideas, write the spec, tests, code, guide. | Often. That is expected. |
| **Script** | ~14 checkers | Prove each agent's output is real. | Deterministic. If one crashes, that is a *pipeline fault*, not a verdict. |

### The "did not run" rule

This idea appears everywhere and is worth understanding early.

A checker has **three** outcomes, not two:

1. **Pass**
2. **Fail**
3. **Did not run** (it crashed, or the app never built)

Mapping the third onto either of the first two is how the pipeline has quietly gone wrong before. So a crash is reported as *"this is a pipeline fault, not the project's — a checker that did not run supports no conclusion."*

---

## 4. What comes out at the end

For a project called `my-project`, you end up with:

| Folder | What it is | Who reads it |
|---|---|---|
| `app/` | The complete working project | The instructor |
| `skeleton/` | Same project with the lessons cut out, leaving TODOs | **The student** |
| `verify/` | The automated test suite | The pipeline |
| `pack/` | Session-by-session teaching guide | The instructor |
| `spec.md` / `spec.json` | What was agreed, in prose and as a machine contract | Everyone |

---

## 5. The 16 steps, walked through

The workflow has 16 steps (numbered 0–15) grouped into four phases. Each phase **stops at its gate** and does not roll into the next.

```
PHASE: IDEA
  0  You give the stack                      HUMAN
  1  Idea Generator -> 5 ideas               AGENT   -> checked by: ideas
  2  GATE 0 - you pick one                   HUMAN

PHASE: SPEC  (the plan and the tests, before any code)
  3  Spec Writer -> spec.md + spec.json      AGENT   -> checked by: lint
  4  Spec Breaker -> ambiguity.md            AGENT   -> checked by: breaker + gate1-check
  5  Test Writer -> verify/                  AGENT   -> checked by: redfirst
  6  GATE 1 - you approve plan AND tests     HUMAN

PHASE: CODE
  7  Builder -> app/                         AGENT   -> checked by: test
  8  Verifier -> strengthens verify/         AGENT   -> checked by: test + mutation
  9  GATE 2 - you read the pass/fail list    HUMAN

PHASE: PACK (handover)
 10  Cutter -> skeleton/                     SCRIPT  -> checked by: leak scan
 11  Pack Writer -> pack/                    AGENT   -> checked by: guide-lint
 12  Deploy check -> deploy.json             SCRIPT
 13  Dry run (a person teaches, timed)       HUMAN
 14  GATE 3 - you approve the pack           HUMAN
 15  Ship + nightly replay + feedback        SCRIPT
```

### Why the tests come *before* the code

This is the single most important design choice.

If the code were written first and the tests second, the tests would be written to match whatever the code happens to do — including its bugs. Writing the tests first, from the spec, and by a **different agent**, means the tests describe what was *agreed*, not what was *built*.

The `redfirst` checker then proves those tests **fail before the code exists**. A test that passes at that point is testing nothing.

---

## 6. The seven agents in detail

Each agent gets: a job, files it may read, files it may write, a **checker** (its eval), and **guardrails**.

---

### 6.1 Idea Generator — step 1

**Job:** Propose **five** one-page project ideas that fit the stack you gave.

**Never** picks one. Choosing is yours.

| | |
|---|---|
| **Reads** | `stack.json` (your stack, sessions, minutes, limits), `learning/lessons.md` |
| **Writes** | `ideas/idea-01.md` … `idea-05.md` |
| **Tools** | Read, Write, Glob, Grep — **no Bash**, so it cannot run anything |

**Eval — the `ideas` checker**
Confirms five real, distinct ideas exist. Not five headings with nothing under them.

**Guardrails**
- Cannot pick. Gate 0 is a separate human action (`pipeline pick`).
- Cannot choose the stack — *"the human gives the stack, the AI does not choose it"* is one of two rules that never change.
- No Bash tool, so it cannot install, run or modify anything.

---

### 6.2 Spec Writer — step 3

**Job:** Turn the one picked idea into a full specification:
- `spec.md` — prose, for the human at Gate 1
- `spec.json` — the machine contract every later script reads

| | |
|---|---|
| **Reads** | `idea.md`, `stack.json`, `lessons.md`, and on a retry `lint.json` |
| **Writes** | `spec.md`, `spec.json` |
| **Never** | writes code |

The spec splits the project into sessions. Each session lists:
- **criteria** — testable statements (`c-1-1`, `c-2-3`, …)
- **cuts** — the blocks students will write (`cut-ui-render-rows`, …), each with a `hint` and a `writes_into` symbol
- **teaches** — the concepts introduced

**Eval — the `lint` checker (`spec_linter.py`)**
Dozens of shape rules, plus a **session-fit model** that estimates teaching minutes:

```
BASE_MINUTES        10.0   intro, recap, wrap-up
MINUTES_PER_CUT      6.0   live-coding one cut with explanation
MINUTES_PER_BUILD    3.0   scaffolding an endpoint or screen
MINUTES_PER_CONCEPT  1.5   one entry in `teaches`
SETUP_MINUTES        6.0   project setup, on the session that carries it

SESSION_MINUTES_CAP   40   over this is a WARNING (a judgement call)
SESSION_MINUTES_HARD  50   over this is an ERROR (no live session absorbs it)

MIN_CRITERIA, MAX_CRITERIA = 2, 6   per session
MAX_CUTS = 5                        per session
```

> **Note:** these caps are **constants**. They are *not* read from the `--minutes`
> you type. Setting `--minutes 90` does not make bigger sessions allowed.
> See [§15](#15-two-flows-versions) for how to actually get bigger projects.

**Guardrails**
- A retry re-reads `lint.json` and repairs, rather than starting over.
- After Gate 1 the spec is **frozen** (`.pipeline/SPEC_FROZEN`) and `guard.py` refuses to write it. Reopening requires `pipeline revise`.

---

### 6.3 Spec Breaker — step 4

**Job:** Read the spec **adversarially** and list every sentence that could mean two different things.

It **only lists**. It never fixes. That separation is deliberate — a writer marking its own work grades leniently.

| | |
|---|---|
| **Reads** | `spec.md`, `spec.json`, `idea.md` |
| **Writes** | `ambiguity.md` |
| **Runs** | Exactly once per spec version |

**Rule 2 — the Spec Breaker is a different agent from the Spec Writer.**

**Eval — `breaker begin` / `breaker end` + `gate1-check`**

This is **rule 7** in action: *a report must name the spec it read.*

```
pipeline breaker <slug> begin   records the current spec hash, deletes any old report
        (the Spec Breaker runs)
pipeline breaker <slug> end     refuses if the spec changed during the pass
```

If the spec moves while the Breaker is reading, the report reviewed neither version cleanly and is rejected. A stale report is refused at Gate 1.

**Guardrails**
- The report is bound to a spec hash. Copying an old report back in does not fool it.
- If the spec has moved on, the fix is a **fresh Breaker pass** — not the Spec Writer, because rewriting the spec is what made the report stale in the first place.

---

### 6.4 Test Writer — step 5

**Job:** Write the test suite **from the spec, before any code exists**, as a *different agent from the Builder*.

| | |
|---|---|
| **Reads** | `spec.json`, `spec.md`, `ambiguity.md`, `lessons.md` |
| **Writes** | `verify/` — test files plus `coverage.json` |
| **Locked to** | `verify/` only |

`coverage.json` maps **one criterion to one test**:

```json
{ "c-1-1": { "test": "verify/test_api.py::test_c_1_1_returns_10_items" } }
```

**Eval — the `redfirst` checker**, which has three independent halves:

| Half | Question | How |
|---|---|---|
| **Static** | Can each test even fail? | Parses every test. Flags "no assertion" and "every assertion is trivially true". |
| **Runnable** | Can the suite execute at all? | `pytest --setup-plan` resolves every fixture **without needing the app**. |
| **Dynamic** | Do the tests fail before the code exists? | Runs the suite. Any test that *passes* now is testing nothing. |

> **Why the "runnable" half exists:** the dynamic half cannot catch a broken
> suite. At step 5 there is no `app/`, so nothing runs and every criterion
> reports `missing` — which the dynamic half reads as "maximally red". A suite
> with a missing `conftest.py` looks *identical* to a healthy one. The runnable
> half asks a question that does not need the app.

**Guardrails**
- Different agent from the Builder (**rule 1** of the build rules).
- Locked to `verify/`; `guard.py` blocks writes elsewhere.
- Owns any failure where the suite itself is broken — a fixture error is a *test* problem, and the Builder is forbidden from touching tests.

---

### 6.5 Builder — step 7

**Job:** Write the working project into `app/`, **one session milestone at a time**, placing the **cut markers** the student skeleton is later generated from.

| | |
|---|---|
| **Reads** | `stack.json`, `spec.json`, `spec.md`, `ambiguity.md`, `lessons.md`, and on retry `results.json` |
| **Writes** | `app/` |
| **Cannot** | touch `verify/` — **rule 3** |

**Eval — the `test` checker (`test_runner.py`)**

Installs, builds, starts the app, runs the suite, maps each result to a criterion:

```json
{ "ok": true, "counts": { "pass": 13, "fail": 0, "skip": 0, "missing": 0 } }
```

It also runs **`stack_check`** and **`code_check`** in the same pass, and `ok` requires all three.

**Guardrails — this agent has the most, because it has the most power**

1. **Cannot edit tests.** `guard.py` runs as a PreToolUse hook; the orchestrator locks `app/`. *"A build that passes because the test was changed is worth nothing."*
2. **`stack_check` (S001–S007)** — the stack is yours, not the agent's:

   | Code | Refuses |
   |---|---|
   | S001 | no `package.json` |
   | S002 | a stack package not declared as a dependency |
   | S003 | an inert build script (`echo`, `node -e`, …) |
   | S004 | a build that never invokes the stack |
   | S005 | a start script that does not *run* the stack |
   | S006 | a build or start that swallows its own failure with `\|\|` |
   | S007 | a pinned version the npm registry marks deprecated |

3. **Retry cap** — 15 attempts, then a ticket (**rule 6**).
4. **Cut marker rules**, enforced downstream by `cutter` and `mutation`:
   - never put a function's **only `return`** inside a marker pair
   - never cut a **binding that surviving code still references**
   - what remains must still compile
5. **Version rule** — check, do not remember: `npm view <pkg>@<version> deprecated`.

> **Why so many guardrails?** Because a builder under pressure optimises for
> "make the check pass", not "build the thing". In one real run it replaced a
> Next/React/TypeScript app with a hand-written Node server that answered the
> same HTTP assertions — all tests passed, and every file holding a cut marker
> was dead code. `stack_check` exists because of that.

---

### 6.6 Verifier — step 8

**Job:** Strengthen the test suite so it covers **every** criterion through the real UI and API — one test per criterion, plus `coverage.json`.

| | |
|---|---|
| **Reads** | `spec.json`, `verify/`, `results.json`, `mutation.json` |
| **Writes** | `verify/` |
| **Special** | Leaves no artifact of its own — it edits a suite that already exists |

**Eval — `test` + `mutation`** (see [§7.6](#76-mutation--the-strongest-check))

**Guardrails**
- Because it leaves no unique file, "has the Verifier run?" is answered from the **run ledger** (`.pipeline/ui-runs.jsonl`), not from a file's existence.
- It may only *tighten*. `verify_hash` is recorded at Gate 1, and Gate 2 reports plainly whether `verify/` moved, so a human reads the diff — *a gate cannot tell a tightened assertion from a weakened one.*

---

### 6.7 Pack Writer — step 11

**Job:** Write the instructor's session guide — what to build, in what order, what to explain, and where students get stuck.

| | |
|---|---|
| **Reads** | `spec.json`, `app/`, `skeleton/`, `verify/` |
| **Writes** | `pack/README.md`, `pack/session-N.md`, `pack/troubleshooting.md` |
| **Runs** | **One pass.** A person reads it at Gate 3. |

**Eval — the `guide-lint` checker**

Checks one file per session, that every cut id and criterion id is accounted for, that the vocabulary matches the spec, and estimates whether each session fits its time budget.

A common warning:

```
WRN G033  session 1 has no '**Time:**' line, so its planned total was
          guessed as 40 - the largest duration mentioned in the file
```

**Guardrails**
- One pass only — this is **rule 1's** other branch: when a checker cannot fully judge quality, a person reads it.
- The guide linter compares the guide against the *actual* code corpus, so a guide describing code that does not exist is caught.

---

## 7. The checkers (scripts) in detail

### 7.1 `ideas` — step 1
Confirms five real ideas exist.

### 7.2 `lint` (`spec_linter.py`) — step 3
Spec shape, id vocabulary, cut/criteria counts, session-minute estimate. Reports are bound to a spec hash so a stale clean report cannot masquerade as a fresh one.

### 7.3 `breaker begin/end` — step 4
Binds `ambiguity.md` to the exact spec hash it reviewed (rule 7).

### 7.4 `gate1-check` (`gate1.py`) — step 4
**The stopping rule.** Explained fully in [§9](#9-the-four-human-gates).

### 7.5 `redfirst` — step 5
Static + runnable + dynamic, as above.

### 7.6 `mutation` — the strongest check

**Step 8. This is the check that makes the whole thing trustworthy.**

For **every** cut marker, mutation:

1. copies `app/` to a scratch directory,
2. deletes that one marker's code,
3. builds and runs the whole suite,
4. asks: **did at least one criterion that claims to test this task go red?**

```json
{ "ok": true, "checked": 13, "of_total": 13,
  "ungraded_tasks": [], "inconclusive_tasks": [] }
```

Three outcomes per task:

| Outcome | Meaning |
|---|---|
| **graded** | Removing it turns a requirement red. The task is really taught and really marked. |
| **ungraded** | Every requirement still passes without it. **A student could leave it empty and still "pass".** |
| **inconclusive** | The mutant did not build, so nothing ran. **Proves nothing** — unproven, not fine. |

> Mutation takes roughly **one full build per cut marker** — about 30–40 minutes
> for a 13-cut project. It is the slowest step and the one worth waiting for.

**What it catches in practice:** dead code behind a marker; fixtures already in the order a criterion asserts (so a sort task grades nothing); a placeholder identical to the cut body (ungradeable by construction); markers that break the build when cut.

### 7.7 `cut` (`cutter.py`) — step 10

Generates `skeleton/` from `app/` by replacing each marker pair with a TODO built from the spec's `hint`. **No AI** — the same code always produces byte-identical output (**rule 4**).

It also:
- **typechecks** the skeleton and reports `missing_return` — the classic "cut a function's only return" mistake
- proves the skeleton **fails exactly the right tests** (`skeleton-check.json`)
- records an **`app_hash`**, so if `app/` changes afterwards, Gate 3 and `ship` refuse until you re-cut

### 7.8 `leak` (`leak_scan.py`) — step 10

Rule: *no line unique to a task's answer may appear anywhere in the student tree, **or in its git history***.

Catches answers left in comments, README, seed data, migrations — anywhere.

### 7.9 `guide-lint` — step 11
See [§6.7](#67-pack-writer--step-11).

### 7.10 `deploy` (`deploy_check.py`) — step 12

Proves it runs **on another machine**:

```
fresh copy  ->  install  ->  install advisories  ->  build  ->  preview
```

- **fresh copy** honours `.gitignore` — runtime state is not carried over
- **install advisories** fails the step if npm prints a security warning. `--allow-advisories` ships one deliberately, recorded in `deploy.json` *and* in `.pipeline/ALLOW_ADVISORIES` so step 7 honours the same decision
- This is where "works on my machine" dies: your local `node_modules` may be stale, the clean copy is not

### 7.11 `test` (`test_runner.py`) — steps 7 & 8

Beyond running the suite, it defends against several false greens:

- `BOOT_FAILED_RC = 99` — **a build failure is not a test failure.** It belongs to the Builder, not the Test Writer
- deletes the previous JUnit report first, so a build that dies cannot inherit the last run's "13 pass"
- treats an **empty** `node_modules` as not installed
- matches **parametrised** tests (`test_x[a-1]`) to their criterion, so a parametrised test is not permanently `missing`

### 7.12 `spec-status`
Reports whether the spec on disk still matches what Gate 1 froze.

### 7.13 `watch` (`watchdog.py`) — step 15
Replays shipped suites on demand. A shipped project that quietly breaks gets noticed.

### 7.14 `selftest.py`
**414 deterministic checks** on the pipeline itself. It asserts its own count against `README.md`, so adding checks moves the README number with them.

```bash
python3 -m pipeline.selftest
```

Run this before trusting any change to any script.

---

## 8. Guardrails that apply everywhere

### 8.1 The write guard (`guard.py`)

A **PreToolUse hook**. Before an agent writes anything, this runs.

```
pipeline lock   <slug> app|verify|pack|skeleton
pipeline unlock <slug>
```

- The orchestrator locks **one subtree per step**. Writes outside it are blocked.
- While any lock is held, writes to `pipeline/`, `.claude/` and `learning/` are refused — **rule 5: no agent edits the pipeline.**
- It refuses to write `spec.json` once `SPEC_FROZEN` exists.

> **Honest limit:** the guard sees Write/Edit calls and shell write commands.
> It does **not** see writes made inside an interpreter (`python -c`, a node
> script). Read it as *raising the cost of an accident*, not as a guarantee.

### 8.2 Loop protection — three separate caps

| Cap | Value | Catches |
|---|---|---|
| `RETRY_LIMIT` | **15** per phase | An agent that keeps failing (**rule 6**) |
| `STEP_RUN_LIMIT` | **30** runs of one step | A *green* step re-running forever |
| `GUARD_REPEATS` | **3** | An action repeating with nothing moving and no retry burned |

The third exists because some checkers reject without burning a retry — a cycle with nothing at the end of it.

### 8.3 Hash bindings — "a report must name what it read"

| Artifact | Bound to | Enforced by |
|---|---|---|
| `ambiguity.md` | the spec hash it reviewed | `breaker end`, Gate 1 |
| `lint.json` | the spec on disk | `fresh_report` |
| `spec.json` | frozen at Gate 1 | `SPEC_FROZEN` + `guard.py` |
| `verify/` | `verify_hash` recorded at Gate 1 | reported at Gate 2 |
| `skeleton/` | `app_hash` it was cut from | Gate 3 and `ship` refuse if stale |

### 8.4 Separation of duties

- Spec Writer ≠ Spec Breaker
- Test Writer ≠ Builder
- The Builder cannot edit tests
- The Cutter uses no AI
- **No agent manages another agent.** The orchestrator is plain code.

### 8.5 Network failures are not verdicts

An agent call that never reached the API says nothing about the work. Transport errors and HTTP 429 are retried with backoff; an HTTP 5xx is **not** retried, because the server may have done the work and billed for it.

### 8.6 Token limits

Each agent call caps its output (default 16000 tokens). If a reply is cut off at that ceiling it **raises**, because a truncated tool call parses as nothing and would otherwise read as *"the agent chose to do nothing."*

---

## 9. The four human gates

A gate is a stop. The pipeline will not step past one on its own.

Every gate computes **blockers** — machine-checkable conditions that must hold. **Zero blockers means you *may* approve, not that you *should*.**

### Gate 0 — pick an idea (step 2)

You choose one of five. No script can judge which project is worth teaching.

```bash
pipeline pick my-project 2 -m "why this one"
```

### Gate 1 — approve the plan AND the tests (step 6)

The big one. You are approving a spec, an ambiguity report and a full test suite **before a line of code exists**.

**The stopping rule** (`gate1.py`) is the cleverest part of the system:

> Reject when any **blocking** finding is owned by **"nothing"**.
> Approve when every remaining finding sits in a column a downstream checker owns.

It is deliberately **not** "blocking count == 0", because that never terminates — an adversarial reader can always find one more thing. Instead it asks: *where would this defect surface?* If some later checker owns it, it is handled. If nothing owns it, it ships as written and you are the last line.

**`verify_later`** — an owner that could pass *by not running* owns a finding only **conditionally**. Those are listed with the exact confirmation required, for example:

```
step 8 must show checked == of_total, and the task this finding names must be
among the mutants run - mutation is opt-in, so ok:true over a subset proves
nothing about a task that was skipped
```

### Gate 2 — read the pass/fail list (step 9)

~2 minutes instead of ~40 of clicking. Requires `results.json` **and** `mutation.json` green.

Gate 2 also tells you whether `verify/` moved since Gate 1, and shows the diff command — because a gate cannot tell a tightened assertion from a weakened one.

### Gate 3 — approve the pack (step 14)

Requires: leak scan, guide linter, skeleton check, `pack/` present, and **a dry run on record** where a person who did **not** build it taught one session from the guide, with a timer.

That dry run is the only end-to-end evidence the pack actually works. It cannot be automated — automating it would delete the evidence.

---

## 10. Cut markers and the student skeleton

A **cut marker** wraps the code a student will write:

```ts
let out: number = 0
// >>> CUT cut-lib-compute-total
out = items.reduce((sum, i) => sum + i.price, 0)
// <<< CUT cut-lib-compute-total
return out
```

The Cutter replaces the inside with a TODO built from the spec's `hint`:

```ts
let out: number = 0
// TODO(cut-lib-compute-total): Sum every item's price into `out`
return out
```

### The three rules that matter

1. **Never put a function's only `return` inside a pair.** Cut it and the function returns nothing — it will not compile, the mutant cannot build, and mutation can only say INCONCLUSIVE.
2. **Never cut a binding that surviving code still references.** The block may parse perfectly and the cut still break the build, because the reference that survives no longer resolves.
3. **The placeholder outside must differ from the body inside.** If they are identical, removing the block changes nothing and *no test can ever grade it* — not a weak test, an impossible one.

The safe pattern for all three: **declare above the marker, assign inside it, use below it.**

---

## 11. Files on disk

```
projects/<slug>/
  stack.json            what you gave: stack, sessions, minutes, limits
  ideas/idea-01..05.md  the five proposals
  idea.md               the one you picked
  spec.md  spec.json    the plan, in prose and as a contract
  ambiguity.md          the Spec Breaker's findings
  verify/               the test suite + coverage.json
  app/                  the working project
  skeleton/             the student version (generated, never hand-edited)
  pack/                 the instructor guide

  lint.json             spec linter report
  gate1.json            stopping rule verdict
  redfirst.json         red-first report
  results.json          test run + stack_check + code_check
  mutation.json         per-task grading proof
  skeleton-check.json   skeleton correctness + app_hash
  leak-scan.json        answer leak report
  guide-lint.json       guide report
  deploy.json           clean-machine install/build/preview

  .pipeline/
    state.json          phase, gates, retries, step history
    LOCK                which subtree the current agent may write
    SPEC_FROZEN         the spec hash Gate 1 approved
    ALLOW_ADVISORIES    a deliberate decision to ship a known advisory
    round-N/            an archived, rejected round
```

---

## 12. Commands

```bash
# setup
python3 -m pipeline new <slug>                       # create (flow 2)
python3 -m pipeline stack <slug> --stack "next,react,typescript" \
                                 --sessions 3 --minutes 40

# navigation
python3 -m pipeline next <slug>                      # what is next?
python3 -m pipeline status <slug>                    # gates, retries, tickets

# human decisions
python3 -m pipeline pick <slug> 2 -m "reason"        # GATE 0
python3 -m pipeline gate <slug> 1 approve -m "..."   # GATES 1-3
python3 -m pipeline dryrun <slug> --session 1 --minutes 40 --by <name>
python3 -m pipeline ship <slug>

# checkers (all free, all deterministic)
python3 -m pipeline ideas|lint|redfirst|test|mutation|cut|leak|guide-lint|deploy <slug>

# recovery
python3 -m pipeline revise <slug>                    # archive round, reset Gate 1
python3 -m pipeline feedback <slug> -m "..."         # re-enters at step 3

# trust
python3 -m pipeline.selftest                         # 414 checks
```

---

## 13. The UI

```bash
python3 -m pipeline.ui        # http://127.0.0.1:8765
```

**The UI is a window onto the same CLI, not a second pipeline.** It shells out to the same commands, runs each agent's own prompt against OpenRouter, and stops at every gate.

| Button | Does |
|---|---|
| **Start** | Runs step after step until it must stop |
| **Step** | Runs exactly one action |
| **Stop** | Pauses after the current action finishes |
| **Preview** | Builds and serves `app/` or `skeleton/` so you can look at it |

It writes only `.pipeline/ui-*.json*` and `ui-logs/`, which nothing else reads.

**Where it stops on its own:** a gate, a person step, completion, a rejected gate, a retry cap, a churn cap, or no API key.

> **Important:** Python modules load once at startup. If a `.py` file changes,
> **restart the UI**. CSS and JS are re-read on every request, so those land on
> a browser refresh alone.

---

## 14. When things go wrong

### Read the shape of the failure first

| Symptom | Usually means |
|---|---|
| `0 pass, 0 fail, N missing` | The suite never ran — a build failure or a broken suite, **not** failing code |
| `INCONCLUSIVE` in mutation | The mutant did not build. Unproven, not fine |
| A step repeats identically | Its checker may be **crashing**, never producing a verdict |
| Green tests but `ok: false` | `stack_check` or `code_check` failed — the tests passing is not the whole bar |
| Deploy fails, local works | Exactly what deploy is for — your `node_modules` is stale, the clean copy is not |

### Who owns which failure

| Red report | Owner | Why |
|---|---|---|
| `lint.json` | Spec Writer | The spec is wrong |
| `gate1.json` — stale | **Spec Breaker** | Rewriting the spec is what made it stale |
| `gate1.json` — findings | Spec Writer | Real blocking findings |
| `redfirst.json` | Test Writer | The tests are the problem |
| `results.json` — failing | Builder | The code is wrong |
| `results.json` — suite broken | **Test Writer** | The Builder cannot fix tests (rule 3) |
| `mutation.json` | Verifier and/or Builder | A weak test, or code that grades nothing |
| `leak-scan.json` | Builder | Markers must move — never hand-edit the skeleton |

### If you edit `app/` after step 10

Re-run **`cut`** and **`leak`**. Gate 3 and `ship` now refuse a stale skeleton, but the fastest path is to re-cut immediately.

---

## 15. Two flows (versions)

| | flow 1 | flow 2 *(default)* |
|---|---|---|
| Steps | 12 | 16 (0–15) |
| Gates | 3 | 4, with Gate 0 on the idea |
| Tests written | step 6, **after** the code | step 5, **before** the code |
| Phases | spec, code, pack | idea, spec, code, pack |

Flow 1 is kept working because three projects shipped under it. Every script reads the flow from `state.json`.

### Making projects bigger

Projects come out modest because of the **per-session caps** in [§6.2](#62-spec-writer--step-3) — and those caps are constants, not your `--minutes`.

Three levers that actually work:

1. **More sessions** — the only size lever not capped. Costs mutation time: roughly one build per cut marker.
2. **A richer stack** — probably the biggest lever. `next,react,typescript` with no database yields seeded JSON and in-memory state. Adding `prisma,sqlite` yields migrations, persistence and real queries.
3. **The `limits` field** — free text handed to the Idea Generator. *"must persist across restarts; migrations and seed must run from a clean checkout"* changes what gets proposed.

---

## 16. Glossary

| Term | Meaning |
|---|---|
| **Agent** | An AI given one job, one prompt, and one checker |
| **Checker** | A deterministic script that proves an agent's output is real |
| **Gate** | A stop where a human decides. Four of them |
| **Cut marker** | `>>> CUT id` / `<<< CUT id` around code a student will write |
| **Skeleton** | The student version, generated from cut markers, never hand-edited |
| **Criterion** | One testable statement, e.g. `c-2-3`, mapped to exactly one test |
| **Mutation** | Deleting one task's code to prove a test notices |
| **Ungraded task** | A task a student could leave empty and still pass |
| **Inconclusive** | The mutant did not build, so nothing was proven either way |
| **Red-first** | Tests must fail before the code exists |
| **Stopping rule** | Gate 1's terminating condition: no blocking finding owned by "nothing" |
| **verify_later** | A finding owned only conditionally, with the confirmation required |
| **Ticket** | Raised at 15 retries. Stops the phase for a person to look |
| **Flow** | Which version of the workflow a project uses (1 or 2) |

---

## The shortest possible summary

> You give a stack. Five ideas come back and you pick one. A spec is written,
> then attacked by a different agent, then the tests are written **before any
> code** — and you approve all three together. Only then is the code built, and
> it is not finished until a script has deleted each student task in turn and
> proved a test notices. Then the student version is generated mechanically,
> the guide is written, a clean machine installs it from scratch, and a person
> who did not build it teaches one session with a timer.
>
> **Four times, you decide. The rest is drafted by AI and proven by scripts.**
