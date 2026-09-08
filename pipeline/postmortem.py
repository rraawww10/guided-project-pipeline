"""Postmortem - SCRIPT. What went wrong in a run, and which of it had no owner.

Rule 1 says every agent has a checker. It does not say every *defect class* has
one, and that is where the pipeline stops being self-correcting: when a checker
goes red and the component it routes to cannot reach the fault, the loop cannot
converge. The retry cap stops it, but stops it as "this project is stuck" rather
than "this class has no checker", so the finding lives in whoever was watching.

This counts instead. For every red checker it reports how many times it went red
before it went green, and flags the ones that never converged - those are the
classes worth promoting to a checker of their own, and the ones that cost the
most while nobody was counting.

Rule 5 keeps this a report. It proposes nothing and edits nothing: a person
reads it and decides, which is the same standing rule that keeps an agent out of
`pipeline/`. The bar for acting on it is already written down in
learning/lessons.md under "Which findings can become linter rules" - promote a
class once it recurs, and test the candidate against the round that contained
the defect before writing it.

  python -m pipeline.postmortem <slug>      one project
  python -m pipeline.postmortem --all       every project on disk
  python -m pipeline.postmortem --all --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ui_core import PROJECTS

# Which component the orchestrator sends a red report to. Imported rather than
# restated so this cannot drift from the routing it is describing.
from .ui_core import FAILED_REPORT_REPAIRS as _REPAIRS

# state.json's step names are the checker's name, not its report file. This is
# the join between the two, so a red step can be attributed to the component the
# orchestrator would route it to.
STEP_TO_REPORT = {
    "ideas": "ideas.json", "lint": "lint.json", "gate1-check": "gate1.json",
    "breaker": "gate1.json", "redfirst": "redfirst.json",
    "test": "results.json", "test:app": "results.json",
    "test:skeleton": "skeleton-check.json", "mutation": "mutation.json",
    "cut": "skeleton-check.json", "leak-scan": "leak-scan.json",
    "leak": "leak-scan.json", "guide-lint": "guide-lint.json",
    "deploy": "deploy.json",
}


def owner_of(step: str) -> str:
    report = STEP_TO_REPORT.get(step, "")
    meta = _REPAIRS.get(report)
    return f"{meta['kind']}:{meta['component']}" if meta else "-"


def runs_of(project: Path) -> list[dict]:
    """The step ledger. Present for every project, including pre-UI ones."""
    p = project / ".pipeline" / "state.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("steps") or []
    except Exception:
        return []


def analyse(project: Path) -> dict:
    """Group the ledger by step, and find the reds that never went green."""
    steps = runs_of(project)
    by_step: dict[str, list[dict]] = {}
    for s in steps:
        by_step.setdefault(str(s.get("step") or "?"), []).append(s)

    episodes = []
    for step, entries in sorted(by_step.items()):
        reds = [e for e in entries if not e.get("ok")]
        if not reds:
            continue
        # Converged if anything green for this step came after the last red.
        last_red = max(str(e.get("at") or "") for e in reds)
        greens_after = [e for e in entries
                        if e.get("ok") and str(e.get("at") or "") > last_red]
        episodes.append({
            "step": step,
            "red": len(reds),
            "total": len(entries),
            "owner": owner_of(step),
            "converged": bool(greens_after),
            "last_red_at": last_red,
            "detail": str(reds[-1].get("detail") or "")[:120],
        })

    state = {}
    p = project / ".pipeline" / "state.json"
    if p.exists():
        try:
            state = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    return {
        "slug": project.name,
        "flow": state.get("flow"),
        "phase": state.get("phase"),
        "retries": {k: v for k, v in (state.get("retries") or {}).items() if v},
        "ticket": state.get("ticket"),
        "episodes": episodes,
        # The whole point of the report: red, repeatedly, and never green.
        "unconverged": [e for e in episodes if not e["converged"]],
        "churn": [e for e in episodes if e["red"] >= 3],
    }


def render(rep: dict) -> str:
    out = [f"{rep['slug']}  flow={rep['flow']} phase={rep['phase']}"
           + (f"  retries={rep['retries']}" if rep["retries"] else "")
           + ("  TICKET" if rep.get("ticket") else "")]
    if not rep["episodes"]:
        out.append("  no red checker on record")
        return "\n".join(out)
    out.append(f"  {'step':16}{'red':>4}{'runs':>6}  {'owner':22}converged")
    for e in rep["episodes"]:
        out.append(f"  {e['step']:16}{e['red']:>4}{e['total']:>6}  {e['owner']:22}"
                   + ("yes" if e["converged"] else "NO"))
    for e in rep["unconverged"]:
        out.append(f"  ! {e['step']} never went green after {e['red']} red - "
                   f"routed to {e['owner']}. {e['detail']}")
    for e in rep["churn"]:
        if e["converged"]:
            out.append(f"  ~ {e['step']} went red {e['red']} times before it "
                       f"converged - routed to {e['owner']}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pipeline.postmortem")
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    root = Path(PROJECTS)
    if a.all:
        projects = sorted(d for d in root.iterdir() if (d / ".pipeline").is_dir())
    elif a.slug:
        projects = [root / a.slug]
    else:
        ap.error("give a slug or --all")

    reports = [analyse(p) for p in projects]
    if a.json:
        print(json.dumps(reports, indent=2))
        return 0

    for rep in reports:
        print(render(rep))
        print()

    # The cross-project count is the thing a single run cannot show, and the
    # thing lessons.md's promotion bar is written in terms of.
    tally: dict[tuple[str, str], int] = {}
    for rep in reports:
        for e in rep["unconverged"]:
            tally[(e["step"], e["owner"])] = tally.get((e["step"], e["owner"]), 0) + 1
    if tally:
        print("classes that never converged, across every project:")
        for (step, owner), n in sorted(tally.items(), key=lambda kv: -kv[1]):
            flag = "  <- recurs, promotion candidate" if n >= 2 else ""
            print(f"  {step:16} routed to {owner:22} {n} project(s){flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
