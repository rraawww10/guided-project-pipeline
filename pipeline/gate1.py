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

# Rule 8 asks whether a downstream checker OWNS a finding. It cannot ask whether
# that checker will actually RUN, and two owners can pass by not running:
#
#   typecheck    tsc over the generated skeleton, and the second-line check.
#                skeleton-check.json carries `typecheck_fail_open`, which is true
#                when the toolchain could not be reached. A fail-open check that
#                does not run reports no error, so a blocking finding parked
#                there can reach the student skeleton with every gate green.
#                pipeline-test-03's B2 - a TS2367 dead comparison once
#                cut-parse-line is removed - was owned by exactly this, and the
#                only reason it was caught is that a human was told to read the
#                flag at step 10 and did. It read false. Nothing enforced that.
#
#   code-check   step 6, but ONLY for the named checks spec.json declares in
#                `code_checks`. With that list empty the checker runs nothing at
#                all, so the column is `nothing` wearing a checker's name. This
#                one is decidable here, from the spec, so it is decided rather
#                than deferred.
#
# Neither is downgraded to `nothing` outright. typecheck usually does run, and
# rejecting a spec over a check that will probably work is a worse trade than
# recording the obligation. What changes is that the obligation stops depending
# on a person remembering to write it in a gate note.
FAIL_OPEN = {
    "typecheck": ("skeleton-check.json", "typecheck_fail_open",
                  "step 10 must read typecheck_fail_open and require it false - "
                  "a fail-open check that did not run passes without looking"),
}

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


def classify(findings: list[dict], code_checks: list | None = None) -> list[dict]:
    out = []
    declared = list(code_checks or [])
    for f in findings:
        blocking = f["section"] in BLOCKING_HEADINGS
        owner = f["owner"]
        # Fail closed. An owner that is missing, or not one of the known
        # checkers, is treated as unowned - the Breaker must say who catches it.
        valid = owner in OWNERS
        effective = owner if valid else UNOWNED
        why_unowned = None
        # `code-check` owns nothing unless the spec declares something for it to
        # run. Decidable from spec.json, so decide it instead of deferring.
        if effective == "code-check" and not declared:
            effective, why_unowned = UNOWNED, (
                "declared owner 'code-check', but spec.json declares no "
                "code_checks, so that checker runs nothing at all")
        out.append({
            **f,
            "blocking": blocking,
            "owner_declared": owner,
            "owner": effective,
            "owner_valid": valid,
            "owner_downgraded": why_unowned,
            "fail_open": effective in FAIL_OPEN,
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
                 "checker owns. An owner that can pass by not running is owned "
                 "only conditionally: it approves, and the confirmation it "
                 "actually ran is listed in verify_later"),
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

    code_checks = []
    try:
        code_checks = json.loads(
            (project / "spec.json").read_text()).get("code_checks") or []
    except (OSError, json.JSONDecodeError):
        pass
    findings = classify(parse_findings(amb.read_text()), code_checks)
    report["findings"] = findings
    blocking = [f for f in findings if f["blocking"]]
    unowned = [f for f in blocking if f["must_fix_now"]]
    report["counts"] = {
        "blocking": len(blocking),
        "worth_a_look": len(findings) - len(blocking),
        "unowned_blocking": len(unowned),
    }
    downgraded = [f for f in findings if f.get("owner_downgraded")]
    for f in downgraded:
        report["reasons"].append(f"{f['id']}: {f['owner_downgraded']}")

    # A blocking finding parked on a fail-open owner is approve-eligible, but
    # the obligation to confirm the check actually ran is recorded here rather
    # than left to whoever writes the gate note. pipeline-test-03 got this right
    # only because a human was told to read the flag by hand.
    report["verify_later"] = [
        {"id": f["id"], "title": f["title"][:70], "owner": f["owner"],
         "report": FAIL_OPEN[f["owner"]][0], "flag": FAIL_OPEN[f["owner"]][1],
         "requirement": FAIL_OPEN[f["owner"]][2]}
        for f in findings if f["blocking"] and f.get("fail_open")]
    for v in report["verify_later"]:
        report["reasons"].append(
            f"{v['id']} is blocking and owned by '{v['owner']}', which can pass by "
            f"not running - {v['requirement']}")

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
    n_fo = len(report["verify_later"])
    report["reasons"].append(
        f"{len(blocking)} blocking finding(s), all owned by a downstream checker; "
        f"{report['counts']['worth_a_look']} worth a look. Nothing here escapes to the "
        f"shipped project"
        + (f", PROVIDED the {n_fo} finding(s) in verify_later are confirmed to have "
           f"actually been checked - see each one's report and flag."
           if n_fo else "."))
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
