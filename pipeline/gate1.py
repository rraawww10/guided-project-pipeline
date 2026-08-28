"""Gate 1 stopping rule - SCRIPT, step 4's checker.

Round 1's problem was not that the Spec Breaker missed things. It is adversarial
and gets one pass, so it returned something blocking on all five passes it ever
made. "Reject until blocking == 0" provably never terminates, and the rule that
did terminate was invented mid-flight while holding the report:

    approve when every remaining finding sits in a column a downstream checker
    owns.

That rule was written into round-3/why.md and then applied by hand. This module
makes it the machine's rule instead, so the decision does not move to fit the
answer and does not have to be re-derived per project.

  python -m pipeline.gate1 <project-dir>

Reads ambiguity.md, writes gate1.json, exits 0 approve-eligible / 1 reject.
The person still reads the spec and can still reject. What they can no longer do
is approve over a finding that nothing downstream will catch.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .state import spec_hash

# Every downstream checker that can catch a defect after Gate 1, and the step it
# runs at. `nothing` is the column that matters: a finding there escapes to the
# shipped project, so it is the only kind that must be fixed before the code is
# written.
OWNERS = {
    "spec-linter": "step 2 - the linter re-runs on every revision",
    "return-safety": "step 8 - the cutter's static scan, no toolchain needed",
    "typecheck": "step 8 - tsc over the generated skeleton",
    "cutter": "step 8 - marker balance, placement and the skeleton check",
    "skeleton-check": "step 8 - the skeleton must fail exactly the cut criteria",
    "test-runner": "step 6 - the Builder/test-runner loop fixes this for free",
    "code-check": "step 6 - a named static check the spec declares in code_checks",
    "deploy-check": "step 10 - fresh copy, install, build, preview",
    "pack-writer": "step 9 - a person reads the guide at Gate 3",
    "nothing": "NO downstream checker sees this - it ships as written",
}
UNOWNED = "nothing"

RE_SECTION = re.compile(r"^##\s+(.+?)\s*$")
RE_FINDING = re.compile(r"^###\s+([A-Za-z]+\d+)\s*[-–—:]?\s*(.*)$")
RE_OWNER = re.compile(r"^\s*[-*]\s*\*\*Owner:\*\*\s*`?([a-z-]+)`?", re.IGNORECASE)

BLOCKING_HEADINGS = {"blocking"}
SOFT_HEADINGS = {"worth a look", "worth a look:", "non-blocking"}


def parse_findings(md: str) -> list[dict]:
    """Findings in document order, each with its section and declared owner."""
    findings: list[dict] = []
    section = ""
    current: dict | None = None
    for raw in md.splitlines():
        m_sec = RE_SECTION.match(raw)
        if m_sec:
            section = m_sec.group(1).strip().lower()
            continue
        m_f = RE_FINDING.match(raw)
        if m_f:
            current = {"id": m_f.group(1), "title": m_f.group(2).strip(),
                       "section": section, "owner": None}
            findings.append(current)
            continue
        if current is not None:
            m_o = RE_OWNER.match(raw)
            if m_o:
                current["owner"] = m_o.group(1).strip().lower()
    return findings


def classify(findings: list[dict]) -> list[dict]:
    out = []
    for f in findings:
        blocking = f["section"] in BLOCKING_HEADINGS
        owner = f["owner"]
        # Fail closed. An owner that is missing, or not one of the known
        # checkers, is treated as unowned - the Breaker must say who catches it.
        valid = owner in OWNERS
        effective = owner if valid else UNOWNED
        out.append({
            **f,
            "blocking": blocking,
            "owner_declared": owner,
            "owner": effective,
            "owner_valid": valid,
            "caught_by": OWNERS[effective],
            "must_fix_now": blocking and effective == UNOWNED,
        })
    return out


def check(project: Path) -> dict:
    amb = project / "ambiguity.md"
    meta_path = project / ".pipeline" / "ambiguity-meta.json"
    current = spec_hash(project)

    report: dict = {
        "ok": False,
        "verdict": "reject",
        "spec_hash": current,
        "findings": [],
        "counts": {"blocking": 0, "worth_a_look": 0, "unowned_blocking": 0},
        "reasons": [],
        "rule": ("reject when any blocking finding is owned by 'nothing'; approve "
                 "when every remaining finding sits in a column a downstream "
                 "checker owns"),
    }

    if not amb.exists():
        report["reasons"].append("ambiguity.md is missing - the Spec Breaker has not run")
        return report

    # B-04: a report on disk is not evidence it reviewed the spec on disk.
    # recipe-box had round 2's report copied back over a round-3 spec and the
    # gate reader spent a pass on findings that were already fixed.
    if not meta_path.exists():
        report["reasons"].append(
            "ambiguity.md has no .pipeline/ambiguity-meta.json, so nothing ties it to "
            "the spec it reviewed. Re-run the Spec Breaker between "
            "`pipeline breaker <slug> begin` and `pipeline breaker <slug> end`.")
        return report
    meta = json.loads(meta_path.read_text())
    report["reviewed_spec_hash"] = meta.get("spec_hash")
    if meta.get("spec_hash") != current:
        report["reasons"].append(
            f"ambiguity.md reviewed spec {str(meta.get('spec_hash'))[:12]} but the spec on "
            f"disk is {str(current)[:12]}. The report is stale - the spec changed after it "
            f"was written. Re-run the Spec Breaker.")
        return report

    findings = classify(parse_findings(amb.read_text()))
    report["findings"] = findings
    blocking = [f for f in findings if f["blocking"]]
    unowned = [f for f in blocking if f["must_fix_now"]]
    report["counts"] = {
        "blocking": len(blocking),
        "worth_a_look": len(findings) - len(blocking),
        "unowned_blocking": len(unowned),
    }
    missing_owner = [f["id"] for f in findings if not f["owner_valid"]]
    if missing_owner:
        report["reasons"].append(
            f"findings with no valid **Owner:** line: {', '.join(missing_owner)}. "
            f"Valid owners: {', '.join(sorted(OWNERS))}. Treated as 'nothing'.")

    if unowned:
        report["reasons"] += [
            f"{f['id']} ({f['title'][:70]}) is blocking and nothing downstream catches it"
            for f in unowned]
        return report

    report["ok"] = True
    report["verdict"] = "approve-eligible"
    report["reasons"].append(
        f"{len(blocking)} blocking finding(s), all owned by a downstream checker; "
        f"{report['counts']['worth_a_look']} worth a look. Nothing here escapes to the "
        f"shipped project.")
    return report


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m pipeline.gate1 <project-dir>", file=sys.stderr)
        return 2
    project = Path(argv[1]).resolve()
    report = check(project)
    (project / "gate1.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
