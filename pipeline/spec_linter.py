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

# Every cut is an assignment to a value declared above the markers, so a cut has
# exactly one symbol it writes into. `writes_into` records it, and this is how a
# hint is checked against it. Four findings across two Gate 1 rounds on
# pipeline-test-04 were one class: a hint naming a symbol that is not the
# declared accumulator. Round 2 A1 - both frames hints said to append to
# `frames` while the value declared above the markers was `const out`, so
# `frames.push` is a type error on the exported function, and the student meets
# it on their first keystroke. Nothing downstream saw it: W066 only checks that
# a backtick is present, tsc sees the all-open skeleton where the TODO is still
# a comment, and the hint is frozen at Gate 1. The Breaker caught it on one pass
# of two, which is exactly why it belongs in a script instead.
RE_BACKTICKED = re.compile(r"`([^`]+)`")
RE_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def backticked_idents(text: str) -> set[str]:
    """The identifiers a hint names in backticks - `frames()` and `rolls` both count."""
    found: set[str] = set()
    for raw in RE_BACKTICKED.findall(text or ""):
        name = raw.strip()
        if name.endswith("()"):
            name = name[:-2].strip()
        if RE_IDENT.match(name):
            found.add(name)
    return found


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

# --- how much a cut costs to teach, flow 2 only -----------------------------
# MINUTES_PER_CUT above weighs every cut the same 6 minutes. Five consecutive
# projects overran on one cut far larger than its siblings, so round 3 first
# weighted a cut by its HINT LENGTH. pipeline-test-03 disproved that outright:
# every cut came in at 46-53 words, under the nominal, the linter reported both
# sessions at 38.5 against the 40 cap and stayed silent - and the Pack Writer
# then timed session 1 at 48 and session 2 at 45, locating the excess exactly:
#
#   cut-parse-line "carries three rules, a rule ORDER, and the argument against
#   Date - about 13 live minutes, not the flat 6 the linter charges"
#
# on a 53-word hint. The hints were not being gamed; they were honest. Length
# simply does not predict teaching load, because three ordered rules compress to
# 53 words as easily as one rule does. What costs live minutes is the number of
# decisions a cut states and whether their order matters.
#
# So the weight is decisions first, with a small residual on length for the case
# decisions cannot see: an algorithm with no conditional prose at all.
# pipeline-test-01's cut-reveal-from is a breadth-first flood fill, 103 words and
# 41 lines removed, and states zero conditions.
#
# CALIBRATION IS THIN - four sessions, three of them measured:
#
#   pipeline-test-01 s2   flat 32.5   model 40.6   measured 45   (hero)
#   pipeline-test-02 s2   flat 37.0   model 53.9   measured 50   (Priya)
#   pipeline-test-03 s1   flat 38.5   model 52.1   measured 47   (Priya)
#   pipeline-test-03 s2   flat 38.5   model 40.2   pack est 45
#
# pipeline-test-03 s1 is the only OUT-OF-SAMPLE point this model has faced: it
# was fitted against the Pack Writer's estimate of 48 and the session then
# measured 47, so the model over-predicted by 5.1. Refitting on the measurement
# moves MINUTES_PER_DECISION 1.7 -> 1.6 and the worst error 5.1 -> 4.9. That is
# noise, and refitting two parameters on four points again would buy nothing, so
# the constants stand.
#
# Worst error about 5 minutes, against a flat model that was 6.5 to 13 minutes
# low on every one of them and silent on this one. The gain is not precision -
# the error now falls on both sides instead of always short, and it arrives at
# step 2 instead of step 9.
#
# KNOW WHAT THIS IS FOR. The Pack Writer predicted 48 against the measured 47 -
# five times closer than this model - because it reads the session plan it just
# wrote, while the linter reads prose in spec.json before any plan exists. The
# linter is not trying to win that comparison and cannot. Its job is to be wrong
# by about five minutes nine steps earlier, where the fix is one Spec Writer pass
# rather than a rebuild. Treat a session it prices near the cap as a question for
# the Pack Writer, not as an answer.
#
# Flow 1 keeps the flat weight it was calibrated on. Its specs write many small
# cuts where flow 2 writes few large ones, so the flat 6 over-charges it - the
# model reads recipe-box s1 and tip-split s1 about 10 minutes HIGH - and those
# three projects have shipped.
NOMINAL_HINT_WORDS = 55        # length beyond which the residual starts
MINUTES_PER_DECISION = 1.7     # one stated condition, or one ordering between rules
MINUTES_PER_OVERSIZE_WORD = 0.04
CUT_SHARE_CAP = 0.45           # one cut's share of a session's cut minutes
SHARE_MIN_CUTS = 3             # below this a "share" is arithmetic, not skew

# A decision is a branch the instructor has to state and justify: a condition, or
# an ordering between rules. Deliberately NOT positional words like "first" or
# "next" - "the first number is the first object's own paise" describes an
# element, not a branch. An earlier marker set included them, fitted the four
# sessions visibly better (worst error 3.2 against 4.8), and was dropped: with
# four points a regex that happens to fire more is indistinguishable from one
# that measures more, and the positional reading is plainly not a decision.
RE_DECISION = re.compile(
    r"\b(unless|otherwise|when|if|else|except|then|before|in that order|falls? through)\b",
    re.IGNORECASE)

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


def _flow(project: Path) -> int:
    """A state file with no flow key is flow 1, same rule as state.py. A
    project with no state file at all reads as flow 1 too, so a bare fixture
    keeps the behaviour it was written against."""
    try:
        return int(json.loads(
            (project / ".pipeline" / "state.json").read_text(encoding="utf-8")).get("flow", 1))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return 1


def cut_words(cut: object) -> int:
    """Hint length in words. Tolerates a cut that is not a dict: the session
    load checks are also called on bare count fixtures."""
    if not isinstance(cut, dict):
        return 0
    return len((cut.get("hint") or "").split())


def cut_decisions(cut: object) -> int:
    """How many branches the instructor has to state and justify.

    This is the thing hint length was standing in for and failed at:
    pipeline-test-03's cut-parse-line states four ordered fallbacks in 53 words
    and takes about 13 live minutes, while cut-account-totals states one rule in
    46 words and takes about 6.
    """
    if not isinstance(cut, dict):
        return 0
    return len(RE_DECISION.findall(cut.get("hint") or ""))


def cut_minutes(cut: object, weighted: bool) -> float:
    """The flat cost for a one-rule cut, plus what its decisions cost, plus a
    small residual on length for the algorithm that states no conditions at all.

    Never below MINUTES_PER_CUT - a cut with no branches is not free, it is a
    cut whose cost the flat weight already covers.
    """
    if not weighted:
        return MINUTES_PER_CUT
    over = max(0, cut_words(cut) - NOMINAL_HINT_WORDS)
    return (MINUTES_PER_CUT
            + MINUTES_PER_DECISION * cut_decisions(cut)
            + MINUTES_PER_OVERSIZE_WORD * over)


def session_minutes(s: dict, carries_setup: bool, *, weighted: bool = False) -> float:
    return round(
        BASE_MINUTES
        + sum(cut_minutes(c, weighted) for c in (s.get("cuts") or []))
        + MINUTES_PER_BUILD * len(s.get("builds") or [])
        + MINUTES_PER_CONCEPT * len(s.get("teaches") or [])
        + (SETUP_MINUTES if carries_setup else 0.0), 1)


def _check_cut_share(lint: Lint, sessions: list[dict]) -> None:
    """One cut far larger than its siblings - the shape four consecutive
    projects overran on, most recently pipeline-test-02 session 2 at 50 minutes
    against 40 and habit-tracker's cut-api-toggle, estimated 6 and measured
    about 20.

    A warning, not an error, for the same reason W112 is: the session may still
    be teachable, and the fix is a judgement call about which rules belong in
    one live-coding block. Under SHARE_MIN_CUTS cuts a share is arithmetic - two
    cuts always split at least 50/50 - so those sessions are left to W112.
    """
    for s in sessions:
        cuts = s.get("cuts") or []
        if len(cuts) < SHARE_MIN_CUTS:
            continue
        mins = [(c, cut_minutes(c, True)) for c in cuts]
        total = sum(m for _, m in mins)
        if total <= 0:
            continue
        big, big_m = max(mins, key=lambda cm: cm[1])
        share = big_m / total
        if share <= CUT_SHARE_CAP:
            continue
        cid = big.get("id", "?") if isinstance(big, dict) else "?"
        rest = sorted(m for c, m in mins if c is not big)
        lint.warn("W114", f"session {s.get('n')}",
                  f"cut {cid} is {share:.0%} of the session's {total:g} cut "
                  f"minutes ({big_m:g} against siblings at "
                  f"{', '.join(format(m, 'g') for m in rest)}) - over the "
                  f"{CUT_SHARE_CAP:.0%} cap, on {cut_decisions(big)} stated "
                  f"decisions and {cut_words(big)} hint words. Five projects "
                  f"have overrun on this shape. Split {cid} so each half states "
                  f"fewer decisions, or name a drop candidate inside this "
                  f"session. Do NOT move it into the setup session - that is "
                  f"E113. Shortening the hint does not make the cut smaller.")


def _check_session_load(lint: Lint, sessions: list[dict], weighted: bool = False) -> None:
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
        mins = session_minutes(s, n == setup_n, weighted=weighted)
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
        spec = json.loads(sj.read_text(encoding="utf-8"))
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

            # The symbol the block assigns to. Optional, because three shipped
            # projects predate it and a warning must not fail them retroactively
            # - but once it is declared, the hint has to agree with it.
            writes = c.get("writes_into")
            named = backticked_idents(hint)
            if writes is None:
                lint.warn("W068", cw,
                          "cut does not declare writes_into, the symbol the block "
                          "assigns to. Nothing then compares the hint's symbols to the "
                          "value declared above the markers, so a hint naming the wrong "
                          "one reaches the student as a type error and is frozen at "
                          "Gate 1. Declare it and this becomes E121.")
            elif not isinstance(writes, str) or not RE_IDENT.match(writes.strip()):
                lint.err("E122", cw,
                         f"writes_into must be a bare identifier, got {writes!r}")
            elif writes.strip() not in named:
                lint.err("E121", cw,
                         f"hint must name the value it writes into, in backticks: "
                         f"writes_into is `{writes.strip()}` but the hint backticks "
                         f"{sorted(named) if named else 'no identifier at all'}. A hint "
                         f"pointing at a symbol that is not the one declared above the "
                         f"markers is a type error on the student's first keystroke.")

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
    # Flow 1 keeps the flat cut weight it was calibrated on; the oversize
    # surcharge and W114 step aside rather than fail three shipped projects
    # retroactively.
    weighted = _flow(project) >= 2
    _check_session_load(lint, sessions, weighted)
    if weighted:
        _check_cut_share(lint, sessions)

    # -- spec.md ----------------------------------------------------------
    if not sm.exists():
        lint.err("E100", "spec.md", "spec.md is missing - Gate 1 has nothing to read")
        return lint
    md = sm.read_text(encoding="utf-8")
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
        spec = json.loads((project / "spec.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    sessions = spec.get("sessions") or []
    setup_n = _setup_session(sessions)
    weighted = _flow(project) >= 2
    out = []
    for s in sessions:
        mins = session_minutes(s, s.get("n") == setup_n, weighted=weighted)
        cuts = s.get("cuts") or []
        row = {"n": s.get("n"),
               "minutes": mins,
               "cuts": len(cuts),
               "builds": len(s.get("builds") or []),
               "concepts": len(s.get("teaches") or []),
               "carries_setup": s.get("n") == setup_n,
               "over_cap": mins > SESSION_MINUTES_CAP,
               "weighted": weighted}
        # Gate 1 reads this. Without the per-cut split, a session that is over
        # only because one cut is oversized looks the same as one that is over
        # because it carries four ordinary cuts, and the two need opposite fixes.
        if weighted and cuts:
            per = sorted(((cut_minutes(c, True), c.get("id", "?") if isinstance(c, dict) else "?",
                           cut_words(c), cut_decisions(c)) for c in cuts), reverse=True)
            total = sum(m for m, _, _, _ in per)
            row["cut_minutes"] = [{"id": i, "minutes": round(m, 1),
                                   "decisions": dc, "hint_words": w}
                                  for m, i, w, dc in per]
            row["largest_cut_share"] = round(per[0][0] / total, 2) if total else 0.0
        out.append(row)
    return out


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
    (project / "lint.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
