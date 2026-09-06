"""Named static code checks - SCRIPT, part of step 6's checker.

Some constraints are load-bearing for the curriculum and invisible to the test
suite. habit-tracker's Gate 1 round 3 found one: "date arithmetic must give the
same answer in every timezone" was called make-or-break in the idea, and nothing
could assert it, because the Verifier cannot change the server's `TZ`. The Spec
Breaker's suggestion was that a person read `lib/week.ts` at Gate 3.

A person reading code at Gate 3 is the thing this pipeline exists to avoid, and
the rule is perfectly checkable statically: the defect is a local-time `Date`
accessor where a UTC one was meant. So it is a check.

Checks are NAMED and OPT-IN. A spec declares the ones that apply to it:

    "code_checks": ["utc-dates"]

They run at step 6 against `app/`, so a failure lands in the
Builder/test-runner loop and is fixed for free - which moves a finding out of
the "nothing catches it" column that Gate 1 rejects on.

This is deliberately a registry of specific named rules, not a
patterns-from-the-spec engine. A spec that could ask for any regex would be a
spec that could ask for nonsense.

  python -m pipeline.code_check <project-dir> [--target app|skeleton]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".turbo",
             "coverage", "__pycache__", ".venv", ".pipeline", "verify"}

# Local-time Date members, each of which has a UTC counterpart. Reading any of
# them turns a YYYY-MM-DD string into a different weekday depending on where the
# machine is: `new Date("2026-08-26").getDay()` is Wednesday in IST and Tuesday
# west of Greenwich.
LOCAL_TIME_MEMBERS = (
    "getDate", "getDay", "getFullYear", "getMonth", "getHours", "getMinutes",
    "getSeconds", "getMilliseconds",
    "setDate", "setFullYear", "setMonth", "setHours", "setMinutes",
    "setSeconds", "setMilliseconds",
    "toLocaleDateString", "toLocaleTimeString", "toLocaleString",
    "getTimezoneOffset",
)
RE_LOCAL_TIME = re.compile(r"\.(" + "|".join(LOCAL_TIME_MEMBERS) + r")\s*\(")
# The clock itself. A guided project with a fixed tracked day must not read it.
RE_CLOCK = re.compile(r"\bnew\s+Date\s*\(\s*\)|\bDate\s*\.\s*now\s*\(\s*\)")


def _strip_noise(line: str) -> str:
    """Comments and string bodies do not count as code."""
    line = re.sub(r"//.*$", "", line)
    return re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`", '""', line)


def _sources(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_dir() or p.suffix not in CODE_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def check_utc_dates(root: Path) -> list[dict]:
    """Every date calculation must give the same answer in every timezone."""
    out: list[dict] = []
    for path in _sources(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, raw in enumerate(text.splitlines(), start=1):
            line = _strip_noise(raw)
            for m in RE_LOCAL_TIME.finditer(line):
                member = m.group(1)
                utc = member.replace("get", "getUTC", 1).replace("set", "setUTC", 1) \
                    if member[:3] in ("get", "set") else None
                out.append({
                    "file": str(path.relative_to(root)), "line": n,
                    "found": f".{member}()",
                    "why": (f"local-time accessor - the answer changes with the "
                            f"machine's timezone"),
                    "fix": (f"use .{utc}() instead" if utc else
                            "format from the UTC parts, or do the arithmetic on the "
                            "YYYY-MM-DD string directly"),
                    "source": raw.strip()[:120],
                })
            for m in RE_CLOCK.finditer(line):
                out.append({
                    "file": str(path.relative_to(root)), "line": n,
                    "found": m.group(0).strip(),
                    "why": "reads the real clock, so the same input stops giving the "
                           "same answer",
                    "fix": "derive every date from the seed's tracked day",
                    "source": raw.strip()[:120],
                })
    return out


CHECKS = {
    "utc-dates": (
        check_utc_dates,
        "date arithmetic gives the same answer in every timezone: no local-time "
        "Date accessors, and no reading the real clock",
    ),
}


def run(project: Path, target: str = "app") -> dict:
    """Run every check the spec declares. A spec that declares none passes."""
    try:
        spec = json.loads((project / "spec.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": f"cannot read spec.json: {e}", "checks": {}}

    declared = spec.get("code_checks") or []
    unknown = [c for c in declared if c not in CHECKS]
    root = project / target
    results: dict[str, dict] = {}
    for name in declared:
        if name not in CHECKS:
            continue
        fn, why = CHECKS[name]
        findings = fn(root) if root.exists() else []
        results[name] = {"ok": not findings, "rule": why,
                         "violations": findings[:40], "count": len(findings)}
    return {
        "ok": not unknown and all(r["ok"] for r in results.values()),
        "target": target,
        "declared": declared,
        "unknown": unknown,
        "checks": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--target", default="app", choices=["app", "skeleton"])
    a = ap.parse_args(argv)
    report = run(Path(a.project).resolve(), a.target)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
