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
import re
import shutil
import sys
import time
from pathlib import Path

from . import test_runner
from .cutter import (CLOSE, OPEN, SKIP_DIRS, link_dir, load_hints, todo_line,
                     walk_source)

MUTANT_ROOT = Path(".pipeline") / "mutants"


# The verdict a reader acts on, and the one basic_needs_v1 §9.3 is about: a
# task nothing turns red is a task a student can skip. One definition, because
# it is reached from two places - the per-mutant path in `run` and the
# reclassifying path in `_apply_run_control`.
NOT_GRADED = ("NOT GRADED: every requirement that declares this task still "
              "passes with it removed, so a student can leave it empty")


# `next build` picks Turbopack from Next 16 on, and Turbopack refuses a
# node_modules that is a link out of the build root:
#
#   Error [TurbopackInternalError]: Symlink node_modules is invalid,
#   it points out of the filesystem root
#
# A mutant borrows the app's node_modules rather than installing its own -
# sixteen installs per run is not affordable - so on Next 16 every mutant
# failed to build, every criterion went red, and `ran` was false for all of
# them. That reads as INCONCLUSIVE, not as a wrong answer, so nothing shipped
# on it; it just meant rule 3 could not be checked at all. Webpack follows the
# link, so ask for it by name.
#
# Only from 16: `--webpack` does not exist before it (Next 15.5 rejects the
# flag outright), and Next 15 already builds with webpack anyway. Read the
# version off the modules the mutant will actually build against, not off
# package.json - demo-run-03 declares 16.1.1 and has 14.2.5 installed.
def _prefer_webpack(app: Path, out: Path) -> str:
    """Pin the mutant's build to webpack where Turbopack would refuse the link.

    Edits only the throwaway mutant tree. Returns what it did, for the caller
    that wants to say so; "" when it left the build script alone.
    """
    pkg = out / "package.json"
    ver = app / "node_modules" / "next" / "package.json"
    if not pkg.exists() or not ver.exists():
        return ""
    try:
        major = int(json.loads(ver.read_text(encoding="utf-8"))["version"].split(".")[0])
    except (ValueError, KeyError, json.JSONDecodeError):
        return ""
    if major < 16:
        return ""
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    build = (data.get("scripts") or {}).get("build", "")
    if not build or "--webpack" in build:
        return ""
    # An explicit --turbopack is swapped too: honouring it would leave the
    # check unable to run, and the mutant exists only to say which criteria
    # go red, not to decide which bundler the project ships with.
    fixed = build.replace("--turbopack", "--webpack").replace("--turbo", "--webpack")
    if "--webpack" not in fixed:
        fixed = fixed.replace("next build", "next build --webpack", 1)
    if fixed == build:
        return ""
    data["scripts"]["build"] = fixed
    pkg.write_text(json.dumps(data, indent=2) + chr(10), encoding="utf-8")
    return fixed


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
            text = src.read_text(encoding="utf-8")
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
        dst.write_text("\n".join(lines_out) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    # the mutant needs the app's modules to build
    nm = out / "node_modules"
    if not nm.exists() and (app / "node_modules").exists():
        link_dir((app / "node_modules").resolve(), nm)
        _prefer_webpack(app, out)
    return removed


SETTER = re.compile(r"\bset([A-Z]\w*)\s*\(")


def scan_dead_cuts(app: Path, tasks: list[str]) -> list[dict]:
    """A cut whose only effect is state nobody reads can never be graded.

    2026-09-07, game-arcade: `cut-ui-append-guess` called `setGuessesState`,
    and `guessesState` appeared exactly once in the file - its own declaration -
    while the board rendered from a second state that `await loadGame()` refilled
    from the server on the next line. The pair was balanced, correctly placed and
    compiled; the mutant built and ran; and the answer was still NOT GRADED after
    2052 seconds of booting and building sixteen trees.

    Worse than the cost is the routing. NOT GRADED is read as "the suite is weak"
    and goes to the Verifier, which rule 3 hooks out of `app/` - it cannot make a
    test observe state the code never reads, at any price. That run spent four
    attempts there. This check answers the same question statically, before the
    first build, and names the Builder.

    Reads the React setter convention, which is what this pipeline's stack
    produces: `setFoo(...)` in the block means the block's effect is `foo`, and
    `foo` must be READ somewhere outside this task's own block - a mention that
    is neither its `useState` declaration nor another `setFoo` call. A read
    inside a DIFFERENT cut is fine: mutation removes one task at a time, so that
    block is present when this one is missing.

    Blind spot, stated rather than hidden: a block whose effect is not a setter -
    a direct DOM write, a mutated ref, an imperative call - is not modelled here
    and still relies on the full run to catch it.
    """
    dead: list[dict] = []
    for src in walk_source(app, respect_gitignore=False):
        try:
            text = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if ">>> CUT" not in text:
            continue
        lines = text.splitlines()
        blocks: dict[str, list[int]] = {}
        open_id, open_at = None, 0
        for i, line in enumerate(lines):
            mo, mc = OPEN.match(line), CLOSE.match(line)
            if mo and not mc:
                open_id, open_at = mo["id"], i
            elif mc and open_id:
                blocks.setdefault(open_id, []).extend(range(open_at, i + 1))
                open_id = None
        for task, own in blocks.items():
            if task not in tasks:
                continue
            body = "\n".join(lines[i] for i in own)
            outside = [ln for i, ln in enumerate(lines) if i not in set(own)]
            for setter in sorted(set(SETTER.findall(body))):
                sym = setter[0].lower() + setter[1:]
                word = re.compile(rf"\b{re.escape(sym)}\b")
                reads = [ln for ln in outside if word.search(ln)
                         and not re.search(rf"\[\s*{re.escape(sym)}\s*,", ln)
                         and not re.search(rf"\bset{re.escape(setter)}\b", ln)]
                if not reads:
                    dead.append({
                        "task": task,
                        "file": str(src.relative_to(app)).replace(chr(92), "/"),
                        "symbol": sym,
                        "owner": "builder",
                        "why": f"the block sets `{sym}` and nothing outside it ever reads "
                               f"`{sym}`, so removing the block changes nothing a "
                               f"criterion can see - a student can leave it empty",
                        "fix": f"make the block the only path to the thing the criterion "
                               f"looks at: render from `{sym}`, and do not re-read the "
                               f"server underneath it"})
    return dead


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
                NOT_GRADED)
    for r in results:
        r.pop("_outcomes", None)


def classify_run(results: list[dict]) -> dict:
    """The run-level verdict: which tasks grade nothing, and whether the run passed.

    Factored out of `run` so the decision can be exercised without booting and
    building once per mutant. That matters for basic_needs_v1 acceptance
    criterion 3 - "the mutation check catches a fake browser test (one that only
    checks the page loads)" - because that is precisely this decision. A test
    which only asserts the page loaded still passes once the task it nominally
    grades is removed, so nothing goes red, and the task has to come back
    reported as grading nothing rather than as a pass.

    Applies the run-level harness control first, exactly as `run` does, so a
    caller testing this is testing the whole decision and not half of it.
    """
    _apply_run_control(results)
    ungraded = [r["task"] for r in results if not r["ok"] and not r.get("inconclusive")]
    inconclusive = [r["task"] for r in results if r.get("inconclusive")]
    return {
        "ok": not ungraded and not inconclusive and bool(results),
        "ungraded_tasks": ungraded,
        "inconclusive_tasks": inconclusive,
    }


def run(project: Path, only: list[str] | None = None, max_tasks: int | None = None,
        target: str = "app") -> dict:
    spec = json.loads((project / "spec.json").read_text(encoding="utf-8"))
    hints = load_hints(spec)
    tasks = [t for t in sorted(hints) if not only or t in only]
    if max_tasks:
        tasks = tasks[:max_tasks]

    started = time.time()
    # Before sixteen boots and builds: any task this can already prove ungraded,
    # it proves in milliseconds - and names the Builder, which is the owner
    # NOT_GRADED routing gets wrong. Fail here and the run costs a second
    # instead of the 2052 it cost game-arcade to reach the same answer.
    dead = scan_dead_cuts(project / target, tasks)
    if dead:
        return {
            "ok": False, "ungraded_tasks": sorted({d["task"] for d in dead}),
            "inconclusive_tasks": [], "dead_cuts": dead, "owner": "builder",
            "target": target, "checked": 0, "of_total": len(hints),
            "seconds": round(time.time() - started, 1), "results": [],
            "rule": ("a student task must have an effect something outside its own "
                     "block reads, or no test can grade it"),
        }

    results: list[dict] = []
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
                (project / ".pipeline" / "mutants" / f"{task}-results.json").read_text(encoding="utf-8")
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
                    NOT_GRADED),
        })
        shutil.rmtree(mdir, ignore_errors=True)

    verdict = classify_run(results)
    return {
        **verdict,
        "target": target,
        "dead_cuts": [],
        "checked": len(results),
        "of_total": len(hints),
        "seconds": round(time.time() - started, 1),
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
    (project / "mutation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
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
