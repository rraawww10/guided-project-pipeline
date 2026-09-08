"""Red-first check - SCRIPT, step 5's checker (requirements_doc rule 2).

"Every new test must fail before the code is written. A test that passes early
proves nothing."

Two halves, because only one of them can run with no code on disk:

* `scan_assertions` is static and needs nothing. It reads the test files and
  flags a test with no assertion at all, or one whose only assertions are
  trivially true. That is the vacuous test the rule is really about, and it can
  be caught the moment the Test Writer finishes.

* `check_all_red` is dynamic. It boots a target where the marked blocks are
  unwritten and requires EVERY requirement's test to fail. Run it against the
  scaffold before the Builder fills anything in, and again against `student/`
  at step 10 - it is the same assertion at two points in the flow.

  python -m pipeline.redfirst <project-dir> [--target app|skeleton] [--static-only]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import test_runner

# `assert True`, `assert 1`, `assert x or True` - green whatever the code does.
TRIVIAL = re.compile(r"^\s*assert\s+(True|1|-1|not\s+False|\"[^\"]*\"|'[^']*')\s*(,|$)")

# A call that actually blocks until the page catches up. `expect(...)` is here
# because its matchers retry to a deadline; `wait_for_timeout` is deliberately
# NOT - it sleeps a fixed span and calls that waiting.
WAITS = re.compile(r"^(wait_for_(selector|url|load_state|function|event|response|request)"
                   r"|expect|to_have_\w+|to_be_\w+|not_to_\w+)$")


def _call_names(node: ast.AST) -> list[str]:
    """Every function name called anywhere under `node`, attribute or bare."""
    out = []
    for c in ast.walk(node):
        if not isinstance(c, ast.Call):
            continue
        f = c.func
        out.append(f.attr if isinstance(f, ast.Attribute) else
                   f.id if isinstance(f, ast.Name) else "")
    return out


def scan_waits(project: Path, target: str = "app") -> list[dict]:
    """A UI assertion that does not wait is red for reasons the Builder cannot fix.

    2026-09-07, game-arcade: `page.goto("/games")` then `assert rows.count() == 2`
    read `0 == 2` against a list a client-side fetch had not filled yet. Three
    criteria stayed red across five Builder retries and the app was right every
    time - but rule 3 forbids the Builder from touching verify/, so nobody in
    the loop could clear it. Static, so it lands at step 5 with no code on disk,
    which is a whole phase before that loop can start.

    Two shapes, both from that run:

    * `.count()` inside an assert, in a test that never waits for anything.
      `Locator.count()` answers immediately. It is legitimate AFTER an explicit
      wait - stock-tracker and demo-run-03 both do exactly that and must keep
      passing - so the flag needs the test to contain no wait at all.
    * `wait_for_timeout(...)` anywhere. A fixed sleep is the same bug with a
      longer fuse: green on a fast machine, red on the nightly watchdog.

    Blind spot, stated rather than hidden: this reads one test function at a
    time. A wait parked in a fixture or a helper in another file counts as "no
    wait here" and would be flagged.
    """
    out: list[dict] = []
    for path in _test_files(project, target):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue                      # scan_assertions already reports this
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            names = _call_names(node)
            for c in ast.walk(node):
                if isinstance(c, ast.Call) and (
                        (isinstance(c.func, ast.Attribute) and c.func.attr == "wait_for_timeout")
                        or (isinstance(c.func, ast.Name) and c.func.id == "wait_for_timeout")):
                    out.append({
                        "test": f"{path.name}::{node.name}", "line": c.lineno,
                        "problem": "wait_for_timeout() is a fixed sleep, not a wait",
                        "fix": "wait for the thing itself - expect(locator).to_have_count(n), "
                               "wait_for_selector(...), or the URL the app routes to"})
            if any(WAITS.match(n) for n in names):
                continue                  # this test does wait; count() is fine here
            for a in ast.walk(node):
                if not isinstance(a, ast.Assert):
                    continue
                src = "\n".join(lines[a.lineno - 1:getattr(a, "end_lineno", a.lineno)])
                if ".count()" not in src:
                    continue
                out.append({
                    "test": f"{path.name}::{node.name}", "line": a.lineno,
                    "problem": "asserts on .count(), which does not wait, and this "
                               "test never waits for anything",
                    "fix": "expect(locator).to_have_count(n) - it retries to a deadline"})
    return out


def _test_files(project: Path, target: str) -> list[Path]:
    for d in ((project / target / "verify"), (project / "verify"),
              (project / target / "tests"), (project / "tests")):
        if d.exists():
            return sorted(p for p in d.rglob("test_*.py"))
    return []


def scan_assertions(project: Path, target: str = "app") -> list[dict]:
    """A test with no real assertion cannot go red. Needs no code to run."""
    out: list[dict] = []
    for path in _test_files(project, target):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            out.append({"test": path.name, "problem": f"does not parse: {e}"})
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            body = ast.walk(node)
            asserts = [n for n in body if isinstance(n, ast.Assert)]
            # pytest.raises / a helper that asserts internally also counts
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
            named = " ".join(
                (c.func.attr if isinstance(c.func, ast.Attribute) else
                 c.func.id if isinstance(c.func, ast.Name) else "")
                for c in calls)
            helps = bool(re.search(r"raises|expect|to_have|to_be|assert", named))
            if not asserts and not helps:
                out.append({"test": f"{path.name}::{node.name}", "line": node.lineno,
                            "problem": "no assertion - cannot go red"})
                continue
            trivial = [a for a in asserts
                       if a.lineno <= len(lines) and TRIVIAL.match(lines[a.lineno - 1])]
            if asserts and len(trivial) == len(asserts) and not helps:
                out.append({"test": f"{path.name}::{node.name}", "line": node.lineno,
                            "problem": "every assertion is trivially true"})
    return out


def check_all_red(project: Path, target: str = "app") -> dict:
    """Every requirement's test must fail while its block is unwritten."""
    rc = test_runner.main([str(project), "--target", target,
                           "--out", "redfirst-results.json"])
    res = json.loads((project / "redfirst-results.json").read_text(encoding="utf-8"))
    crit = res.get("criteria", {})
    green = [{"criterion": cid, "test": c.get("test")}
             for cid, c in sorted(crit.items()) if c.get("status") == "pass"]
    return {
        "ran": True,
        "ok": not green and bool(crit),
        "target": target,
        "checked": len(crit),
        "passed_too_early": green,
        "counts": res.get("counts", {}),
        "why": ("every test is red before the code is written"
                if not green and crit else
                "these tests pass with the block unwritten, so they do not grade it"
                if green else "no criteria were collected - the suite did not run"),
        "runner_returncode": rc,
    }


def check_runnable(project: Path) -> dict:
    """Can pytest resolve every test's fixtures, with no app in existence?

    The dynamic half cannot answer this. At step 5 there is no app/, so the
    server never boots, every criterion comes back `missing`, and check_all_red
    reads that as "no test passed early" and approves - the same all-missing
    shape mutation.py already learned to distrust. ui-live-01 and demo-run-01
    both looked exactly like this with sound suites, so the shape alone proves
    nothing either way.

    demo-run-02 is what that costs. Its Test Writer wrote no conftest.py, so
    `page` did not exist and all ten UI tests errored on setup. Red-first passed,
    Gate 1 approved, and the break only surfaced at step 7 - as ten red criteria
    routed to the Builder, which rule 3 forbids from touching verify/. A red
    nobody in the loop can clear.

    `--setup-plan` resolves fixtures without running anything, so it needs no
    app: BASE_URL is set to a dead address only because suites read it at import
    time. It found all ten in 0.42 seconds.
    """
    verify = project / "verify"
    if not verify.exists():
        return {"ran": False, "ok": False, "why": "verify/ does not exist"}
    try:
        py = test_runner.ensure_venv(project)
    except Exception as exc:                      # a venv we cannot build is a
        return {"ran": False, "ok": True,         # pipeline fault, not a verdict
                "why": f"could not prepare an interpreter: {type(exc).__name__}: {exc}"}
    env = {**os.environ, "BASE_URL": "http://127.0.0.1:1",
           "APP_DIR": str(project / "app"), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        proc = subprocess.run(
            [str(py), "-m", "pytest", str(verify), "--setup-plan", "-q",
             "-p", "no:cacheprovider"],
            cwd=str(project), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300)
    except Exception as exc:
        return {"ran": False, "ok": True,
                "why": f"could not run the fixture plan: {type(exc).__name__}: {exc}"}
    text = (proc.stdout or "") + (proc.stderr or "")
    broken = sorted({ln.split(" ", 1)[1].strip()
                     for ln in text.splitlines()
                     if ln.startswith("ERROR ") and " " in ln})
    return {
        "ran": True,
        "ok": not broken,
        "broken": broken[:40],
        "count": len(broken),
        "why": ("every test's fixtures resolve" if not broken else
                "these tests cannot run at all - a fixture or import is missing, "
                "and the Builder cannot fix it because rule 3 forbids it editing "
                "verify/"),
        "detail": "" if not broken else text[-1500:],
    }


def run(project: Path, target: str = "app", static_only: bool = False) -> dict:
    vacuous = scan_assertions(project, target)
    unwaited = scan_waits(project, target)
    runnable = check_runnable(project)
    report: dict = {
        "ok": not vacuous and not unwaited and runnable.get("ok", True),
        "target": target,
        "vacuous_tests": vacuous,
        "unwaited_assertions": unwaited,
        "runnable": runnable,
        "dynamic": None,
    }
    if not static_only:
        dyn = check_all_red(project, target)
        report["dynamic"] = dyn
        report["ok"] = report["ok"] and dyn["ok"]
    else:
        report["dynamic"] = {"ran": False,
                             "why": "--static-only: the dynamic half needs a target "
                                    "whose marked blocks are unwritten"}
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--target", default="app", choices=["app", "skeleton"])
    ap.add_argument("--static-only", action="store_true")
    # A locked agent needs to check its own work without recording a verdict.
    # redfirst.json is written at the PROJECT ROOT, and the Test Writer runs at
    # step 5 locked to verify/ - so self-checking produced a file it was then
    # refused permission to clean up, and left dynamic.ran=false sitting where a
    # reader at Gate 1 could mistake it for evidence that the dynamic half had
    # passed. The report is the orchestrator's to write; the check is anyone's
    # to run.
    ap.add_argument("--no-report", action="store_true",
                    help="print the result, write no file - for an agent checking itself")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    report = run(project, a.target, a.static_only)
    if not a.no_report:
        (project / "redfirst.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
