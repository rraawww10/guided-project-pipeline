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
import re
import sys
from pathlib import Path

from . import test_runner

# `assert True`, `assert 1`, `assert x or True` - green whatever the code does.
TRIVIAL = re.compile(r"^\s*assert\s+(True|1|-1|not\s+False|\"[^\"]*\"|'[^']*')\s*(,|$)")


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


def run(project: Path, target: str = "app", static_only: bool = False) -> dict:
    vacuous = scan_assertions(project, target)
    report: dict = {
        "ok": not vacuous,
        "target": target,
        "vacuous_tests": vacuous,
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
