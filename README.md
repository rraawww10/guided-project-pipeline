# Guided project production pipeline

Implements [requirements_doc.md](requirements_doc.md): seven agents, twelve
scripts, four gates. The original [Flow.md](Flow.md) shape is still supported and
still runs.

An agent is used only where judgement is needed. Everything else is plain code.
The orchestrator is plain code, so no agent manages another agent.

**Humans decide. AI drafts. Scripts check.**

Two rules that never change:

- **The human gives the stack. The AI does not choose it.**
- **The AI gives the ideas. The human approves them. The AI does not pick.**

---

## Two flows, and why both exist

`requirements_doc.md` adds four things the original twelve steps did not have: a
stack and five ideas in front with a gate of their own, the tests written
*before* the code by a different agent, a mutation check that proves the suite
can go red, and a timed dry run by someone who did not build it.

Three projects shipped under the original flow. Rewriting their state would have
invalidated them, so the flow is versioned instead:

| | flow 1 | flow 2 (default) |
|---|---|---|
| Steps | 12 | 16 (0-15) |
| Gates | 3 | 4, with Gate 0 on the idea |
| Tests written | step 6, after the code | **step 5, before the code** |
| Phases | spec, code, pack | idea, spec, code, pack |
| Projects | recipe-box, tip-split, habit-tracker | new ones |

`pipeline new <slug>` creates flow 2. `pipeline new <slug> --flow 1` creates the
old shape. Every script reads the flow off `state.json` and behaves accordingly;
a state file written before the split reads as flow 1. The new checkers step
aside on a flow-1 project rather than failing it retroactively - pass `--force`
to run one anyway.

---

## Run one project (flow 2)

```bash
python3 -m pipeline new todo-tracker                      # step 0 scaffold

# ---- the human gives the stack. The AI does not choose it.
python3 -m pipeline stack todo-tracker \
    --stack 'next,react,typescript' --sessions 3 --minutes 40

# ---- IDEAS.  Idea Generator <-> idea check.  Stops at Gate 0.
/workflow gp-phase0-ideas {"slug":"todo-tracker"}
#   read projects/todo-tracker/ideas/ - all five
python3 -m pipeline pick todo-tracker 3 -m "it has a write path"   # GATE 0

# ---- PLAN.  Spec Writer <-> linter, Spec Breaker, Test Writer <-> red-first.
/workflow gp-phase1-spec {"slug":"todo-tracker"}
#   read spec.md, ambiguity.md, gate1.json, verify/ and redfirst.json
python3 -m pipeline gate todo-tracker 1 approve -m "plan and tests approved"

# ---- CODE.  Builder <-> test runner, Verifier, then the mutation check.
/workflow gp-phase2-code {"slug":"todo-tracker"}
#   read results.json - every criterion - and mutation.json
python3 -m pipeline gate todo-tracker 2 approve -m "44/44 green, every task graded"

# ---- HANDOVER.  Cutter, Guide Writer, deploy check, leak scan, guide linter.
/workflow gp-phase3-pack {"slug":"todo-tracker"}
#   read pack/, deploy.json, leak-scan.json, guide-lint.json
python3 -m pipeline dryrun todo-tracker --session 2 --minutes 38 \
    --by "someone who did not build it"                    # step 13
python3 -m pipeline gate todo-tracker 3 approve -m "teachable as written"
python3 -m pipeline ship todo-tracker

# ---- LIVE
python3 -m pipeline watch                                  # nightly
python3 -m pipeline feedback todo-tracker -m "session 2 ran over" --session 2
```

`pipeline next <slug>` says what the pipeline wants next in either flow, and
`pipeline status <slug>` shows gates, retries and tickets.

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

## The sixteen steps of flow 2, and what implements each

| # | Step | Who | Implementation |
|---|---|---|---|
| 0 | Stack input | Person | `pipeline stack <slug> --stack .. --sessions .. --minutes ..` |
| 1 | Idea generator (5) | Agent | `.claude/agents/idea-generator.md` + `skills/idea-generator` |
| — | idea check | Script | `pipeline ideas` - five real pages, no placeholders |
| 2 | **Gate 0** | Person | `pipeline pick <slug> <n>` - the human picks |
| 3 | Spec writer | Agent | `.claude/agents/spec-writer.md` |
| — | spec linter | Script | `pipeline/spec_linter.py` |
| 4 | Ambiguity check | Agent | `.claude/agents/spec-breaker.md` |
| — | report binding + gate rule | Script | `pipeline breaker <slug> end`, `pipeline/gate1.py` |
| 5 | **Test writer** | Agent | `.claude/agents/test-writer.md` + `skills/test-writer` |
| — | **red-first check** | Script | `pipeline/redfirst.py` |
| 6 | **Gate 1** — plan **and** tests | Person | `pipeline gate <slug> 1 approve` |
| 7 | Builder | Agent | `.claude/agents/builder.md` |
| — | test runner | Script | `pipeline/test_runner.py` |
| 8 | Verifier | Agent | `.claude/agents/verifier.md` |
| — | **mutation check** | Script | `pipeline/mutation.py` |
| 9 | **Gate 2** | Person | `pipeline gate <slug> 2 approve` |
| 10 | Cutter | Script | `pipeline/cutter.py` |
| — | **leak scan** | Script | `pipeline/leak_scan.py` |
| 11 | Guide writer | Agent | `.claude/agents/pack-writer.md` |
| — | **guide linter** | Script | `pipeline/guide_linter.py` |
| 12 | Deploy check | Script | `pipeline/deploy_check.py` |
| 13 | **Dry run** (timed) | Person | `pipeline dryrun <slug> --session N --minutes M --by <who>` |
| 14 | **Gate 3** | Person | `pipeline gate <slug> 3 approve` |
| 15 | Live + feedback | Script | `pipeline ship`, `pipeline watch`, `pipeline feedback` |

Bold rows are what `requirements_doc.md` added.

## The twelve steps of flow 1, and what implements each

| # | Step | Who | Implementation |
|---|---|---|---|
| 1 | One-page idea | Person | `pipeline new` scaffolds `idea.md` |
| 2 | Spec Writer | Agent | `.claude/agents/spec-writer.md` + `skills/spec-writer` |
| — | spec linter | Script | `pipeline/spec_linter.py` |
| 3 | Spec Breaker | Agent | `.claude/agents/spec-breaker.md` + `skills/spec-breaker` |
| — | report binding | Script | `pipeline breaker <slug> end` |
| — | gate 1 rule | Script | `pipeline/gate1.py` - the stopping rule |
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
| 6. Retries stop at 15 | `pipeline/state.py`. On the fifteenth the run stops and writes a ticket with the last error. A *green* step that keeps re-running is a loop too, so `step_runs` caps that at 30 and raises the same ticket |
| 7. The approved spec cannot move | `pipeline gate <slug> 1 approve` hashes spec.json + spec.md, archives them to `.pipeline/approved/` and writes `.pipeline/SPEC_FROZEN`. The write guard then refuses edits to the spec with no lock set, and every later phase refuses to run on a drift |
| 8. A report must name the spec it read | A clean `pipeline lint` opens a Spec Breaker pass against that exact hash; `pipeline breaker <slug> end` binds `ambiguity.md` to it and refuses if the spec moved mid-pass. `pipeline next` and Gate 1 both reject a stale report |
| 9. Gate 1 terminates | `pipeline gate1-check` - reject when a blocking finding is owned by `nothing`, approve when every finding sits in a column a downstream checker owns. Not "blocking == 0", which never terminates |

### The eight rules of `requirements_doc.md`, and how each is enforced

| Rule | Enforced by |
|---|---|
| 1. Tests before the code, by a different AI; the tests folder is read-only to the builder | The Test Writer runs at step 5 under `pipeline lock <slug> verify`, the Builder at step 7 under `lock app`, and `pipeline/guard.py` blocks either from the other's tree |
| 2. Red-first | `pipeline/redfirst.py`. The static half runs at step 5 and rejects a test with no assertion or only trivially true ones; the dynamic all-red proof is the skeleton check at step 10. Gate 1 refuses without it |
| 3. The verifier is checked by a script | `pipeline/mutation.py` removes one student task at a time and requires it to turn one of its own requirements red. Gate 2 refuses without it |
| 4. The cutter uses no AI | `pipeline/cutter.py` only, deleted and regenerated every run |
| 5. The student version fails exactly the right tests | `cutter.verify` - a task's criteria must fail, a no-task criterion must pass |
| 6. Leak scan | `pipeline/leak_scan.py` - no line unique to a task's answer may appear anywhere in the student tree or its git history. Gate 3 refuses without it |
| 7. Builder stops after 15 tries, ticket marked code or spec problem | `state.burn_retry(..., kind=)`. The ticket carries `re_enter_at`: 7 for a code problem, 3 for a spec problem. An ungraded task from the mutation check is filed as a spec problem |
| 8. Any later edit re-enters at step 7 | The spec freeze - `.pipeline/SPEC_FROZEN` plus a hash every later phase checks - and `pipeline revise`, which is the only way to reopen an approved spec. The student version is never hand-edited: it is deleted and regenerated |

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

### What the spec linter catches, and what it cannot

Round 1's central finding was that the linter had **never rejected a spec** -
six rounds, all clean, while 17 blocking findings were caught by reading. It
checked shape. It now also checks the three defects that recurred:

| Code | Rule | The round-1 defect it catches |
|---|---|---|
| `E110` | Two cuts graded by exactly the same criteria are rejected | `cut-fraction-scale` / `cut-recipe-scale-quantity` were graded only by c-4-2/3/4, so one could be left empty with every criterion green. The same rule catches the skeleton-check blind spot: `cut-store-find-one` / `cut-api-recipe-get` share a signature, which is exactly why c-3-2 went green with find-one still empty |
| `E111` / `W112` | Teaching minutes per session, weighing setup cost | Both projects shipped a session at 45 minutes against a 40 minute cap, found at step 9 where the only fix invalidates the whole build |
| `E113` | The session carrying the setup must have strictly fewer cuts than the others | tip-split session 1 carried 4 cuts *plus* all the setup while session 2 also carried 4 |
| `W066` | A hint that names nothing concrete - no symbol, path, method or count | `cut-recipe-scale-quantity` not naming `scaleQuantity` made a second cut bypassable |
| `W067` | A hint phrased as "return ..." | It tells the Builder to put the return inside the markers - the TS2355 shape |

`W066` and `W067` are warnings on purpose. A hint is deliberately prose so it
does not hand over the answer, so whether a given hint is too vague is a
judgement call for the person at Gate 1. The estimate and the hint list are in
`lint.json` on every run, pass or fail.

**What the linter cannot do:** it cannot check marker placement. At step 2 no
code exists - the Builder places the markers at step 5. So the authoritative
TS2355 check is `cutter.scan_return_safety`, a static scan that needs no
toolchain and refuses to generate a skeleton from a cut that holds its
function's only return. `typecheck()` still runs tsc, but it *fails open* with
no `node_modules` - which is every fresh clone - so it is the second line, not
the first, and a typecheck that could not run is now recorded as
`fail_open: true` instead of passing silently.

### What makes the skeleton check work

Every cut is referenced by at least one acceptance criterion, and the linter
rejects a spec where one is not. So the cutter can prove the skeleton is right:

- a criterion whose cuts were removed **must fail** on the skeleton — if it
  passes, the cut left a working implementation behind
- a criterion with no cuts **must pass** — if it fails, the cut took away code
  the student was supposed to be given

This is what stops the skeleton drifting from the final code.

It proves exactly two things, and no more: all-cuts-open must fail, no-cuts must
pass. It says nothing about the partial states a student actually moves through,
so `skeleton-check.json` now lists `partial_state_risks` - the cut groups that
share a grading signature and therefore have a proper subset that satisfies
their criteria. Linter rule `E110` rejects that shape at step 2, so on a new
spec the list is empty by construction. Proving every subset would need one full
test run per subset, which is why the report names the risk instead.

---

## Nightly watchdog

```bash
python3 -m pipeline watch
# cron: 0 2 * * * python3 -m pipeline watch
```

Replays the committed test suite on every shipped project. Because the Verifier
wrote a script instead of driving the browser itself, a project costs money to
verify once and every run after that is free.

Each project is isolated: a project whose venv cannot be built or whose app will
not boot is recorded as broken and the run continues, instead of the exception
escaping the loop and leaving no report for anything. The report says what it
did *not* check (`shipped_total`, `skipped`, `unknown_slugs`) - the one run on
record before this said `"checked": 1` with two projects on disk and nothing
flagged it. A shipped project whose spec no longer matches what Gate 1 approved
is reported as broken too, since no test can see that.

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

318 checks on the deterministic core - linter rules and their false positives,
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
