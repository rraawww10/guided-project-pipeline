"""Spec linter - SCRIPT, step 2's checker.

A rule check must give the same answer every time, so there is no agent in here.
Reads spec.json and spec.md, writes lint.json, exits 0 clean / 1 dirty.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .code_check import CHECKS as CODE_CHECKS
from .state import spec_hash

# Words that let a spec line mean two things. The Spec Breaker catches subtler
# cases by reading; these are the ones a regex can own outright.
VAGUE = [
    "etc", "and so on", "and more", "appropriate", "as needed", "as required",
    "user-friendly", "user friendly", "properly", "correctly handle", "some",
    "various", "several", "a few", "if necessary", "where relevant", "nice to have",
    "robust", "seamless", "intuitive", "clean ui", "good ux", "handle errors",
    "and similar", "or something", "flexible", "scalable",
]
# Case-sensitive: an uppercase marker is a placeholder, the lowercase word may be
# domain vocabulary. "one row per todo" is a real criterion; "TODO" is not.
MARKERS = ["TODO", "TBD", "FIXME", "XXX", "T.B.D"]
# Case-insensitive: these are never anything but a placeholder.
PLACEHOLDER = ["???", "lorem ipsum", "<insert", "<fill in", "coming soon"]

# A criterion is testable if it names a real thing a script can look at.
TESTABLE_VERBS = [
    "returns", "responds", "renders", "displays", "shows", "hides", "redirects",
    "persists", "stores", "removes", "disables", "enables", "navigates",
    "contains", "rejects", "accepts", "sorts", "filters", "updates", "clears",
]

METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
TRACKS = {"react", "node", "fullstack", "ai"}

RE_EP = re.compile(r"^ep-[a-z0-9]+(-[a-z0-9]+)*$")
RE_SC = re.compile(r"^sc-[a-z0-9]+(-[a-z0-9]+)*$")
# Two id vocabularies, both accepted. `cut-<kebab>` is what the shipped projects
# use; `S03-T01` is requirements_doc.md's student-task id.
RE_CUT = re.compile(r"^(?:cut-[a-z0-9]+(-[a-z0-9]+)*|S\d{1,3}-T\d{1,3})$")
RE_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# A hint is the whole text the student gets. It must point at something
# concrete: a symbol, a path, a method, a status code, a number. recipe-box
# round 3 B1 - "cut-recipe-scale-quantity does not name scaleQuantity" - made
# a second cut bypassable with every criterion green.
RE_ANCHOR = re.compile(
    r"`[^`]+`"                                  # `scaleQuantity`
    r"|\b[a-z]+[A-Z][A-Za-z0-9]*\b"             # camelCase
    r"|\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b"     # PascalCase
    r"|\b[a-z_]+_[a-z_0-9]+\b"                  # snake_case
    r"|\b[A-Za-z_][A-Za-z0-9_]*\(\)"            # someCall()
    r"|/[a-z][\w/\[\]-]*"                       # /api/recipes
    r"|\b(?:GET|POST|PUT|PATCH|DELETE)\b"       # a method
    r"|\d"                                      # a status code or a count
)

# A hint phrased as "return X" tells the Builder to put the return inside the
# markers. That is the TS2355 shape: the skeleton then has a typed function
# with no return and does not compile at all - no red test, no build. The
# authoritative check is static, in the cutter, because no code exists yet at
# step 2. This is the cheap wording warning that comes first.
RE_HINT_RETURN = re.compile(r"^\s*(?:and\s+)?returns?\b|\breturn\s+(?:the|a|an|every|it|its)\b",
                            re.IGNORECASE)

# 40 minutes of live teaching. These caps are the session-fit heuristic that
# Gate 1 would otherwise have to eyeball.
MIN_CRITERIA, MAX_CRITERIA = 2, 6
MAX_CUTS = 5

# --- session minutes -------------------------------------------------------
# Round 1 shipped two sessions over the 40 minute cap, and both were found at
# step 9 by the Pack Writer - after the spec, the code, the tests and the
# skeleton were all built and both gates were passed. Nothing before step 9
# weighed teaching minutes, so the caps above counted cuts and criteria and
# missed the setup cost entirely.
#
# Calibrated against the two measured overruns:
#   tip-split  session 1: setup + 4 cuts + 2 builds + 6 concepts -> 45 min
#   recipe-box session 3:         4 cuts + 2 builds + 5 concepts -> 45 min
# and against the sessions that fitted (tip-split 3, recipe-box 1 and 4).
# The estimate is always reported. Over the cap is a warning, because a
# 43-minute estimate is a judgement call for the person at Gate 1. Over the
# hard ceiling is an error, because no live session absorbs that.
BASE_MINUTES = 10.0          # intro, recap, wrap-up
MINUTES_PER_CUT = 6.0        # live-coding one cut point with explanation
MINUTES_PER_BUILD = 3.0      # scaffolding a new endpoint or screen
MINUTES_PER_CONCEPT = 1.5    # one entry in `teaches`
SETUP_MINUTES = 6.0          # project setup, on the session that carries it
SESSION_MINUTES_CAP = 40.0
SESSION_MINUTES_HARD = 50.0

REQUIRED_MD_HEADINGS = ["## Outcome", "## Out of scope", "## Sessions"]


class Lint:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def err(self, code: str, where: str, message: str) -> None:
        self.errors.append({"code": code, "where": where, "message": message})

    def warn(self, code: str, where: str, message: str) -> None:
        self.warnings.append({"code": code, "where": where, "message": message})


def _rx(phrase: str) -> re.Pattern:
    """Word-boundary match, so 'some' does not fire inside 'handsome'."""
    body = re.escape(phrase)
    left = r"\b" if phrase[:1].isalnum() else ""
    right = r"\b" if phrase[-1:].isalnum() else ""
    return re.compile(left + body + right)


_VAGUE_RX = [(p, _rx(p)) for p in VAGUE]
_MARKER_RX = [(p, _rx(p)) for p in MARKERS]
_PLACEHOLDER_RX = [(p, _rx(p)) for p in PLACEHOLDER]


def _scan_vague(lint: Lint, text: str, where: str, code: str) -> None:
    low = text.lower()
    for phrase, rx in _VAGUE_RX:
        if rx.search(low):
            lint.err(code, where, f"vague wording: {phrase!r} in {text!r}")


def _scan_placeholder(lint: Lint, text: str, where: str, code: str) -> None:
    for phrase, rx in _MARKER_RX:              # case-sensitive
        if rx.search(text):
            lint.err(code, where, f"placeholder: {phrase!r} in {text[:120]!r}")
    low = text.lower()
    for phrase, rx in _PLACEHOLDER_RX:         # case-insensitive
        if rx.search(low):
            lint.err(code, where, f"placeholder: {phrase!r} in {text[:120]!r}")


def _check_grading_independence(lint: Lint, cut_signature: dict[str, set[str]]) -> None:
    """Two cuts graded by exactly the same criteria cannot be told apart.

    This is the one rule that catches both of round 1's worst cut defects, and
    it caught both of them when it was written:

    * recipe-box round 3 B1 - cut-fraction-scale and cut-recipe-scale-quantity
      appear in c-4-2, c-4-3 and c-4-4 and nowhere else, so a student who does
      the scaling in one of them leaves the other empty with every criterion
      green. A bypassable grading cut, invisible to every downstream checker.
    * the skeleton-check blind spot - cut-store-find-one and cut-api-recipe-get
      have the same signature, which is exactly why c-3-2 goes green with
      find-one still empty. The cutter can only prove the all-open and no-cut
      cases, so a pair like this is where a proper subset satisfies the test.

    The fix in both cases is one criterion that depends on one cut and not the
    other, which makes the pair independently gradable and removes the subset
    case at the same time.
    """
    groups: dict[frozenset, list[str]] = {}
    for cut, crits in cut_signature.items():
        groups.setdefault(frozenset(crits), []).append(cut)
    for crits, cuts in sorted(groups.items(), key=lambda kv: sorted(kv[1])):
        if len(cuts) < 2:
            continue
        lint.err("E110", f"cuts {', '.join(sorted(cuts))}",
                 f"these {len(cuts)} cuts are graded by exactly the same criteria "
                 f"({', '.join(sorted(crits))}), so no test can tell them apart. One "
                 f"can be left empty with every criterion green, and a proper subset "
                 f"of them satisfies the test - which is the one case the skeleton "
                 f"check cannot see. Add a criterion that depends on one of them and "
                 f"not the other.")


def _setup_session(sessions: list[dict]) -> int | None:
    """Which session carries the project setup. Session 1 unless one says so."""
    for s in sessions:
        if s.get("setup") is True:
            return s.get("n")
    return sessions[0].get("n") if sessions else None


def session_minutes(s: dict, carries_setup: bool) -> float:
    return round(
        BASE_MINUTES
        + MINUTES_PER_CUT * len(s.get("cuts") or [])
        + MINUTES_PER_BUILD * len(s.get("builds") or [])
        + MINUTES_PER_CONCEPT * len(s.get("teaches") or [])
        + (SETUP_MINUTES if carries_setup else 0.0), 1)


def _check_session_load(lint: Lint, sessions: list[dict]) -> None:
    """Weigh setup cost and teaching minutes, not just counts.

    Round 1 found both overruns at step 9, where the only real fix is a Gate 1
    rebalance that invalidates the spec, the code, the tests and the skeleton.
    Both projects shipped the defect instead of paying that. This moves the
    finding to step 2, where the fix is one Spec Writer pass.
    """
    if not sessions:
        return
    setup_n = _setup_session(sessions)
    for s in sessions:
        n = s.get("n")
        w = f"session {n}"
        mins = session_minutes(s, n == setup_n)
        if mins > SESSION_MINUTES_HARD:
            lint.err("E111", w,
                     f"estimated {mins:g} teaching minutes against a "
                     f"{SESSION_MINUTES_CAP:g} minute cap - over the "
                     f"{SESSION_MINUTES_HARD:g} minute ceiling no live session absorbs. "
                     f"{len(s.get('cuts') or [])} cuts, {len(s.get('builds') or [])} builds, "
                     f"{len(s.get('teaches') or [])} concepts"
                     + (" plus the project setup" if n == setup_n else "")
                     + ". Move a cut or a build to another session.")
        elif mins > SESSION_MINUTES_CAP:
            lint.warn("W112", w,
                      f"estimated {mins:g} teaching minutes against a "
                      f"{SESSION_MINUTES_CAP:g} minute cap. Nothing before step 9 "
                      f"measures this, so decide it here: "
                      f"{len(s.get('cuts') or [])} cuts, {len(s.get('builds') or [])} builds, "
                      f"{len(s.get('teaches') or [])} concepts"
                      + (" plus the project setup" if n == setup_n else "") + ".")

    # The explicit lesson from tip-split: the session holding the setup must
    # carry fewer cuts than the others, not the same number. tip-split session 1
    # carried 4 cuts plus all the setup while session 2 also carried 4, and ran
    # 45 minutes against the cap.
    if setup_n is not None and len(sessions) > 1:
        setup_s = next((s for s in sessions if s.get("n") == setup_n), None)
        others = [s for s in sessions if s.get("n") != setup_n]
        if setup_s is not None and others:
            mine = len(setup_s.get("cuts") or [])
            most = max(len(s.get("cuts") or []) for s in others)
            if mine >= most:
                lint.err("E113", f"session {setup_n}",
                         f"session {setup_n} carries the project setup and {mine} cuts, "
                         f"while the heaviest other session carries {most}. The session "
                         f"holding the setup must carry strictly fewer cuts than the "
                         f"others - tip-split shipped this shape and ran 45 minutes "
                         f"against a 40 minute cap. Move a cut out of session {setup_n}.")


def lint_spec(project: Path) -> Lint:
    lint = Lint()
    sj, sm = project / "spec.json", project / "spec.md"

    if not sj.exists():
        lint.err("E001", "spec.json", "spec.json is missing")
        return lint
    try:
        spec = json.loads(sj.read_text())
    except json.JSONDecodeError as e:
        lint.err("E002", "spec.json", f"spec.json is not valid JSON: {e}")
        return lint

    # -- top level --------------------------------------------------------
    for key in ("slug", "title", "track", "sessions_planned", "stack", "sessions"):
        if key not in spec:
            lint.err("E010", "spec.json", f"missing top-level key {key!r}")
    if lint.errors:
        return lint

    if not RE_SLUG.match(str(spec["slug"])):
        lint.err("E011", "slug", f"slug must be kebab-case, got {spec['slug']!r}")
    if spec["track"] not in TRACKS:
        lint.err("E012", "track", f"track must be one of {sorted(TRACKS)}")
    if not isinstance(spec.get("stack"), list) or not spec["stack"]:
        lint.err("E013", "stack", "stack must be a non-empty list")

    for name in (spec.get("code_checks") or []):
        if name not in CODE_CHECKS:
            lint.err("E120", "code_checks",
                     f"unknown code check {name!r} - known: {sorted(CODE_CHECKS)}")

    endpoints = spec.get("endpoints") or []
    screens = spec.get("screens") or []
    sessions = spec.get("sessions") or []

    # -- endpoints --------------------------------------------------------
    ep_ids: set[str] = set()
    for i, ep in enumerate(endpoints):
        w = f"endpoints[{i}]"
        eid = ep.get("id", "")
        if not RE_EP.match(eid):
            lint.err("E020", w, f"endpoint id must match ep-<kebab>, got {eid!r}")
        if eid in ep_ids:
            lint.err("E021", w, f"duplicate endpoint id {eid!r}")
        ep_ids.add(eid)
        if ep.get("method") not in METHODS:
            lint.err("E022", w, f"method must be one of {sorted(METHODS)}, got {ep.get('method')!r}")
        if not str(ep.get("path", "")).startswith("/"):
            lint.err("E023", w, f"path must start with '/', got {ep.get('path')!r}")
        status = ep.get("status")
        if not isinstance(status, list) or not all(isinstance(s, int) for s in status) or not status:
            lint.err("E024", w, "status must be a non-empty list of integers")

    # -- screens ----------------------------------------------------------
    sc_ids: set[str] = set()
    for i, sc in enumerate(screens):
        w = f"screens[{i}]"
        sid = sc.get("id", "")
        if not RE_SC.match(sid):
            lint.err("E030", w, f"screen id must match sc-<kebab>, got {sid!r}")
        if sid in sc_ids:
            lint.err("E031", w, f"duplicate screen id {sid!r}")
        sc_ids.add(sid)
        if not str(sc.get("route", "")).startswith("/"):
            lint.err("E032", w, f"route must start with '/', got {sc.get('route')!r}")
        if not sc.get("states"):
            lint.err("E033", w, "screen must list its states (empty, loading, loaded, error...)")

    if not ep_ids and not sc_ids:
        lint.err("E034", "spec.json", "spec declares no endpoints and no screens - nothing to verify")

    # -- sessions ---------------------------------------------------------
    if len(sessions) != spec["sessions_planned"]:
        lint.err("E040", "sessions",
                 f"sessions_planned is {spec['sessions_planned']} but {len(sessions)} sessions are defined")
    for i, s in enumerate(sessions):
        if s.get("n") != i + 1:
            lint.err("E041", f"sessions[{i}]", f"session numbers must run 1..n in order, got n={s.get('n')!r}")

    crit_ids: set[str] = set()
    cut_ids: set[str] = set()
    cuts_seen_by_session: dict[str, int] = {}
    referenced_cuts: set[str] = set()
    cut_signature: dict[str, set[str]] = {}
    built: dict[str, int] = {}

    for s in sessions:
        n = s.get("n")
        w = f"session {n}"
        for key in ("title", "goal", "teaches", "builds", "criteria", "cuts"):
            if key not in s:
                lint.err("E042", w, f"missing key {key!r}")
        if lint.errors and any(e["where"] == w for e in lint.errors):
            continue

        if s.get("id") is not None and s["id"] != f"S{n:02d}":
            lint.err("E043", w,
                     f"session id must be S{n:02d} to match n={n}, got {s['id']!r}")

        _scan_vague(lint, s["goal"], f"{w}.goal", "E050")
        _scan_placeholder(lint, s["goal"], f"{w}.goal", "E051")
        _scan_placeholder(lint, s["title"], f"{w}.title", "E051")

        # cuts declared here
        for c in s["cuts"]:
            cid = c.get("id", "")
            cw = f"{w}.cut {cid}"
            if not RE_CUT.match(cid):
                lint.err("E060", cw, f"cut id must match cut-<kebab>, got {cid!r}")
            if cid in cut_ids:
                lint.err("E061", cw, f"duplicate cut id {cid!r} - cut ids are global")
            cut_ids.add(cid)
            cuts_seen_by_session[cid] = n
            if not c.get("file"):
                lint.err("E062", cw, "cut must name the file it lives in")
            hint = c.get("hint", "")
            if len(hint.split()) < 4:
                lint.err("E063", cw, f"hint is the only thing the student sees - write a real sentence, got {hint!r}")
            _scan_vague(lint, hint, cw, "E064")
            # A hint with nothing concrete in it cannot be graded against, and
            # the student cannot tell which symbol they are meant to write.
            # Warning, not error: hints are deliberately prose so they do not
            # hand over the answer, so the person at Gate 1 makes the call.
            if hint and not RE_ANCHOR.search(hint):
                lint.warn("W066", cw,
                          "hint names nothing concrete - no symbol, path, method, "
                          f"status or count. The student cannot tell what to write: {hint!r}")
            if RE_HINT_RETURN.search(hint):
                lint.warn("W067", cw,
                          "hint is phrased as 'return ...', which puts the return inside "
                          "the markers. If it is a typed function's only return the "
                          "skeleton will not compile (TS2355) - no red test, no build at "
                          "all. Prefer 'put X into <the value declared above>'. The cutter "
                          "checks the real marker placement at step 8.")

        if len(s["cuts"]) > MAX_CUTS:
            lint.err("E065", w, f"{len(s['cuts'])} cut points - more than {MAX_CUTS} will not fit 40 minutes")

        # criteria
        n_crit = len(s["criteria"])
        if not (MIN_CRITERIA <= n_crit <= MAX_CRITERIA):
            lint.err("E070", w,
                     f"{n_crit} acceptance criteria - a 40 minute session needs between "
                     f"{MIN_CRITERIA} and {MAX_CRITERIA}")
        for k, c in enumerate(s["criteria"], start=1):
            cid = c.get("id", "")
            cw = f"{w}.criterion {cid}"
            # c-3-1 or the doc's S03-AC01 - either, but one shape per session
            if cid not in (f"c-{n}-{k}", f"S{n:02d}-AC{k:02d}"):
                lint.err("E071", cw,
                         f"criterion id must be c-{n}-{k} or S{n:02d}-AC{k:02d} in "
                         f"order, got {cid!r}")
            if cid in crit_ids:
                lint.err("E072", cw, f"duplicate criterion id {cid!r}")
            crit_ids.add(cid)

            check = c.get("check", "")
            _scan_vague(lint, check, cw, "E073")
            _scan_placeholder(lint, check, cw, "E074")
            low = check.lower()
            concrete = (
                any(v in low for v in TESTABLE_VERBS)
                or any(m in check for m in METHODS)
                or re.search(r"\b[1-5]\d\d\b", check)
            )
            if not concrete:
                lint.err("E075", cw,
                         "criterion is not testable - name an HTTP method, a status code, "
                         f"or use a verb like {TESTABLE_VERBS[:5]}. Got: {check!r}")
            if len(check.split()) < 5:
                lint.err("E076", cw, f"criterion is too short to test: {check!r}")

            target = c.get("target")
            if target not in ep_ids and target not in sc_ids:
                lint.err("E077", cw, f"target {target!r} is not a declared endpoint or screen id")

            for ref in c.get("cuts", []):
                referenced_cuts.add(ref)
                cut_signature.setdefault(ref, set()).add(cid)
                if ref not in cut_ids:
                    lint.err("E078", cw,
                             f"references cut {ref!r} which is not declared in this or an earlier session")

        for b in s["builds"]:
            if b not in ep_ids and b not in sc_ids:
                lint.err("E080", w, f"builds {b!r} which is not a declared endpoint or screen id")
            if b in built:
                lint.err("E081", w, f"{b!r} is already built in session {built[b]}")
            built[b] = n

    # -- whole-spec joins -------------------------------------------------
    for orphan in sorted(cut_ids - referenced_cuts):
        lint.err("E090", f"cut {orphan}",
                 "no criterion depends on this cut - the skeleton would have a hole "
                 "that no test asks the student to fill")
    for missing in sorted((ep_ids | sc_ids) - set(built)):
        lint.err("E091", missing, "declared but no session builds it")

    _check_grading_independence(lint, cut_signature)
    _check_session_load(lint, sessions)

    # -- spec.md ----------------------------------------------------------
    if not sm.exists():
        lint.err("E100", "spec.md", "spec.md is missing - Gate 1 has nothing to read")
        return lint
    md = sm.read_text()
    for h in REQUIRED_MD_HEADINGS:
        if h not in md:
            lint.err("E101", "spec.md", f"missing required heading {h!r}")
    _scan_placeholder(lint, md, "spec.md", "E102")
    for s in sessions:
        if s.get("title") and s["title"] not in md:
            lint.err("E103", "spec.md", f"session {s['n']} title {s['title']!r} is not in spec.md")
    for cid in sorted(crit_ids):
        if cid not in md:
            lint.warn("W104", "spec.md", f"criterion {cid} is in spec.json but not written up in spec.md")
    for cid in sorted(cut_ids):
        if cid not in md:
            lint.warn("W105", "spec.md", f"cut {cid} is in spec.json but not written up in spec.md")

    return lint


def minute_estimates(project: Path) -> list[dict]:
    """Always reported, pass or fail - before this, nothing told anyone the
    teaching load of a session until the Pack Writer timed it at step 9."""
    try:
        spec = json.loads((project / "spec.json").read_text())
    except (OSError, json.JSONDecodeError):
        return []
    sessions = spec.get("sessions") or []
    setup_n = _setup_session(sessions)
    return [{"n": s.get("n"),
             "minutes": session_minutes(s, s.get("n") == setup_n),
             "cuts": len(s.get("cuts") or []),
             "builds": len(s.get("builds") or []),
             "concepts": len(s.get("teaches") or []),
             "carries_setup": s.get("n") == setup_n,
             "over_cap": session_minutes(s, s.get("n") == setup_n) > SESSION_MINUTES_CAP}
            for s in sessions]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m pipeline.spec_linter <project-dir>", file=sys.stderr)
        return 2
    project = Path(argv[1]).resolve()
    lint = lint_spec(project)
    report = {
        "ok": not lint.errors,
        "errors": lint.errors,
        "warnings": lint.warnings,
        "counts": {"errors": len(lint.errors), "warnings": len(lint.warnings)},
        "session_minutes": minute_estimates(project),
        "spec_hash": spec_hash(project),
    }
    (project / "lint.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
