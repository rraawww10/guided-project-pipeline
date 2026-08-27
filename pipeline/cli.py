"""Orchestrator - SCRIPT, the thing that runs the twelve steps in order.

Rule 5: the orchestrator is plain code. No agent manages another agent.
This CLI is the single entry point for every script step and every gate.

  python -m pipeline new <slug>
  python -m pipeline status <slug>
  python -m pipeline lint <slug>              # step 2 checker
  python -m pipeline test <slug>              # step 6 checker
  python -m pipeline cut <slug>               # step 8
  python -m pipeline deploy <slug>            # step 10
  python -m pipeline lock <slug> app|verify|pack   # rule 3, before an agent step
  python -m pipeline unlock <slug>
  python -m pipeline revise <slug>            # archive a rejected round, reset gate 1
  python -m pipeline gate <slug> 1|2|3 approve|reject [-m note]
  python -m pipeline ship <slug>              # step 12
  python -m pipeline watch                    # nightly watchdog
  python -m pipeline next <slug>              # what the pipeline wants next
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import cutter, deploy_check, spec_linter, test_runner, watchdog
from .state import GATES, RETRY_LIMIT, State, project_dir

HERE = Path(__file__).parent

# step -> (phase, who, what the orchestrator does about it)
STEPS = [
    (1, "spec", "PERSON", "write idea.md"),
    (2, "spec", "AGENT", "spec-writer  -> spec.md, spec.json   (checked by: lint)"),
    (3, "spec", "AGENT", "spec-breaker -> ambiguity.md         (one pass, you read it)"),
    (4, "spec", "GATE", "gate 1 - approve the spec"),
    (5, "code", "AGENT", "builder      -> app/                 (checked by: test)"),
    (6, "code", "AGENT", "verifier     -> verify/              (checked by: test)"),
    (7, "code", "GATE", "gate 2 - read the pass or fail list"),
    (8, "pack", "SCRIPT", "cut          -> skeleton/"),
    (9, "pack", "AGENT", "pack-writer  -> pack/                (one pass, you read it)"),
    (10, "pack", "SCRIPT", "deploy       -> deploy.json"),
    (11, "pack", "GATE", "gate 3 - approve the pack"),
    (12, "pack", "SCRIPT", "ship         -> handover + nightly watchdog"),
]


def _guard(st: State, phase: str) -> None:
    ok, why = st.may_enter(phase)
    if not ok:
        sys.exit(f"blocked: {why}")
    if st.exhausted(phase):
        t = st.data["ticket"]
        sys.exit(f"blocked: phase '{phase}' hit the {RETRY_LIMIT} retry limit.\n"
                 f"ticket raised {t['raised']}\nlast error: {t['last_error']}")


def cmd_new(a) -> int:
    d = project_dir(a.slug)
    if d.exists():
        sys.exit(f"{d} already exists")
    (d / ".pipeline").mkdir(parents=True)
    shutil.copy(HERE / "templates" / "idea_template.md", d / "idea.md")
    shutil.copy(HERE / "templates" / "CONTRACT.md", d / ".pipeline" / "CONTRACT.md")
    State(a.slug).save()
    print(f"created {d}\nnext: write {d / 'idea.md'}, then run `python -m pipeline next {a.slug}`")
    return 0


def cmd_lint(a) -> int:
    st = State(a.slug)
    _guard(st, "spec")
    rc = spec_linter.main(["", str(st.dir)])
    if rc != 0:
        report = json.loads((st.dir / "lint.json").read_text())
        first = report["errors"][0] if report["errors"] else {}
        n = st.burn_retry("spec", f"{first.get('code')} {first.get('where')}: {first.get('message')}")
        print(f"\nspec retry {n}/{RETRY_LIMIT} - send lint.json back to the spec-writer")
    st.log_step("lint", rc == 0)
    return rc


def cmd_test(a) -> int:
    st = State(a.slug)
    _guard(st, "code")
    rc = test_runner.main([str(st.dir), "--target", a.target])
    if a.target == "app" and rc != 0:
        res = json.loads((st.dir / "results.json").read_text())
        failed = [c for c, v in res.get("criteria", {}).items() if v["status"] != "pass"]
        n = st.burn_retry("code", f"failing criteria: {', '.join(failed[:8])}")
        print(f"\ncode retry {n}/{RETRY_LIMIT} - send results.json back to the builder")
    st.log_step(f"test:{a.target}", rc == 0)
    return rc


def cmd_cut(a) -> int:
    st = State(a.slug)
    _guard(st, "pack")
    rc = cutter.main(["", "cut", str(st.dir)])
    if rc != 0:
        st.log_step("cut", False)
        return rc
    # the skeleton must fail exactly the tests whose cuts were removed
    test_runner.main([str(st.dir), "--target", "skeleton"])   # failures here are expected
    rc = cutter.main(["", "verify", str(st.dir)])
    if rc != 0:
        print("\nthe skeleton does not fail the right tests - fix the cut markers in app/, "
              "never the skeleton (rule 4)")
    st.log_step("cut", rc == 0)
    return rc


def cmd_deploy(a) -> int:
    st = State(a.slug)
    _guard(st, "pack")
    rc = deploy_check.main([str(st.dir), "--target", a.target, "--hold", str(a.hold)])
    st.log_step("deploy", rc == 0)
    return rc


def cmd_gate(a) -> int:
    st = State(a.slug)
    gate = f"gate{a.n}"
    approved = a.decision == "approve"
    if approved:
        blockers = _gate_blockers(st, a.n)
        if blockers:
            sys.exit("cannot approve - these have not passed yet:\n  " + "\n  ".join(blockers))
    st.record_gate(gate, approved, a.note)
    if approved and a.n < 3:
        st.data["phase"] = ["spec", "code", "pack"][a.n]
        st.save()
    print(f"{gate}: {'approved' if approved else 'rejected'}"
          + (f" - {a.note}" if a.note else ""))
    if not approved:
        back = {1: "step 2, spec-writer", 2: "step 5, builder", 3: "step 9, pack-writer"}[a.n]
        print(f"sent back to {back}")
    return 0


def _gate_blockers(st: State, n: int) -> list[str]:
    d, out = st.dir, []
    if n == 1:
        lint = d / "lint.json"
        if not lint.exists() or not json.loads(lint.read_text())["ok"]:
            out.append("spec linter has not passed (run: pipeline lint)")
        if not (d / "ambiguity.md").exists():
            out.append("spec-breaker has not run (ambiguity.md missing)")
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
    print(f"{a.slug} shipped. The nightly watchdog will replay its tests from now on.\n"
          f"cron: 0 2 * * * cd {Path.cwd()} && python -m pipeline watch")
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


def cmd_next(a) -> int:
    """What the pipeline wants next. The Claude workflow calls this to stay in sync."""
    st = State(a.slug)
    d, done = st.dir, []
    checks = [
        (1, (d / "idea.md").exists() and "<Project title>" not in (d / "idea.md").read_text()),
        (2, (d / "lint.json").exists() and json.loads((d / "lint.json").read_text())["ok"]),
        (3, (d / "ambiguity.md").exists()),
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
        step = next(s for s in STEPS if s[0] == n)
        print(json.dumps({"step": n, "phase": step[1], "who": step[2], "do": step[3],
                          "retries_left": st.remaining(step[1]),
                          "completed": done}, indent=2))
        return 0
    print(json.dumps({"step": None, "do": "done - shipped", "completed": done}, indent=2))
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
    moved = []
    for name in ("spec.md", "spec.json", "lint.json", "ambiguity.md"):
        src = st.dir / name
        if src.exists():
            shutil.move(str(src), str(dest / name))
            moved.append(name)
    gate = st.data["gates"].get("gate1") or {}
    (dest / "why.md").write_text(
        f"# Round {n}\n\nGate 1: {'rejected' if gate and not gate.get('approved') else 'not decided'}\n"
        f"Note: {gate.get('note', '')}\n")
    st.data["gates"]["gate1"] = None          # the next round faces a fresh gate
    st.log_step(f"revise:round-{n}", True, ", ".join(moved))
    print(f"archived round {n} to {dest} ({', '.join(moved)})")
    print(f"gate1 reset - the revised spec must be approved on its own merits")
    return 0


def cmd_lock(a) -> int:
    """Rule 3, enforced. The write guard hook reads this file."""
    st = State(a.slug)
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

    slug_cmd("new", cmd_new)
    slug_cmd("status", cmd_status)
    slug_cmd("next", cmd_next)
    slug_cmd("lint", cmd_lint)
    t = slug_cmd("test", cmd_test)
    t.add_argument("--target", default="app", choices=["app", "skeleton"])
    slug_cmd("cut", cmd_cut)
    dp = slug_cmd("deploy", cmd_deploy)
    dp.add_argument("--target", default="app", choices=["app", "skeleton"])
    dp.add_argument("--hold", type=int, default=0)
    g = slug_cmd("gate", cmd_gate)
    g.add_argument("n", type=int, choices=[1, 2, 3])
    g.add_argument("decision", choices=["approve", "reject"])
    g.add_argument("-m", "--note", default="")
    slug_cmd("ship", cmd_ship)
    slug_cmd("revise", cmd_revise)
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
