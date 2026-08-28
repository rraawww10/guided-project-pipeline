"""Leak scan - SCRIPT, step 10's second checker (requirements_doc rule 6).

"Solutions must not appear in comments, README, migrations, seed data, or git
history."

The answer to a student task is the block between its markers in the solution.
This scans the generated student tree for those lines - in any file, including
the ones nobody thinks to check: a leftover comment, the README, a seed fixture,
a migration. Then it asks git whether an earlier commit of the student tree
carried them, because deleting a leak does not remove it from history.

A line only counts as a leak if it is **unique to the answer**: present inside
the markers and nowhere in the solution outside them. Otherwise every `}` and
every `return found` would be a finding.

  python -m pipeline.leak_scan <project-dir> [--solution app] [--student skeleton]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from .cutter import CLOSE, OPEN, walk_source

# A line has to carry enough of the answer to be worth reporting.
MIN_CHARS = 18
MIN_TOKENS = 3
# Structural lines that say nothing about the answer.
NOISE = re.compile(r"^[\s{}()\[\];,]*$|^\s*(else|try|finally|return|break|continue)\s*[{:]?\s*$")


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def answer_lines(solution: Path) -> tuple[dict[str, set[str]], set[str]]:
    """(task id -> its answer lines, every line outside any marker)."""
    inside: dict[str, set[str]] = {}
    outside: set[str] = set()
    for src in walk_source(solution, respect_gitignore=False):
        try:
            text = src.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        open_id = None
        for line in text.splitlines():
            mo, mc = OPEN.match(line), CLOSE.match(line)
            if mo and not mc:
                open_id = mo["id"]
                continue
            if mc:
                open_id = None
                continue
            n = _norm(line)
            if not n:
                continue
            if open_id:
                inside.setdefault(open_id, set()).add(n)
            else:
                outside.add(n)
    return inside, outside


def _interesting(line: str) -> bool:
    return (len(line) >= MIN_CHARS and len(line.split()) >= MIN_TOKENS
            and not NOISE.match(line))


def scan_tree(student: Path, answers: dict[str, set[str]]) -> list[dict]:
    hits: list[dict] = []
    flat = {line: task for task, lines in answers.items() for line in lines}
    if not flat:
        return hits
    for path in sorted(student.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(student)
        if any(part in {"node_modules", ".next", ".git", "__pycache__"} for part in rel.parts):
            continue
        try:
            text = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for n, raw in enumerate(text.splitlines(), start=1):
            line = _norm(raw)
            if line in flat:
                hits.append({"where": "student tree", "file": rel.as_posix(),
                             "line": n, "task": flat[line], "leaked": line[:160]})
    return hits


def scan_git_history(repo_root: Path, student: Path,
                     answers: dict[str, set[str]]) -> list[dict]:
    """A leak that was committed once is still in the history."""
    flat = {line: task for task, lines in answers.items() for line in lines}
    if not flat:
        return []
    try:
        rel = student.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return []
    try:
        r = subprocess.run(["git", "log", "--all", "-p", "--unified=0", "--", rel],
                           cwd=repo_root, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []
    hits: list[dict] = []
    commit = ""
    for raw in r.stdout.splitlines():
        if raw.startswith("commit "):
            commit = raw.split()[1][:9]
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        line = _norm(raw[1:])
        if line in flat:
            hits.append({"where": "git history", "commit": commit,
                         "task": flat[line], "leaked": line[:160]})
    # one report per (commit, task, line) is enough
    seen, unique = set(), []
    for h in hits:
        k = (h["commit"], h["task"], h["leaked"])
        if k not in seen:
            seen.add(k)
            unique.append(h)
    return unique


def run(project: Path, solution: str = "app", student: str = "skeleton",
        check_history: bool = True) -> dict:
    sol, stu = project / solution, project / student
    if not sol.exists() or not stu.exists():
        return {"ok": False, "error": f"need both {solution}/ and {student}/",
                "leaks": []}
    inside, outside = answer_lines(sol)
    # unique to the answer, and substantial enough to matter
    answers = {task: {l for l in lines if l not in outside and _interesting(l)}
               for task, lines in inside.items()}
    answers = {t: l for t, l in answers.items() if l}

    leaks = scan_tree(stu, answers)
    history: list[dict] = []
    if check_history:
        root = project
        while root != root.parent and not (root / ".git").exists():
            root = root.parent
        if (root / ".git").exists():
            history = scan_git_history(root, stu, answers)

    return {
        "ok": not leaks and not history,
        "solution": solution,
        "student": student,
        "tasks_with_answers": len(answers),
        "answer_lines_watched": sum(len(v) for v in answers.values()),
        "leaks": leaks,
        "history_leaks": history,
        "rule": ("no line unique to a task's answer may appear anywhere in the "
                 "student tree, or in its git history"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--solution", default="app")
    ap.add_argument("--student", default="skeleton")
    ap.add_argument("--no-history", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    report = run(project, a.solution, a.student, not a.no_history)
    (project / "leak-scan.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("leaks", "history_leaks")}, indent=2))
    for h in report.get("leaks", [])[:20]:
        print(f"  LEAK {h['file']}:{h['line']}  ({h['task']})  {h['leaked'][:90]}")
    for h in report.get("history_leaks", [])[:20]:
        print(f"  LEAK in history {h['commit']}  ({h['task']})  {h['leaked'][:90]}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
