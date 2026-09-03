"""Guide linter - SCRIPT, step 11's checker (requirements_doc step 11).

The guide was the one AI output with no script behind it: the Pack Writer got
one pass and a person read it at Gate 3. It self-checked on habit-tracker, which
worked, and a self-check is not a checker.

What a script can decide:

* one guide file per session, and every session covered;
* every student task id and every requirement id referenced somewhere;
* each session states a time, and an overrun is disclosed rather than buried;
* every fenced code snippet matches a line that really exists in the solution or
  the student tree - the "never retype a snippet from memory" rule, which is how
  a guide drifts from the code it claims to teach.

  python -m pipeline.guide_linter <project-dir> [--guide pack] [--cap 40]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .cutter import walk_source
from .spec_linter import SESSION_MINUTES_CAP

FENCE = re.compile(r"^```(\w+)?\s*$")
CODE_LANGS = {"ts", "tsx", "js", "jsx", "json", "typescript", "javascript"}
RE_MINUTES = re.compile(r"\b(\d{1,3})\s*(?:min|minute|minutes)\b", re.IGNORECASE)
# Every pack states the plan's total on a `**Time:**` line and then discusses
# other durations around it - the cap, an honest total, a worse alternative, how
# long a step costs in class. Taking max() over the whole file read those as the
# plan: tip-split says "40 minutes as planned below. The honest total for the
# material is 45" and was scored 45, and pipeline-test-05's Guide Writer had to
# reword a sentence about a hypothetical to stop it being read as the plan.
RE_TIME_LINE = re.compile(r"^\s*\*\*Time:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def stated_minutes(text: str) -> tuple[int | None, bool]:
    """The session's planned total, and whether it came from the `**Time:**` line.

    The first duration on that line, because the line reads "the plan below runs
    to 47 minutes against a 40-minute cap" - the plan is the first number and the
    cap is the second. Falls back to the largest duration in the file when there
    is no Time line, which is the old behaviour and is reported as a warning so
    the guess is visible rather than silent.
    """
    m = RE_TIME_LINE.search(text)
    if m:
        on_line = RE_MINUTES.findall(m.group(1))
        if on_line:
            return int(on_line[0]), True
    anywhere = RE_MINUTES.findall(text)
    if anywhere:
        return max(int(x) for x in anywhere), False
    return None, False
# an elision the author marked on purpose
ELIDED = re.compile(r"\.\.\.|…|/\* *\.\.\. *\*/")
NOISE = re.compile(r"^[\s{}()\[\];,]*$")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def code_corpus(project: Path, trees=("app", "skeleton")) -> set[str]:
    out: set[str] = set()
    for t in trees:
        root = project / t
        if not root.exists():
            continue
        for p in walk_source(root, respect_gitignore=False):
            try:
                text = p.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for line in text.splitlines():
                n = _norm(line)
                if n:
                    out.add(n)
    return out


def snippets(md: str) -> list[tuple[int, str, list[str]]]:
    """(start line, language, lines) for each fenced block."""
    out, lang, buf, start = [], None, [], 0
    for i, line in enumerate(md.splitlines(), start=1):
        m = FENCE.match(line)
        if m and lang is None:
            lang, buf, start = (m.group(1) or "").lower(), [], i
            continue
        if m and lang is not None:
            out.append((start, lang, buf))
            lang = None
            continue
        if lang is not None:
            buf.append(line)
    return out


def lint(project: Path, guide: str = "pack", cap: float = SESSION_MINUTES_CAP) -> dict:
    gdir = project / guide
    errors: list[dict] = []
    warnings: list[dict] = []
    if not gdir.exists():
        return {"ok": False, "errors": [{"code": "G001", "where": guide,
                                         "message": f"{guide}/ does not exist"}],
                "warnings": [], "sessions": []}

    spec = json.loads((project / "spec.json").read_text())
    sessions = spec.get("sessions") or []
    task_ids = [c["id"] for s in sessions for c in s.get("cuts", [])]
    req_ids = [c["id"] for s in sessions for c in s.get("criteria", [])]

    files = {p.name: p.read_text() for p in sorted(gdir.glob("*.md"))}
    whole = "\n".join(files.values())

    # one file per session
    per_session: dict[int, str] = {}
    for name in files:
        m = re.search(r"session[-_ ]?(\d+)", name, re.IGNORECASE)
        if m:
            per_session[int(m.group(1))] = name
    for s in sessions:
        n = s.get("n")
        if n not in per_session:
            errors.append({"code": "G010", "where": guide,
                           "message": f"no guide file for session {n} - expected "
                                      f"something matching session-{n}"})

    # every id referenced
    for tid in task_ids:
        if tid not in whole:
            errors.append({"code": "G020", "where": guide,
                           "message": f"student task {tid} is never mentioned in the guide"})
    for rid in req_ids:
        if rid not in whole:
            warnings.append({"code": "G021", "where": guide,
                             "message": f"requirement {rid} is never mentioned in the guide"})

    # timings
    out_sessions = []
    for s in sessions:
        n = s.get("n")
        name = per_session.get(n)
        if not name:
            continue
        text = files[name]
        stated, from_time_line = stated_minutes(text)
        if stated is not None and not from_time_line:
            warnings.append({"code": "G033", "where": name,
                             "message": f"session {n} has no '**Time:**' line, so its "
                                        f"planned total was guessed as {stated} - the "
                                        f"largest duration mentioned anywhere in the "
                                        f"file. State the plan's total on a Time line"})
        if stated is None:
            errors.append({"code": "G030", "where": name,
                           "message": f"session {n} states no time - an instructor "
                                      f"cannot plan from it"})
        over = stated is not None and stated > cap
        disclosed = bool(re.search(r"does not fit|over the cap|overrun|trim",
                                   text, re.IGNORECASE))
        if over and not disclosed:
            errors.append({"code": "G031", "where": name,
                           "message": f"session {n} states {stated} minutes against a "
                                      f"{cap:g} minute cap and never says so - an "
                                      f"overrun must be disclosed with what to cut"})
        elif over:
            warnings.append({"code": "G032", "where": name,
                             "message": f"session {n} is {stated} minutes against the "
                                        f"{cap:g} cap, disclosed with trims"})
        out_sessions.append({"n": n, "file": name, "minutes": stated,
                             "over_cap": bool(over), "disclosed": disclosed})

    # snippets must exist in the code
    corpus = code_corpus(project)
    if corpus:
        for name, text in files.items():
            for start, lang, lines in snippets(text):
                if lang not in CODE_LANGS:
                    continue
                if any(ELIDED.search(l) for l in lines):
                    continue                      # marked as an extract
                for k, raw in enumerate(lines):
                    line = _norm(raw)
                    if not line or NOISE.match(line) or len(line) < 12:
                        continue
                    if line not in corpus:
                        errors.append({
                            "code": "G040", "where": f"{name}:{start + 1 + k}",
                            "message": f"snippet line is in no source file - retyped "
                                       f"from memory or drifted: {line[:90]!r}"})

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "counts": {"errors": len(errors), "warnings": len(warnings)},
            "files": sorted(files), "sessions": out_sessions}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--guide", default="pack")
    ap.add_argument("--cap", type=float, default=SESSION_MINUTES_CAP)
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    report = lint(project, a.guide, a.cap)
    (project / "guide-lint.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("ok", "counts", "files", "sessions")},
                     indent=2))
    for e in report["errors"][:25]:
        print(f"  ERR {e['code']} {e['where']}: {e['message'][:130]}")
    for w in report["warnings"][:10]:
        print(f"  WRN {w['code']} {w['where']}: {w['message'][:130]}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
