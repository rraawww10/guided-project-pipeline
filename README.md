# Guided project production pipeline

Implements [Flow.md](Flow.md): five agents, six scripts, three gates.

An agent is used only where judgement is needed. Everything else is plain code.
The orchestrator is plain code, so no agent manages another agent.

---

## Run one project

```bash
python3 -m pipeline new todo-tracker        # step 1 - creates projects/todo-tracker/idea.md
$EDITOR projects/todo-tracker/idea.md       # write the one-page idea

# PHASE 1 - the spec.  Spec Writer <-> linter, then Spec Breaker, one pass.
/workflow gp-phase1-spec  {"slug":"todo-tracker"}
#   read projects/todo-tracker/spec.md and ambiguity.md
python3 -m pipeline gate todo-tracker 1 approve -m "sessions fit, no blocking ambiguity"

# PHASE 2 - the code.  Builder <-> test runner, Verifier writes the suite once.
/workflow gp-phase2-code  {"slug":"todo-tracker"}
#   read projects/todo-tracker/results.json - every criterion, not a summary
python3 -m pipeline gate todo-tracker 2 approve -m "44/44 criteria green"

# PHASE 3 - the package.  Cutter, Pack Writer, deploy check.
/workflow gp-phase3-pack  {"slug":"todo-tracker"}
#   read projects/todo-tracker/pack/ and deploy.json
python3 -m pipeline gate todo-tracker 3 approve -m "session 4 is teachable as written"
python3 -m pipeline ship todo-tracker
```

At any point, `python3 -m pipeline next <slug>` says what the pipeline wants
next, and `python3 -m pipeline status <slug>` shows gates, retries and tickets.

### Why three workflows and not one

A workflow cannot block on a person. Each phase ends at its gate and stops. The
gate decision is recorded by the orchestrator, and the next phase refuses to
start without it - so the gates are enforced, not just documented.

---

## The twelve steps, and what implements each

| # | Step | Who | Implementation |
|---|---|---|---|
| 1 | One-page idea | Person | `pipeline new` scaffolds `idea.md` |
| 2 | Spec Writer | Agent | `.claude/agents/spec-writer.md` + `skills/spec-writer` |
| — | spec linter | Script | `pipeline/spec_linter.py` |
| 3 | Spec Breaker | Agent | `.claude/agents/spec-breaker.md` + `skills/spec-breaker` |
| 4 | **Gate 1** | Person | `pipeline gate <slug> 1 approve\|reject` |
| 5 | Builder | Agent | `.claude/agents/builder.md` + `skills/builder` |
| — | test runner | Script | `pipeline/test_runner.py` |
| 6 | Verifier | Agent | `.claude/agents/verifier.md` + `skills/verifier` |
| 7 | **Gate 2** | Person | `pipeline gate <slug> 2 approve\|reject` |
| 8 | Cutter | Script | `pipeline/cutter.py` |
| 9 | Pack Writer | Agent | `.claude/agents/pack-writer.md` + `skills/pack-writer` |
| 10 | Deploy check | Script | `pipeline/deploy_check.py` |
| 11 | **Gate 3** | Person | `pipeline gate <slug> 3 approve\|reject` |
| 12 | Handover + watchdog | Script | `pipeline ship`, `pipeline/watchdog.py` |

Agents are thin. The prompt lives in the skill, so the same prompt can be
lifted into an agent framework later without rewriting it.

---

## The rules, and how each one is actually enforced

| Rule | Enforced by |
|---|---|
| 1. Every agent has a checker | Spec Writer → linter, Builder → test runner, Cutter → skeleton check. Spec Breaker and Pack Writer get one pass and a person reads the output |
| 2. Spec Breaker ≠ Spec Writer | Separate agent definitions. The Breaker reads the spec before the idea, so it does not fill the gaps in its head |
| 3. Builder cannot edit test files | **A lock file and a `PreToolUse` hook.** `pipeline lock <slug> app` restricts writes to `app/`; `pipeline/guard.py` blocks anything else, including shell redirects |
| 4. The skeleton is generated | `pipeline/cutter.py` only. Nothing writes `skeleton/` by hand, and it is deleted and rebuilt every run |
| 5. The orchestrator is plain code | `pipeline/cli.py`. The workflow scripts are control flow only - they hold no judgement |
| 6. Retries stop at 15 | `pipeline/state.py`. On the fifteenth the run stops and writes a ticket with the last error |

Rule 3 is the one most often left as prose. Here it is real:

```
$ python3 -m pipeline lock todo-tracker app
$ # builder tries to edit a test
blocked by the pipeline write guard: this step may only write to todo-tracker/app/,
and verify/test_api.py is outside it.
```

---

## The two artifacts everything hangs on

**`spec.json`** is the machine contract. The linter, builder, verifier and cutter
all read it. `spec.md` is the same spec in prose, for the person at Gate 1. The
linter checks they agree. Full shape in `pipeline/templates/CONTRACT.md`.

**Cut markers** join the final code to the student skeleton:

```ts
// >>> CUT cut-api-todos-list
  const todos = await store.all()
  return Response.json(todos)
// <<< CUT cut-api-todos-list
```

becomes

```ts
  // TODO(cut-api-todos-list): Return every todo from the store as JSON
```

The hint comes from `spec.json`, so the instruction the student reads is the one
that was approved at Gate 1.

### What makes the skeleton check work

Every cut is referenced by at least one acceptance criterion, and the linter
rejects a spec where one is not. So the cutter can prove the skeleton is right:

- a criterion whose cuts were removed **must fail** on the skeleton — if it
  passes, the cut left a working implementation behind
- a criterion with no cuts **must pass** — if it fails, the cut took away code
  the student was supposed to be given

This is what stops the skeleton drifting from the final code.

---

## Nightly watchdog

```bash
python3 -m pipeline watch
# cron: 0 2 * * * python3 -m pipeline watch
```

Replays the committed test suite on every shipped project. Because the Verifier
wrote a script instead of driving the browser itself, a project costs money to
verify once and every run after that is free.

---

## Decisions made

Flow.md left two open. One is settled, one is not.

**Where the spec comes from** — house template, with an optional source
document. `idea.md` has a `Source material` field. If it names a file, every
concept the spec teaches must appear in it. If it says `none`, the Spec Writer
works from the one page and the house format alone. Both paths lint identically,
so a project can start without source material and gain it later.

**Whose API key students use on AI tracks** — still open. The Verifier skill
already requires record-and-replay fixtures, so pipeline testing is free either
way. The live-session key is the part still to decide.

---

## Self-test

```bash
python3 -m pipeline.selftest
```

45 checks on the deterministic core - linter rules and their false positives,
cutter comment styles and every malformed-marker case, the skeleton check, the
write guard, and the gate and retry logic. No agents, no network, about a
second. Run it before trusting a change to any script.

---

## Build order

Flow.md's order was Verifier, Cutter, Spec Breaker, Pack Writer, learning loop.
All five exist here. The order still matters for **where to spend review time**:
the Verifier and the Cutter are the two that pay for themselves immediately, and
both work on projects already shipped, so point them at a finished project and
check their output before trusting the pipeline end to end.

`learning/lessons.md` is the learning loop. Every agent reads it. Add a line the
moment a gate rejects something or a nightly run goes red.
