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
import os
import shutil
import sys
import time
from pathlib import Path

from . import test_runner
from .cutter import CLOSE, OPEN, SKIP_DIRS, load_hints, todo_line, walk_source

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


def link_dir(src: Path, dst: Path) -> None:
    """Point dst at the directory src, as cheaply as this platform allows.

    os.symlink needs SeCreateSymbolicLinkPrivilege on Windows - without admin or
    Developer Mode it raises WinError 1314 - so every mutant failed to build and
    `pipeline mutation` crashed before writing a report. A junction needs no
    privilege and behaves the same way for reading node_modules. Copying is the
    last resort: correct, just slow, and node_modules is large.
    """
    try:
        os.symlink(src, dst, target_is_directory=True)
        return
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import _winapi
            _winapi.CreateJunction(str(src), str(dst))
            return
        except (ImportError, OSError):
            pass
    shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)


def graded_by(spec: dict, task_id: str) -> list[str]:
    return [c["id"] for s in spec.get("sessions", [])
            for c in s.get("criteria", []) if task_id in (c.get("cuts") or [])]


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
        results.append({
            "task": task,
            "ok": bool(red),
            "lines_removed": removed,
            "graded_by": expect,
            "went_red": red,
            "stayed_green": sorted(set(expect) - set(red)),
            "collateral": unexpected,
            "why": ("removing it turns its requirements red" if red else
                    "NOT GRADED: every requirement that declares this task still "
                    "passes with it removed, so a student can leave it empty"),
        })
        shutil.rmtree(mdir, ignore_errors=True)

    ungraded = [r["task"] for r in results if not r["ok"]]
    return {
        "ok": not ungraded and bool(results),
        "target": target,
        "checked": len(results),
        "of_total": len(hints),
        "seconds": round(time.time() - started, 1),
        "ungraded_tasks": ungraded,
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
