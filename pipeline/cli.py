"""Orchestrator - SCRIPT, the thing that runs the twelve steps in order.

Rule 5: the orchestrator is plain code. No agent manages another agent.
This CLI is the single entry point for every script step and every gate.

  python -m pipeline new <slug> [--flow 1|2]
  python -m pipeline stack <slug> --stack .. --sessions N --minutes M   # step 0
  python -m pipeline ideas <slug>             # step 1 checker - 5 real ideas
  python -m pipeline pick <slug> <n>          # GATE 0 - the human picks
  python -m pipeline redfirst <slug>          # step 5 checker - rule 2
  python -m pipeline mutation <slug>          # step 8 checker - rule 3
  python -m pipeline leak <slug>              # step 10 checker - rule 6
  python -m pipeline guide-lint <slug>        # step 11 checker
  python -m pipeline handover-checks <slug>   # both of the above, one call
  python -m pipeline dryrun <slug> --session N --minutes M --by <who>   # step 13
  python -m pipeline feedback <slug> -m "..."  # step 15, re-enters at step 3
  python -m pipeline status <slug>
  python -m pipeline lint <slug>              # step 2 checker
  python -m pipeline test <slug>              # step 6 checker
  python -m pipeline cut <slug>               # step 8
  python -m pipeline deploy <slug>            # step 10
  python -m pipeline lock <slug> app|verify|pack   # rule 3, before an agent step
  python -m pipeline unlock <slug>
  python -m pipeline revise <slug>            # archive a rejected round, reset gate 1
  python -m pipeline breaker <slug> begin|end # bind ambiguity.md to the spec it read
  python -m pipeline gate1-check <slug>       # step 4 checker - the stopping rule
  python -m pipeline spec-status <slug>       # is the spec still the approved one
  python -m pipeline gate <slug> 1|2|3 approve|reject [-m note] [--override]
  python -m pipeline ship <slug>              # step 12
  python -m pipeline watch                    # replay shipped suites (on demand)
  python -m pipeline next <slug>              # what the pipeline wants next
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import (cutter, deploy_check, gate1, guide_linter, leak_scan, mutation,
               redfirst, spec_linter, test_runner, watchdog)
from .state import (GATES, RETRY_LIMIT, STEP_RUN_LIMIT, State, frozen_hash,
                    project_dir, spec_drift, spec_hash)

HERE = Path(__file__).parent

# requirements_doc.md step 1: "AI proposes 5 project ideas that fit that stack."
IDEAS_WANTED = 5

# step -> (phase, who, what the orchestrator does about it)
#
# Two tables. Flow 1 is the twelve-step pipeline the three shipped projects were
# built with and must keep working. Flow 2 is requirements_doc.md: a stack and
# five ideas in front, Gate 0, the tests written before the code, and a timed dry
# run before Gate 3.
STEPS_BY_FLOW = {
    1: [
        (1, "spec", "PERSON", "write idea.md"),
        (2, "spec", "AGENT", "spec-writer  -> spec.md, spec.json   (checked by: lint)"),
        (3, "spec", "AGENT", "spec-breaker -> ambiguity.md         (bind: pipeline breaker <slug> end)"),
        (4, "spec", "GATE", "gate 1 - approve the spec"),
        (5, "code", "AGENT", "builder      -> app/                 (checked by: test)"),
        (6, "code", "AGENT", "verifier     -> verify/              (checked by: test)"),
        (7, "code", "GATE", "gate 2 - read the pass or fail list"),
        (8, "pack", "SCRIPT", "cut          -> skeleton/"),
        (9, "pack", "AGENT", "pack-writer  -> pack/                (one pass, you read it)"),
        (10, "pack", "SCRIPT", "deploy       -> deploy.json"),
        (11, "pack", "GATE", "gate 3 - approve the pack"),
        (12, "pack", "SCRIPT", "ship         -> handover + watchdog on demand"),
    ],
    2: [
        (0, "idea", "PERSON", "stack input   -> pipeline stack <slug> --stack .. --sessions .. --minutes .."),
        (1, "idea", "AGENT", "idea-generator -> ideas/idea-01..05.md  (checked by: pipeline ideas)"),
        (2, "idea", "GATE", "gate 0 - pick one idea: pipeline pick <slug> <n>"),
        (3, "spec", "AGENT", "spec-writer   -> spec.md, spec.json     (checked by: lint)"),
        (4, "spec", "AGENT", "spec-breaker  -> ambiguity.md           (bind: pipeline breaker <slug> end)"),
        (5, "spec", "AGENT", "test-writer   -> verify/                (checked by: redfirst)"),
        (6, "spec", "GATE", "gate 1 - approve the plan AND the tests"),
        (7, "code", "AGENT", "builder       -> app/                   (checked by: test)"),
        (8, "code", "AGENT", "verifier      -> browser tests          (checked by: test + mutation)"),
        (9, "code", "GATE", "gate 2 - read the pass or fail list"),
        (10, "pack", "SCRIPT", "cut           -> skeleton/             (checked by: leak scan)"),
        (11, "pack", "AGENT", "guide-writer  -> pack/                 (checked by: guide-lint)"),
        (12, "pack", "SCRIPT", "deploy        -> deploy.json"),
        (13, "pack", "PERSON", "dry run       -> pipeline dryrun <slug> --session N --minutes M --by <who>"),
        (14, "pack", "GATE", "gate 3 - approve the pack"),
        (15, "pack", "SCRIPT", "ship          -> handover + watchdog on demand + feedback intake"),
    ],
}
STEPS = STEPS_BY_FLOW[1]      # kept for callers that predate the flow split


def _guard(st: State, phase: str) -> None:
    ok, why = st.may_enter(phase)
    if not ok:
        sys.exit(f"blocked: {why}")
    if st.exhausted(phase):
        t = st.data["ticket"]
        sys.exit(f"blocked: phase '{phase}' hit the {RETRY_LIMIT} retry limit.\n"
                 f"ticket raised {t['raised']}\nlast error: {t['last_error']}")
    # Rule 6, the other half: a step that keeps re-running while its checker
    # stays green is a loop. burn_retry only fires on failure, so recipe-box
    # logged 10 clean lint runs and 6 clean test runs at 0/15 retries.
    churn = st.churning()
    if churn:
        if not st.data.get("ticket"):
            st.data["ticket"] = {"raised": st.data.get("created"), "phase": phase,
                                 "retries": st.data["retries"][phase],
                                 "last_error": churn}
            st.save()
        sys.exit(f"blocked: {churn}")
    # The code and the tests were built against the approved spec. If the spec
    # has changed since, that relationship no longer holds.
    drift = spec_drift(st.dir)
    if drift and phase in ("code", "pack"):
        sys.exit(f"blocked: {drift}")


def _checker(st: State, step: str, phase: str, fn):
    """Run a checker script. A crash is a failed checker - never a verdict.

    A checker has three outcomes, not two: pass, fail, and DID NOT RUN. The
    pipeline modelled the first two, so everything downstream silently mapped
    the third onto one of them, and which one was arbitrary. An unguarded crash
    in `test` read as "keep trying" and looped the phase-2 workflow for two
    hours; an unguarded crash in `mutation` read as "the spec is wrong" and
    printed an instruction to reject a Gate-1-approved spec that was correct.
    """
    try:
        return fn()
    except SystemExit:
        raise
    except Exception as e:
        n = st.burn_retry(phase, f"{step} crashed: {type(e).__name__}: {e}")
        st.log_step(step, False)
        print(f"{step} crashed: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"\n{phase} retry {n}/{RETRY_LIMIT} - this is a pipeline fault, not "
              f"the project's. A checker that did not run supports no conclusion.",
              file=sys.stderr)
        raise SystemExit(1)


def cmd_new(a) -> int:
    d = project_dir(a.slug)
    if d.exists():
        sys.exit(f"{d} already exists")
    (d / ".pipeline").mkdir(parents=True)
    shutil.copy(HERE / "templates" / "CONTRACT.md", d / ".pipeline" / "CONTRACT.md")
    st = State(a.slug)
    st.data["flow"] = a.flow
    st.data["phase"] = st.phases[0]
    st.data["retries"] = {ph: 0 for ph in st.phases}
    st.data["gates"] = {g: None for g in st.gates.values()}
    st.save()

    if a.flow == 2:
        (d / "ideas").mkdir()
        print(f"created {d}  (flow 2 - requirements_doc.md, 16 steps, 4 gates)")
        print("next: step 0 is yours - state the stack, the sessions and the minutes:\n"
              f"  python -m pipeline stack {a.slug} --stack 'next,react,typescript' "
              f"--sessions 3 --minutes 40")
        print("The human gives the stack. The AI does not choose it.")
    else:
        shutil.copy(HERE / "templates" / "idea_template.md", d / "idea.md")
        print(f"created {d}  (flow 1 - the original 12 steps, 3 gates)")
        print(f"next: write {d / 'idea.md'}, then run `python -m pipeline next {a.slug}`")
    return 0


def cmd_lint(a) -> int:
    st = State(a.slug)
    _guard(st, "spec")
    rc = _checker(st, "lint", "spec", lambda: spec_linter.main(["", str(st.dir)]))
    if rc != 0:
        report = json.loads((st.dir / "lint.json").read_text())
        first = report["errors"][0] if report["errors"] else {}
        n = st.burn_retry("spec", f"{first.get('code')} {first.get('where')}: {first.get('message')}")
        print(f"\nspec retry {n}/{RETRY_LIMIT} - send lint.json back to the spec-writer")
    else:
        _open_breaker_pass(st)
    st.log_step("lint", rc == 0)
    return rc


def _open_breaker_pass(st: State) -> None:
    """A clean lint opens the spec-breaker pass against that exact spec.

    Folded in here so the workflow needs no separate agent for it, and so the
    binding cannot be forgotten. Only fires when the spec has actually changed -
    recipe-box ran the linter ten times in fifteen minutes, and re-linting an
    unchanged spec must not throw away a report that is still valid for it.
    """
    h = spec_hash(st.dir)
    if h is None:
        return
    began = st.dir / ".pipeline" / "breaker-begin.json"
    if began.exists() and json.loads(began.read_text()).get("spec_hash") == h:
        return
    began.parent.mkdir(parents=True, exist_ok=True)
    began.write_text(json.dumps({"spec_hash": h}, indent=2) + "\n")
    # fail closed: a report written against the previous spec is not this one's
    for stale in ((st.dir / "ambiguity.md"), (st.dir / ".pipeline" / "ambiguity-meta.json")):
        stale.unlink(missing_ok=True)
    print(f"spec-breaker pass opened against spec {h[:12]} "
          f"(any earlier ambiguity.md cleared - it reviewed a different spec)")


def cmd_test(a) -> int:
    st = State(a.slug)
    _guard(st, "code")
    # The runner boots the app and writes results.json, so it cannot run under a
    # subtree lock. Clearing it here removes the separate `unlock` agent the
    # workflow used to spawn before every test run - one command-only agent per
    # retry iteration, and the one the security classifier kept flagging.
    (st.dir / ".pipeline" / "LOCK").unlink(missing_ok=True)
    # A checker that CRASHES is a failed checker. It used to escape as an
    # exception, so burn_retry and log_step below never ran: `pipeline test`
    # died in ensure_venv on Windows with retries still reading code=0/15, and
    # the phase-2 workflow looped on the Verifier for two hours with nothing to
    # stop it. Rule 6 has to cover the crash, not just the red run.
    try:
        rc = test_runner.main([str(st.dir), "--target", a.target])
    except Exception as e:
        n = st.burn_retry("code", f"the test runner crashed: {type(e).__name__}: {e}")
        st.log_step(f"test:{a.target}", False)
        print(f"the test runner crashed: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"\ncode retry {n}/{RETRY_LIMIT} - this is a pipeline fault, not the "
              f"builder's; fix the runner rather than the app", file=sys.stderr)
        return 1
    if a.target == "app" and rc != 0:
        res = json.loads((st.dir / "results.json").read_text())
        failed = [c for c, v in res.get("criteria", {}).items() if v["status"] != "pass"]
        bad_checks = [n for n, r in ((res.get("code_checks") or {}).get("checks")
                                     or {}).items() if not r["ok"]]
        why = f"failing criteria: {', '.join(failed[:8])}" if failed else ""
        if bad_checks:
            why = (why + "; " if why else "") + f"failing code checks: {', '.join(bad_checks)}"
        n = st.burn_retry("code", why or "the suite did not run")
        print(f"\ncode retry {n}/{RETRY_LIMIT} - send results.json back to the builder")
    st.log_step(f"test:{a.target}", rc == 0)
    return rc


def cmd_cut(a) -> int:
    st = State(a.slug)
    _guard(st, "pack")
    (st.dir / ".pipeline" / "LOCK").unlink(missing_ok=True)
    rc = _checker(st, "cut", "pack", lambda: cutter.main(["", "cut", str(st.dir)]))
    if rc != 0:
        st.log_step("cut", False)
        return rc
    # the skeleton must fail exactly the tests whose cuts were removed
    test_runner.main([str(st.dir), "--target", "skeleton"])   # failures here are expected
    rc = _checker(st, "skeleton-check", "pack", lambda: cutter.main(["", "verify", str(st.dir)]))
    if rc != 0:
        print("\nthe skeleton does not fail the right tests - fix the cut markers in app/, "
              "never the skeleton (rule 4)")
    else:
        # The typecheck and the skeleton build both write artifacts into the
        # skeleton after it was copied, so excluding them from the copy is not
        # enough. Sweep once the checks that needed them have passed.
        swept = cutter.sweep_generated(st.dir)
        if swept:
            print(f"swept {len(swept)} generated file(s) out of the skeleton: "
                  f"{', '.join(swept)}")
    st.log_step("cut", rc == 0)
    return rc


def cmd_deploy(a) -> int:
    st = State(a.slug)
    _guard(st, "pack")
    rc = _checker(st, "deploy", "pack",
                  lambda: deploy_check.main([str(st.dir), "--target", a.target,
                                            "--hold", str(a.hold)]))
    st.log_step("deploy", rc == 0)
    return rc


def cmd_gate(a) -> int:
    st = State(a.slug)
    gate = f"gate{a.n}"
    approved = a.decision == "approve"
    extra: dict = {}
    if approved:
        blockers = _gate_blockers(st, a.n, override=bool(getattr(a, "override", False)))
        if blockers:
            sys.exit("cannot approve - these have not passed yet:\n  " + "\n  ".join(blockers))
        if a.n == 1:
            if getattr(a, "override", False) and not a.note:
                sys.exit("--override needs -m \"<why nothing downstream catching it is "
                         "acceptable>\" - it is recorded in state.json")
            extra = _approve_spec(st, a)
    st.record_gate(gate, approved, a.note, extra)
    if approved:
        # each gate guards one phase; approving it opens the next one. Works for
        # both flows because it reads the flow's own phase order.
        by_gate = {g: ph for ph, g in st.gates.items()}
        ph = by_gate.get(gate)
        if ph:
            order = list(st.phases)
            i = order.index(ph)
            if i + 1 < len(order):
                st.data["phase"] = order[i + 1]
                st.save()
    print(f"{gate}: {'approved' if approved else 'rejected'}"
          + (f" - {a.note}" if a.note else ""))
    if not approved:
        back = ({0: "step 1, idea-generator", 3: "step 11, guide-writer",
                 1: "step 3, spec-writer", 2: "step 7, builder"}[a.n]
                if st.flow == 2 else
                {1: "step 2, spec-writer", 2: "step 5, builder",
                 3: "step 9, pack-writer"}[a.n])
        print(f"sent back to {back}")
    return 0


def _approve_spec(st: State, a) -> dict:
    """Freeze and archive the spec Gate 1 just approved.

    Round 1 built app/ and verify/ against a spec that existed only in the
    working tree while HEAD held a rejected round, and a finished Spec Writer
    woke up an hour later and copied a rejected round back over the live files.
    `revise` archives on rejection only, so there was no archive-on-approval and
    nothing to compare against. Both are fixed here:

      .pipeline/approved/     the bytes that were approved
      .pipeline/SPEC_FROZEN   their hash - every later phase checks it, and the
                              write guard refuses edits to the spec while it exists
    """
    d = st.dir
    h = spec_hash(d)
    if h is None:
        sys.exit("cannot approve - spec.json or spec.md is missing")
    archive = d / ".pipeline" / "approved"
    if archive.exists():
        shutil.rmtree(archive)
    archive.mkdir(parents=True)
    kept = []
    for name in ("spec.md", "spec.json", "lint.json", "ambiguity.md", "gate1.json"):
        src = d / name
        if src.exists():
            shutil.copy2(src, archive / name)
            kept.append(name)
    (archive / "APPROVED").write_text(f"{h}\n{a.note}\n")
    (d / ".pipeline" / "SPEC_FROZEN").write_text(h + "\n")
    print(f"spec frozen at {h[:12]} and archived to {archive} ({', '.join(kept)})")
    print("the write guard now refuses edits to spec.md and spec.json; "
          "`pipeline revise` is the only way to reopen them")
    return {"spec_hash": h, "override": bool(getattr(a, "override", False))}


def _gate_blockers(st: State, n: int, override: bool = False) -> list[str]:
    d, out = st.dir, []

    # A gate cannot be approved while the gate before it is not. `may_enter`
    # guards entering a phase, but nothing guarded approving a gate out of
    # order - so gate 1 was approvable with gate 0 still open.
    order = [st.gates[ph] for ph in st.phases]
    want = f"gate{n}"
    if want in order:
        i = order.index(want)
        if i > 0 and not st.gate_passed(order[i - 1]):
            out.append(f"{order[i - 1]} has not been approved - gates are approved in "
                       f"order, so {want} cannot be")

    # requirements_doc.md widens three of the four gates. Guarded on flow 2 so a
    # legacy project's gates keep exactly the requirements they were approved
    # under.
    if st.flow == 2:
        if n == 0:
            if not (d / "stack.json").exists():
                out.append("no stack.json - step 0 is the human giving the stack "
                           "(pipeline stack <slug> --stack .. --sessions .. --minutes ..)")
            if not _ok_json(d / "ideas.json"):
                out.append(f"the idea set has not passed (run: pipeline ideas {st.slug})")
        if n == 1:
            # rule 1: the tests exist before the code. rule 2: they were red.
            if not (d / "verify").exists():
                out.append("verify/ is missing - in this flow the tests are written at "
                           "step 5, BEFORE the builder runs")
            if not _ok_json(d / "redfirst.json"):
                out.append(f"the red-first check has not passed (run: pipeline "
                           f"redfirst {st.slug}) - a test that passes before the code "
                           f"is written proves nothing")
        if n == 2:
            # rule 3: a suite that cannot go red is not a check
            if not _ok_json(d / "mutation.json"):
                out.append(f"the mutation check has not passed (run: pipeline "
                           f"mutation {st.slug}) - every student task must turn a "
                           f"requirement red when it alone is removed")
        if n == 3:
            if not _ok_json(d / "leak-scan.json"):
                out.append(f"the leak scan has not passed (run: pipeline leak {st.slug})")
            if not _ok_json(d / "guide-lint.json"):
                out.append(f"the guide linter has not passed (run: pipeline "
                           f"guide-lint {st.slug})")
            dr = st.data.get("dry_run")
            if not dr:
                out.append("no dry run on record - step 13 is a person who did not "
                           "build it teaching one session from the guide, with a timer "
                           "(pipeline dryrun <slug> --session N --minutes M --by <who>)")
            elif not dr.get("taught_without_the_code"):
                out.append(f"the dry run on {dr['at']} recorded that the session could "
                           f"NOT be taught from the guide alone")

    if n == 1:
        lint = d / "lint.json"
        if not lint.exists() or not json.loads(lint.read_text())["ok"]:
            out.append("spec linter has not passed (run: pipeline lint)")
        if not (d / "ambiguity.md").exists():
            out.append("spec-breaker has not run (ambiguity.md missing)")
        else:
            # The stopping rule, enforced. Not "blocking == 0" - that never
            # terminates - but "nothing is left that no downstream checker owns".
            g1 = gate1.check(d)
            (d / "gate1.json").write_text(json.dumps(g1, indent=2) + "\n")
            if not g1["ok"]:
                if override:
                    print("WARNING: --override used. The gate 1 stopping rule said "
                          "reject:\n  " + "\n  ".join(g1["reasons"]))
                    print("Recorded in state.json. This is a person overruling the rule, "
                          "not the rule passing.")
                else:
                    out.append("gate 1 stopping rule says reject:\n    "
                               + "\n    ".join(g1["reasons"])
                               + f"\n  (detail: pipeline gate1-check {st.slug};"
                               f" to overrule deliberately: --override -m \"<why>\")")
    if n == 2:
        res = d / "results.json"
        if not res.exists() or not json.loads(res.read_text())["ok"]:
            out.append("test runner has not passed (run: pipeline test)")
    if n == 3:
        chk = d / "skeleton-check.json"
        if not chk.exists() or not json.loads(chk.read_text())["ok"]:
            out.append("skeleton does not fail the right tests (run: pipeline cut)")
        if not (d / "pack").exists():
            out.append("pack-writer has not run (pack/ missing)")
        dep = d / "deploy.json"
        if not dep.exists() or not json.loads(dep.read_text())["ok"]:
            out.append("deploy check has not passed (run: pipeline deploy)")
    return out


def cmd_ship(a) -> int:
    st = State(a.slug)
    if not st.gate_passed("gate3"):
        sys.exit("blocked: gate3 has not been approved")
    (st.dir / ".pipeline" / "SHIPPED").write_text(st.data["gates"]["gate3"]["at"] + "\n")
    st.log_step("ship", True)
    # basic_needs_v1.md section 10 keeps nightly checks out of scope until
    # something is actually live, and nothing is. This used to hand over a cron
    # line, which read as an instruction to install one; no schedule was ever
    # installed, so `watchdog-latest.json` has only ever come from a hand run.
    # The watchdog itself stays - `pipeline watch` runs it on demand, and the
    # cron line goes back the day the first project is taught for real.
    print(f"{a.slug} shipped. Its suite is now part of `pipeline watch`, "
          f"which is run on demand - there is no nightly schedule while "
          f"nothing is live.")
    return 0


def cmd_watch(a) -> int:
    return watchdog.main(["--root", ".", "--only", a.only])


def cmd_status(a) -> int:
    st = State(a.slug)
    d = st.data
    print(f"{a.slug}  phase={d['phase']}")
    for g in ("gate1", "gate2", "gate3"):
        v = d["gates"][g]
        print(f"  {g}: {'approved' if v and v['approved'] else 'rejected' if v else 'not reached'}")
    print("  retries: " + ", ".join(f"{k}={v}/{RETRY_LIMIT}" for k, v in d["retries"].items()))
    if d.get("ticket"):
        print(f"  TICKET: {d['ticket']['phase']} - {d['ticket']['last_error']}")
    for s in d["steps"][-8:]:
        print(f"    {'ok  ' if s['ok'] else 'FAIL'} {s['step']}  {s['at']}")
    return 0


def _ok_json(path: Path, key: str = "ok") -> bool:
    try:
        return bool(json.loads(path.read_text()).get(key))
    except (OSError, json.JSONDecodeError):
        return False


def _flow2_checks(st: State) -> list[tuple[int, bool]]:
    """requirements_doc.md, steps 0-15."""
    d = st.dir
    return [
        (0, (d / "stack.json").exists()),
        (1, len(list((d / "ideas").glob("idea-*.md"))) >= 5
            if (d / "ideas").exists() else False),
        (2, st.gate_passed("gate0") and (d / "idea.md").exists()),
        (3, _ok_json(d / "lint.json")),
        (4, (d / "ambiguity.md").exists()
            and (st.gate_passed("gate1")
                 or gate1.check(d).get("reviewed_spec_hash") == spec_hash(d))),
        # rule 1 and 2: the tests exist, and they were red before any code
        (5, (d / "verify").exists() and _ok_json(d / "redfirst.json")),
        (6, st.gate_passed("gate1")),
        (7, (d / "app").exists()),
        # rule 3: green criteria AND a suite proven able to go red
        (8, _ok_json(d / "results.json") and _ok_json(d / "mutation.json")),
        (9, st.gate_passed("gate2")),
        # rule 6: the student version fails the right tests and leaks nothing
        (10, _ok_json(d / "skeleton-check.json") and _ok_json(d / "leak-scan.json")),
        (11, (d / "pack").exists() and _ok_json(d / "guide-lint.json")),
        (12, _ok_json(d / "deploy.json")),
        (13, bool(st.data.get("dry_run"))),
        (14, st.gate_passed("gate3")),
        (15, (d / ".pipeline" / "SHIPPED").exists()),
    ]


def cmd_next(a) -> int:
    """What the pipeline wants next. The Claude workflow calls this to stay in sync."""
    st = State(a.slug)
    d, done = st.dir, []
    steps = STEPS_BY_FLOW[st.flow]
    if st.flow == 2:
        checks = _flow2_checks(st)
        for n, ok in checks:
            if ok:
                done.append(n)
                continue
            step = next(x for x in steps if x[0] == n)
            print(json.dumps({"flow": 2, "step": n, "phase": step[1], "who": step[2],
                              "do": step[3], "retries_left": st.remaining(step[1]),
                              "completed": done}, indent=2))
            return 0
        print(json.dumps({"flow": 2, "step": None, "do": "done - shipped",
                          "completed": done}, indent=2))
        return 0

    checks = [
        (1, (d / "idea.md").exists() and "<Project title>" not in (d / "idea.md").read_text()),
        (2, (d / "lint.json").exists() and json.loads((d / "lint.json").read_text())["ok"]),
        # B-04: a report on disk is not evidence it reviewed the spec on disk.
        # This is the check whose absence made `next` report "Gate 1" for a
        # round-3 spec the Spec Breaker had never read.
        #
        # Only before Gate 1. Once the gate has approved, the spec is frozen and
        # archived, which is the stronger guarantee, and the report's freshness
        # is history - re-checking it would walk a shipped project back to
        # step 3, which is what it did to both round-1 projects.
        (3, (d / "ambiguity.md").exists()
            and (st.gate_passed("gate1")
                 or gate1.check(d).get("reviewed_spec_hash") == spec_hash(d))),
        (4, st.gate_passed("gate1")),
        (5, (d / "app").exists()),
        (6, (d / "results.json").exists() and json.loads((d / "results.json").read_text())["ok"]),
        (7, st.gate_passed("gate2")),
        (8, (d / "skeleton-check.json").exists() and json.loads((d / "skeleton-check.json").read_text())["ok"]),
        (9, (d / "pack").exists()),
        (10, (d / "deploy.json").exists() and json.loads((d / "deploy.json").read_text())["ok"]),
        (11, st.gate_passed("gate3")),
        (12, (d / ".pipeline" / "SHIPPED").exists()),
    ]
    for n, ok in checks:
        if ok:
            done.append(n)
            continue
        step = next(x for x in steps if x[0] == n)
        print(json.dumps({"flow": 1, "step": n, "phase": step[1], "who": step[2],
                          "do": step[3], "retries_left": st.remaining(step[1]),
                          "completed": done}, indent=2))
        return 0
    print(json.dumps({"flow": 1, "step": None, "do": "done - shipped",
                      "completed": done}, indent=2))
    return 0


def cmd_revise(a) -> int:
    """Archive the rejected round before the Spec Writer overwrites it.

    Flow.md sends a rejected spec back to step 2. Without this the previous
    spec and the ambiguity report that rejected it are simply overwritten, and
    the reason for a change is lost by round three.
    """
    st = State(a.slug)
    n = len([d for d in (st.dir / ".pipeline").glob("round-*") if d.is_dir()]) + 1
    dest = st.dir / ".pipeline" / f"round-{n}"
    dest.mkdir(parents=True)
    # Move, never copy. `next` reads progress off the files on disk, so a stale
    # clean lint.json left behind would make the rejected round still look like
    # a spec waiting at gate 1 - `revise` says "back to step 2" and `next` would
    # answer "step 4". The archive under round-N/ is the record; the Spec Writer
    # reads it there.
    names = ["spec.md", "spec.json", "lint.json", "ambiguity.md", "gate1.json"]
    # Flow 2 writes the tests at step 5, BEFORE gate 1, so a rejected round
    # leaves a suite written against the spec being archived. Step 5 completes
    # on "verify/ exists and redfirst.json is ok" with no hash binding, so
    # leaving them behind marks step 5 done for the NEXT round and the tests are
    # never rewritten - Gate 1 would then approve a round-2 spec graded by
    # round-1 tests. Worse, the findings that force a revise are usually about
    # criteria that are not graded, so the very criteria the new spec extends
    # are the ones whose tests would be missing.
    if st.flow == 2:
        names += ["redfirst.json", "verify"]
    moved = []
    for name in names:
        src = st.dir / name
        if src.exists():
            shutil.move(str(src), str(dest / name))
            moved.append(name)
    gate = st.data["gates"].get("gate1") or {}
    (dest / "why.md").write_text(
        f"# Round {n}\n\nGate 1: {'rejected' if gate and not gate.get('approved') else 'not decided'}\n"
        f"Note: {gate.get('note', '')}\n")
    st.data["gates"]["gate1"] = None          # the next round faces a fresh gate
    # Reopen the spec: the freeze belongs to the approval that was just undone,
    # and the report and its binding belong to the spec that was just archived.
    for name in ("SPEC_FROZEN", "ambiguity-meta.json", "breaker-begin.json"):
        (st.dir / ".pipeline" / name).unlink(missing_ok=True)
    st.log_step(f"revise:round-{n}", True, ", ".join(moved))
    print(f"archived round {n} to {dest} ({', '.join(moved)})")
    print(f"gate1 reset - the revised spec must be approved on its own merits")
    return 0


def cmd_stack(a) -> int:
    """Step 0. The human gives the stack. The AI does not choose it."""
    st = State(a.slug)
    if st.flow != 2:
        sys.exit(f"{a.slug} is a flow-1 project - step 0 does not exist in that flow")
    stack = [x.strip() for x in a.stack.split(",") if x.strip()]
    if not stack:
        sys.exit("--stack needs at least one technology, e.g. --stack 'next,react,typescript'")
    payload = {
        "stack": stack, "sessions": a.sessions, "minutes_per_session": a.minutes,
        "track": a.track, "limits": a.limits, "given_by": a.by, "at": st.data["created"],
    }
    (st.dir / "stack.json").write_text(json.dumps(payload, indent=2) + "\n")
    (st.dir / "ideas").mkdir(exist_ok=True)
    st.log_step("stack", True, ", ".join(stack))
    print(json.dumps(payload, indent=2))
    print(f"\nnext: the idea generator writes {IDEAS_WANTED} one-page ideas into "
          f"{st.dir / 'ideas'}")
    return 0


def cmd_ideas(a) -> int:
    """Step 1's checker. Five ideas, each a real page, none a placeholder."""
    st = State(a.slug)
    d = st.dir / "ideas"
    files = sorted(d.glob("idea-*.md")) if d.exists() else []
    problems = []
    if len(files) < IDEAS_WANTED:
        problems.append(f"{len(files)} ideas, need {IDEAS_WANTED}")
    for f in files:
        text = f.read_text()
        if len(text.split()) < 80:
            problems.append(f"{f.name} is {len(text.split())} words - not a page")
        for marker in ("TODO", "TBD", "FIXME", "???", "<insert"):
            if marker in text:
                problems.append(f"{f.name} still contains {marker!r}")
    report = {"ok": not problems, "count": len(files),
              "wanted": IDEAS_WANTED,
              "files": [f.name for f in files], "problems": problems}
    (st.dir / "ideas.json").write_text(json.dumps(report, indent=2) + "\n")
    st.log_step("ideas", report["ok"], f"{len(files)} ideas")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


def cmd_pick(a) -> int:
    """Gate 0. The human picks. The AI does not pick.

    Copies the chosen idea to idea.md, which is what the Spec Writer reads, and
    records which one was chosen so the choice is auditable.
    """
    st = State(a.slug)
    if st.flow != 2:
        sys.exit(f"{a.slug} is a flow-1 project - it has no gate 0")
    src = st.dir / "ideas" / f"idea-{a.n:02d}.md"
    if not src.exists():
        sys.exit(f"{src} does not exist - run the idea generator first, "
                 f"then `pipeline ideas {a.slug}`")
    rc = cmd_ideas(argparse.Namespace(slug=a.slug))
    if rc != 0:
        sys.exit("the idea set has problems - fix those before picking")
    shutil.copy2(src, st.dir / "idea.md")
    st.record_gate("gate0", True, a.note or f"picked idea-{a.n:02d}",
                   {"picked": src.name})
    st.data["phase"] = "spec"
    st.save()
    st.log_step("pick", True, src.name)
    print(f"gate0: approved - picked {src.name}, copied to idea.md")
    print(f"next: the spec writer reads {st.dir / 'idea.md'}")
    return 0


def cmd_redfirst(a) -> int:
    """Step 5's checker. Rule 2: a test that passes early proves nothing."""
    st = State(a.slug)
    argv = [str(st.dir), "--target", a.target]
    if a.static_only:
        argv.append("--static-only")
    if a.no_report:                      # a self-check records nothing
        return redfirst.main(argv + ["--no-report"])
    rc = _checker(st, "redfirst", "spec", lambda: redfirst.main(argv))
    st.log_step("redfirst", rc == 0)
    return rc


def cmd_mutation(a) -> int:
    """Step 8's second checker. Rule 3: the suite must be able to go red."""
    st = State(a.slug)
    if st.flow != 2 and not a.force:
        print(f"{a.slug} is a flow-1 project - the mutation check is not part of that "
              f"flow. Run it anyway with --force (one boot and build per task).")
        return 0
    _guard(st, "code")
    (st.dir / ".pipeline" / "LOCK").unlink(missing_ok=True)
    argv = [str(st.dir)]
    if a.only:
        argv += ["--only", a.only]
    if a.max:
        argv += ["--max", str(a.max)]
    # Same rule as cmd_test: a checker that crashes is a failed checker. This one
    # crashed out of os.symlink on Windows, wrote no mutation.json, burned no
    # retry - and the phase-2 workflow then reported the missing report as the
    # finding "the mutation check found student tasks that grade nothing" with
    # an EMPTY task list, whose printed fix was to reject Gate 1 and revise a
    # spec that had nothing wrong with it. A crash must never read as a verdict.
    try:
        rc = mutation.main(argv)
    except Exception as e:
        n = st.burn_retry("code", f"the mutation check crashed: {type(e).__name__}: {e}")
        st.log_step("mutation", False)
        print(f"the mutation check crashed: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"\ncode retry {n}/{RETRY_LIMIT} - this is a pipeline fault, not the "
              f"spec's; no conclusion can be drawn about ungraded tasks", file=sys.stderr)
        return 1
    if rc != 0:
        rep = json.loads((st.dir / "mutation.json").read_text())
        n = st.burn_retry("code", "ungraded student tasks: "
                          + ", ".join(rep.get("ungraded_tasks", [])[:8]),
                          kind="spec problem")
        print(f"\ncode retry {n}/{RETRY_LIMIT} - an ungraded task is a SPEC problem: "
              f"the requirement list does not notice the task. Back to step 3.")
    st.log_step("mutation", rc == 0)
    return rc


def cmd_leak(a) -> int:
    """Step 10's second checker. Rule 6: solutions must not leak."""
    st = State(a.slug)
    rc = _checker(st, "leak", "pack",
                  lambda: leak_scan.main([str(st.dir)]
                                         + (["--no-history"] if a.no_history else [])))
    st.log_step("leak-scan", rc == 0)
    return rc


def cmd_guide_lint(a) -> int:
    """Step 11's checker."""
    st = State(a.slug)
    rc = _checker(st, "guide-lint", "pack", lambda: guide_linter.main([str(st.dir)]))
    st.log_step("guide-lint", rc == 0)
    return rc


def cmd_handover_checks(a) -> int:
    """Steps 10 and 11's checkers together - rule 6 and the guide linter.

    One command so the phase-3 workflow needs one command runner rather than two.
    On a flow-1 project it steps aside: those projects were approved at Gate 3
    without these checks and re-running them now would only fail them
    retroactively.
    """
    st = State(a.slug)
    if st.flow != 2 and not a.force:
        print(f"{a.slug} is a flow-1 project - the leak scan and guide linter are not "
              f"part of that flow. Run them anyway with --force.")
        return 0
    # guarded like cmd_leak and cmd_guide_lint - this convenience wrapper calls the
    # checkers directly rather than going through them, so it had the R2-18 shape
    # after both of those were fixed.
    rc_leak = _checker(st, "leak", "pack",
                       lambda: leak_scan.main([str(st.dir)]
                                              + (["--no-history"] if a.no_history else [])))
    st.log_step("leak-scan", rc_leak == 0)
    print()
    rc_guide = _checker(st, "guide-lint", "pack", lambda: guide_linter.main([str(st.dir)]))
    st.log_step("guide-lint", rc_guide == 0)
    if rc_leak or rc_guide:
        print("\nhandover checks failed - a leak goes back to the cut markers in app/, "
              "a guide error goes back to the guide writer at step 11", file=sys.stderr)
    return 0 if (rc_leak == 0 and rc_guide == 0) else 1


def cmd_dryrun(a) -> int:
    """Step 13. A person who did not build it teaches one session, with a timer."""
    st = State(a.slug)
    if st.flow != 2:
        sys.exit(f"{a.slug} is a flow-1 project - step 13 does not exist in that flow")
    if not a.by:
        sys.exit("--by needs the name of the person who taught it, and it must not be "
                 "whoever built it")
    st.record_dry_run(a.session, a.minutes, a.by, not a.could_not_teach, a.note)
    st.log_step("dryrun", True, f"session {a.session}, {a.minutes} min, {a.by}")
    print(json.dumps(st.data["dry_run"], indent=2))
    if a.could_not_teach:
        print("\nrecorded as NOT teachable from the guide alone - gate 3 will refuse")
    return 0


def cmd_feedback(a) -> int:
    """Step 15. Instructor feedback goes back to step 3."""
    st = State(a.slug)
    if not a.note:
        sys.exit('-m "<what happened in the session>" is required')
    entry = st.record_feedback(a.note, a.session, a.by)
    st.log_step("feedback", True, a.note[:120])
    print(json.dumps(entry, indent=2))
    print(f"\n{len(st.data['feedback'])} feedback item(s) on file. Feedback re-enters "
          f"at step 3: `pipeline revise {a.slug}` archives the round and sends the "
          f"spec back to the writer.")
    return 0


# Which phase a lock belongs to, so `lock` is a real gate check.
#
# Flow-dependent for verify/: in flow 1 the tests are written at step 6, inside
# the code phase. In flow 2 they are written at step 5, BEFORE Gate 1, so the
# lock belongs to the spec phase - otherwise locking verify/ for the test writer
# would demand the very gate the test writer runs before.
LOCK_PHASE_BY_FLOW = {
    1: {"app": "code", "verify": "code", "pack": "pack", "skeleton": "pack"},
    2: {"app": "code", "verify": "spec", "pack": "pack", "skeleton": "pack"},
}
LOCK_PHASE = LOCK_PHASE_BY_FLOW[1]      # kept for callers that predate the split


def cmd_gate1_check(a) -> int:
    """The stopping rule, on demand. Same code the gate itself runs."""
    st = State(a.slug)
    return gate1.main(["", str(st.dir)])


def cmd_breaker(a) -> int:
    """Bind the ambiguity report to the exact spec the Spec Breaker read.

    Nothing tied a report to a spec, so a report copied back from an archived
    round looked current and `pipeline next` reported Gate 1 for a spec the
    Breaker had never seen. `begin` records the hash and clears the old report;
    `end` refuses if the spec moved during the pass.
    """
    st = State(a.slug)
    meta_dir = st.dir / ".pipeline"
    meta_dir.mkdir(parents=True, exist_ok=True)
    began = meta_dir / "breaker-begin.json"
    h = spec_hash(st.dir)
    if h is None:
        sys.exit("spec.json or spec.md is missing - nothing to review")

    if a.mode == "begin":
        began.write_text(json.dumps({"spec_hash": h}, indent=2) + "\n")
        # fail closed: this pass must produce the report, not inherit one
        (st.dir / "ambiguity.md").unlink(missing_ok=True)
        (meta_dir / "ambiguity-meta.json").unlink(missing_ok=True)
        print(f"spec-breaker pass opened against spec {h[:12]}")
        return 0

    if not began.exists():
        sys.exit("no breaker pass was opened - run `pipeline breaker <slug> begin` first")
    want = json.loads(began.read_text())["spec_hash"]
    if want != h:
        sys.exit(f"the spec changed during the spec-breaker pass "
                 f"({want[:12]} -> {h[:12]}). The report reviewed neither version "
                 f"cleanly. Nothing may edit the spec while the Breaker is reading it.")
    if not (st.dir / "ambiguity.md").exists():
        sys.exit("the spec-breaker did not write ambiguity.md")
    (meta_dir / "ambiguity-meta.json").write_text(
        json.dumps({"spec_hash": h, "at": State(a.slug).data.get("created")}, indent=2) + "\n")
    st.log_step("breaker", True, h[:12])
    print(f"ambiguity.md bound to spec {h[:12]}")
    return 0


def cmd_spec_status(a) -> int:
    """Is the spec still the one Gate 1 approved?"""
    st = State(a.slug)
    h, frozen = spec_hash(st.dir), frozen_hash(st.dir)
    drift = spec_drift(st.dir)
    print(json.dumps({"slug": a.slug, "spec_hash": h, "frozen_hash": frozen,
                      "frozen": frozen is not None, "drift": drift}, indent=2))
    return 1 if drift else 0


def cmd_lock(a) -> int:
    """Rule 3, enforced. The write guard hook reads this file.

    `lock` is the first command every agent phase runs, so it carries the phase
    guard. That is what lets the workflows drop their separate `gate1-check` and
    `gate2-check` agents: the first real command already refuses to proceed.
    """
    st = State(a.slug)
    _guard(st, LOCK_PHASE_BY_FLOW[st.flow][a.tree])
    (st.dir / ".pipeline").mkdir(parents=True, exist_ok=True)
    (st.dir / ".pipeline" / "LOCK").write_text(a.tree + "\n")
    print(f"{a.slug}: writes restricted to {a.tree}/")
    return 0


def cmd_unlock(a) -> int:
    lock = State(a.slug).dir / ".pipeline" / "LOCK"
    lock.unlink(missing_ok=True)
    print(f"{a.slug}: write guard cleared")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="pipeline", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def slug_cmd(name, fn, **kw):
        p = sub.add_parser(name, **kw)
        p.add_argument("slug")
        p.set_defaults(fn=fn)
        return p

    nw = slug_cmd("new", cmd_new)
    nw.add_argument("--flow", type=int, default=2, choices=[1, 2],
                    help="2 (default) = requirements_doc.md, 16 steps and 4 gates. "
                         "1 = the original 12 steps and 3 gates.")
    slug_cmd("status", cmd_status)
    slug_cmd("next", cmd_next)
    slug_cmd("lint", cmd_lint)
    t = slug_cmd("test", cmd_test)
    t.add_argument("--target", default="app", choices=["app", "skeleton"])
    slug_cmd("cut", cmd_cut)
    dp = slug_cmd("deploy", cmd_deploy)
    dp.add_argument("--target", default="app", choices=["app", "skeleton"])
    dp.add_argument("--hold", type=int, default=0)
    stk = slug_cmd("stack", cmd_stack)
    stk.add_argument("--stack", required=True,
                     help="comma-separated, e.g. 'next,react,typescript'")
    stk.add_argument("--sessions", type=int, required=True)
    stk.add_argument("--minutes", type=int, default=40)
    stk.add_argument("--track", default="fullstack")
    stk.add_argument("--limits", default="")
    stk.add_argument("--by", default="")
    slug_cmd("ideas", cmd_ideas)
    pk = slug_cmd("pick", cmd_pick)
    pk.add_argument("n", type=int, help="which idea, e.g. 3 for ideas/idea-03.md")
    pk.add_argument("-m", "--note", default="")
    rf = slug_cmd("redfirst", cmd_redfirst)
    rf.add_argument("--target", default="app")
    rf.add_argument("--static-only", action="store_true")
    rf.add_argument("--no-report", action="store_true",
                    help="print the result, write no file, log no step - self-check only")
    mu = slug_cmd("mutation", cmd_mutation)
    mu.add_argument("--only", default="")
    mu.add_argument("--max", type=int, default=None)
    mu.add_argument("--force", action="store_true",
                    help="run it on a flow-1 project too")
    lk2 = slug_cmd("leak", cmd_leak)
    lk2.add_argument("--no-history", action="store_true")
    slug_cmd("guide-lint", cmd_guide_lint)
    hc = slug_cmd("handover-checks", cmd_handover_checks)
    hc.add_argument("--no-history", action="store_true")
    hc.add_argument("--force", action="store_true")
    dr = slug_cmd("dryrun", cmd_dryrun)
    dr.add_argument("--session", type=int, required=True)
    dr.add_argument("--minutes", type=int, required=True)
    dr.add_argument("--by", required=True, help="who taught it - not whoever built it")
    dr.add_argument("--could-not-teach", action="store_true")
    dr.add_argument("-m", "--note", default="")
    fb = slug_cmd("feedback", cmd_feedback)
    fb.add_argument("-m", "--note", default="")
    fb.add_argument("--session", type=int, default=None)
    fb.add_argument("--by", default="")

    g = slug_cmd("gate", cmd_gate)
    g.add_argument("n", type=int, choices=[0, 1, 2, 3])
    g.add_argument("decision", choices=["approve", "reject"])
    g.add_argument("-m", "--note", default="")
    g.add_argument("--override", action="store_true",
                   help="gate 1 only: approve despite the stopping rule. Needs -m, "
                        "and is recorded in state.json as an override.")
    slug_cmd("ship", cmd_ship)
    slug_cmd("revise", cmd_revise)
    slug_cmd("gate1-check", cmd_gate1_check)
    slug_cmd("spec-status", cmd_spec_status)
    br = slug_cmd("breaker", cmd_breaker)
    br.add_argument("mode", choices=["begin", "end"])
    lk = slug_cmd("lock", cmd_lock)
    lk.add_argument("tree", choices=["app", "verify", "pack", "skeleton"])
    slug_cmd("unlock", cmd_unlock)
    w = sub.add_parser("watch")
    w.add_argument("--only", default="")
    w.set_defaults(fn=cmd_watch)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
