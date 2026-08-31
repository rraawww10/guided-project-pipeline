"""Mutation check - SCRIPT, step 8's second checker (requirements_doc rule 3).

"The verifier is checked by a script. It must cover every requirement, and it
must go red when we deliberately break the code. Otherwise a useless test looks
green."

The mutation used here is the most meaningful one available: **remove exactly one
student task and leave every other one written.** For each task in turn, the
suite must go red on at least one requirement that declares it. A task no
requirement notices is a task that grades nothing - the bypassable-cut defect
that shipped twice before anything looked for it.

This is also the partial-subset proof the skeleton check cannot give. That check
sees only two states, all-tasks-open and no-tasks-open, so it says nothing about
the states a student actually moves through. Single-task mutants are exactly
those states, and there are N of them, not 2^N.

The cost is one boot and build per task, so it is opt-in and can be narrowed:

  python -m pipeline.mutation <project-dir> [--only S03-T01,cut-x] [--max N]

Exit 0 when every task is graded, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from . import test_runner
from .cutter import (CLOSE, OPEN, SKIP_DIRS, link_dir, load_hints, todo_line,
                     walk_source)

MUTANT_ROOT = Path(".pipeline") / "mutants"


def mutate_one(app: Path, out: Path, task_id: str, hints: dict) -> int:
    """Write a copy of `app` with only `task_id` unwritten.

    Every other task's markers are stripped and its body kept, so the result is
    "a student who has done everything except this one".
    """
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    removed = 0
    for src in walk_source(app, respect_gitignore=False):
        rel = src.relative_to(app)
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src.read_text()
        except UnicodeDecodeError:
            shutil.copy2(src, dst)
            continue
        if ">>> CUT" not in text and "STUDENT" not in text:
            shutil.copy2(src, dst)
            continue

        lines_out: list[str] = []
        open_id: str | None = None
        for line in text.splitlines():
            mo, mc = OPEN.match(line), CLOSE.match(line)
            if mo and not mc:
                open_id = mo["id"]
                if open_id == task_id:
                    hint = (hints.get(task_id) or {}).get("hint", "")
                    lines_out.append(todo_line(rel, mo["indent"], task_id, hint,
                                               "{/*" in mo["lead"]))
                continue                      # marker lines never survive
            if mc:
                open_id = None
                continue
            if open_id == task_id:
                removed += 1
                continue                      # this is the block being removed
            lines_out.append(line)
        dst.write_text("\n".join(lines_out) + ("\n" if text.endswith("\n") else ""))
    # the mutant needs the app's modules to build
    nm = out / "node_modules"
    if not nm.exists() and (app / "node_modules").exists():
        link_dir((app / "node_modules").resolve(), nm)
    return removed


def graded_by(spec: dict, task_id: str) -> list[str]:
    return [c["id"] for s in spec.get("sessions", [])
            for c in s.get("criteria", []) if task_id in (c.get("cuts") or [])]


def _apply_run_control(results: list[dict]) -> None:
    """Take the harness-alive control from the run, not from the mutant.

    Per-mutant, "did anything pass" is the only evidence available that the
    harness was working, and it is unavailable by construction to a cut every
    criterion declares - its expected set IS the suite, so nothing is left over
    to stay green. That is not a rare shape: pipeline-test-03's cut-parse-line,
    and recipe-box's and tip-split's cut-store-read-all, are all declared by
    every criterion in their project.

    Across the run the evidence does exist. Mutants are independent runs of the
    same harness minutes apart, so one mutant that produced a passing criterion
    proves the harness boots, serves and grades. An all-red mutant in that same
    run is then a real result rather than an ambiguous one.

    Two independent conditions, both required, because a false green is this
    checker's worst outcome:

      1. some *other* mutant in this run produced a passing criterion - the
         harness is proven live by a run that is not this one;
      2. this mutant produced real per-test outcomes - at least one pass or
         fail, not the all-`missing` shape the original guard was written for,
         where a target whose log path could not be created reported every
         criterion missing and passed every task vacuously.

    Neither alone is enough. Condition 2 alone would trust a run whose harness
    was broken for every mutant; condition 1 alone would trust a mutant that
    never reported a per-test outcome at all.
    """
    live = any(r.get("_outcomes") and not r["inconclusive"] for r in results)
    for r in results:
        if r["inconclusive"] and live and r.get("_outcomes"):
            r["inconclusive"] = False
            r["ok"] = bool(r["went_red"])
            r["why"] = (
                "removing it turns its requirements red - every criterion in the "
                "project declares this task, so no criterion could stay green to "
                "prove the harness was alive; another mutant in this run produced "
                "a passing criterion, which proves it, and this mutant reported "
                "real per-test outcomes rather than the all-missing shape"
                if r["went_red"] else
                "NOT GRADED: every requirement that declares this task still "
                "passes with it removed, so a student can leave it empty")
    for r in results:
        r.pop("_outcomes", None)


def run(project: Path, only: list[str] | None = None, max_tasks: int | None = None,
        target: str = "app") -> dict:
    spec = json.loads((project / "spec.json").read_text())
    hints = load_hints(spec)
    tasks = [t for t in sorted(hints) if not only or t in only]
    if max_tasks:
        tasks = tasks[:max_tasks]

    results: list[dict] = []
    started = time.time()
    for task in tasks:
        mdir = project / MUTANT_ROOT / task
        rel_target = str(mdir.relative_to(project))
        removed = mutate_one(project / target, mdir, task, hints)
        expect = graded_by(spec, task)
        rc = 1
        crit: dict = {}
        try:
            rc = test_runner.main([str(project), "--target", rel_target,
                                   "--out", f".pipeline/mutants/{task}-results.json"])
            crit = json.loads(
                (project / ".pipeline" / "mutants" / f"{task}-results.json").read_text()
            ).get("criteria", {})
        except Exception as e:                       # a mutant that will not boot
            results.append({"task": task, "ok": False, "error": f"{type(e).__name__}: {e}",
                            "lines_removed": removed, "graded_by": expect})
            shutil.rmtree(mdir, ignore_errors=True)
            continue
        red = sorted(cid for cid in expect
                     if crit.get(cid, {}).get("status") in ("fail", "missing"))
        unexpected = sorted(cid for cid, c in crit.items()
                            if cid not in expect and c.get("status") in ("fail", "missing"))
        # A mutant that removes ONE task should leave the rest of the suite green.
        # If nothing passes, the mutant did not run, and "every requirement went
        # red" is not evidence that the task is graded - it is evidence of
        # nothing. This check reports on rule 3, so a false green is the worst
        # outcome it has: for the whole life of the mutation check, a target
        # whose log path could not be created reported all criteria "missing",
        # counted every one as red, and passed every task vacuously.
        ran = any(c.get("status") == "pass" for c in crit.values())
        # A cut every criterion declares has no criterion outside its expected
        # set, so `ran` can never be true for it however healthy the harness is:
        # pipeline-test-03's cut-parse-line went 9 red of 9 with the suite
        # plainly executing (junit tests=9 failures=9 errors=0) and was still
        # called "never ran". Whether the suite produced real per-test outcomes
        # is the other half of the question, and it is what separates this from
        # the failure the guard above exists for - a target whose log path could
        # not be created reported every criterion *missing*, not failed.
        outcomes = any(c.get("status") in ("pass", "fail") for c in crit.values())
        results.append({
            "task": task,
            "ok": bool(red) and ran,
            "inconclusive": not ran,
            "_outcomes": outcomes,
            "lines_removed": removed,
            "graded_by": expect,
            "went_red": red,
            "stayed_green": sorted(set(expect) - set(red)),
            "collateral": unexpected,
            "why": ("INCONCLUSIVE: no criterion passed against this mutant, so it "
                    "never ran - this proves nothing about whether the task is graded"
                    if not ran else
                    "removing it turns its requirements red" if red else
                    "NOT GRADED: every requirement that declares this task still "
                    "passes with it removed, so a student can leave it empty"),
        })
        shutil.rmtree(mdir, ignore_errors=True)

    _apply_run_control(results)

    ungraded = [r["task"] for r in results if not r["ok"] and not r.get("inconclusive")]
    inconclusive = [r["task"] for r in results if r.get("inconclusive")]
    return {
        "ok": not ungraded and not inconclusive and bool(results),
        "target": target,
        "checked": len(results),
        "of_total": len(hints),
        "seconds": round(time.time() - started, 1),
        "ungraded_tasks": ungraded,
        "inconclusive_tasks": inconclusive,
        "results": results,
        "rule": ("every student task must turn at least one of its requirements red "
                 "when it alone is removed"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--only", default="", help="comma-separated task ids")
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--target", default="app")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    only = [x.strip() for x in a.only.split(",") if x.strip()] or None
    report = run(project, only, a.max, a.target)
    (project / "mutation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in
                      ("ok", "checked", "of_total", "seconds", "ungraded_tasks")},
                     indent=2))
    for r in report["results"]:
        if not r["ok"]:
            print(f"\nUNGRADED {r['task']}: {r.get('why') or r.get('error')}",
                  file=sys.stderr)
    shutil.rmtree(project / MUTANT_ROOT, ignore_errors=True)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
