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

import hashlib
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
    # The vocabulary had no name for mutation.py, so the one class it exists to
    # catch had nowhere to be parked. pipeline-test-04 round 3 rejected on
    # "cut-pending-frame can be left empty with every criterion green" - which is
    # mutation.py's docstring almost word for word ("a task no requirement
    # notices is a task that grades nothing - the bypassable-cut defect") - and
    # the Breaker had to write `nothing` because `mutation` was not on the list.
    # A missing word cost a round.
    "mutation": "step 8 - leave-one-out: each task alone removed must turn one "
                "of its own criteria red",
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
    # Opt-in and narrowable (`--only`, `--max`), so it costs one boot and build
    # per task and a run can legitimately cover a subset. A finding parked here
    # approves, but somebody has to confirm the mutant for THIS task was among
    # the ones actually run.
    "mutation": ("mutation.json", "checked",
                 "step 8 must show checked == of_total, and the task this finding "
                 "names must be among the mutants run - mutation is opt-in and "
                 "--only/--max narrow it, so ok:true over a subset proves nothing "
                 "about a task that was skipped"),
}

RE_SECTION = re.compile(r"^##\s+(.+?)\s*$")
RE_FINDING = re.compile(r"^###\s+([A-Za-z]+\d+)\s*[-–—:]?\s*(.*)$")
RE_OWNER = re.compile(r"^\s*[-*]\s*\*\*Owner:\*\*\s*`?([a-z-]+)`?", re.IGNORECASE)
# The spec line a finding is about. Captured so a re-raise of the SAME line in a
# later round can be recognised - see drift_against_prior_round below.
RE_LINE = re.compile(r"^\s*[-*]\s*\*\*The line:\*\*\s*(.+?)\s*$", re.IGNORECASE)
# Where the finding lives. The most reliable id-bearing field of the three, and
# the one that made cut-pending-frame's owner drift visible across two rounds.
RE_WHERE = re.compile(r"^\s*[-*]\s*\*\*Where:\*\*\s*(.+?)\s*$", re.IGNORECASE)

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
                       "section": section, "owner": None, "line": None, "where": None}
            findings.append(current)
            continue
        if current is not None:
            m_o = RE_OWNER.match(raw)
            if m_o:
                current["owner"] = m_o.group(1).strip().lower()
            m_l = RE_LINE.match(raw)
            if m_l and current.get("line") is None:
                current["line"] = m_l.group(1).strip()
            m_w = RE_WHERE.match(raw)
            if m_w and current.get("where") is None:
                current["where"] = m_w.group(1).strip()
    return findings


def line_key(line: str | None) -> str | None:
    """An exact key for a verbatim re-quote of the same spec line."""
    if not line:
        return None
    text = " ".join(line.split()).strip().strip("\"'`").strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# The id vocabulary the spec linter already enforces: criteria, cuts, endpoints
# and screens. A finding's *subject* is the set of those it talks about, and
# unlike its own id (which renumbers) or its quoted line (which the Breaker
# re-words freely between rounds) that set is stable.
RE_SPEC_ID = re.compile(r"\b(?:c-\d+-\d+|S\d{2}-AC\d{2}|cut-[a-z0-9-]+|ep-[a-z0-9-]+|sc-[a-z0-9-]+)\b")


def subject_key(finding: dict) -> tuple[str, ...]:
    """The spec objects a finding is about, from its title and its quoted line.

    Matched as a set and not by intersection: two different findings about the
    same criterion must not be reported as one changing its mind.
    """
    text = " ".join(str(finding.get(k) or "")
                    for k in ("title", "where", "line"))
    return tuple(sorted(set(RE_SPEC_ID.findall(text))))


def drift_against_prior_round(project: Path, findings: list[dict]) -> list[dict]:
    """Findings that quote a line an earlier round already judged, judged differently.

    The Gate 1 stopping rule reads exactly two fields - `blocking` and `owner` -
    and the Spec Breaker writes both, with no memory of what it wrote last time.
    On pipeline-test-04 the same unchanged criterion moved from "worth a look /
    test-runner" to "blocking / test-runner" between rounds, and two more
    findings moved their owner to `nothing`, which is what the rule rejects on.
    Nothing noticed, because ids renumber and nothing compared the rounds.

    This does NOT change the verdict. An escalation can be right - the point is
    that a person reading the gate should be told the line did not change and
    the judgement did, instead of having to diff two archived reports by hand.
    """
    rounds = sorted(
        (d for d in (project / ".pipeline").glob("round-*") if (d / "gate1.json").is_file()),
        key=lambda d: int(m.group(1)) if (m := re.search(r"(\d+)$", d.name)) else -1,
    )
    if not rounds:
        return []
    prior_dir = rounds[-1]
    try:
        prior = json.loads((prior_dir / "gate1.json").read_text())
    except (OSError, json.JSONDecodeError):
        return []

    by_subject: dict[tuple[str, ...], dict] = {}
    by_line: dict[str, dict] = {}
    for f in prior.get("findings", []):
        subj = tuple(f.get("subject") or subject_key(f))
        if subj and subj not in by_subject:
            by_subject[subj] = f
        key = f.get("line_key") or line_key(f.get("line"))
        if key and key not in by_line:
            by_line[key] = f

    drift = []
    for f in findings:
        subj = tuple(f.get("subject") or ())
        was = by_subject.get(subj) if subj else None
        if was is None:
            was = by_line.get(f.get("line_key") or "")
        if not was:
            continue
        harsher = f["blocking"] and not was.get("blocking")
        unowned_now = f["owner"] == UNOWNED and was.get("owner") not in (None, UNOWNED)
        if not (harsher or unowned_now):
            continue
        moves = []
        if harsher:
            moves.append(f"{was.get('section') or 'worth a look'} -> blocking")
        if unowned_now:
            moves.append(f"owner {was.get('owner')} -> {UNOWNED}")
        drift.append({
            "id": f["id"],
            "prior_id": was.get("id"),
            "prior_round": prior_dir.name,
            "line": f.get("line"),
            "moved": moves,
            "note": (f"{prior_dir.name} judged this same line as "
                     f"{was.get('section') or '?'} / owner {was.get('owner')}. The line "
                     f"itself is unchanged, so either the earlier round was wrong or this "
                     f"one is - the Breaker re-reads the spec with no memory of its own "
                     f"previous verdict, and the rule reads only these two fields."),
        })
    return drift


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
            "line_key": line_key(f.get("line")),
            "subject": list(subject_key(f)),
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

    # Informational, never a verdict change: the same spec line judged more
    # harshly than the round before. See drift_against_prior_round.
    report["drift"] = drift_against_prior_round(project, findings)
    for d in report["drift"]:
        report["reasons"].append(
            f"{d['id']} (was {d['prior_round']} {d['prior_id']}): {'; '.join(d['moved'])} "
            f"on an unchanged line")

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
