"""Spec linter - SCRIPT, step 2's checker.

A rule check must give the same answer every time, so there is no agent in here.
Reads spec.json and spec.md, writes lint.json, exits 0 clean / 1 dirty.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

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
RE_CUT = re.compile(r"^cut-[a-z0-9]+(-[a-z0-9]+)*$")
RE_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# 40 minutes of live teaching. These caps are the session-fit heuristic that
# Gate 1 would otherwise have to eyeball.
MIN_CRITERIA, MAX_CRITERIA = 2, 6
MAX_CUTS = 5

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
    built: dict[str, int] = {}

    for s in sessions:
        n = s.get("n")
        w = f"session {n}"
        for key in ("title", "goal", "teaches", "builds", "criteria", "cuts"):
            if key not in s:
                lint.err("E042", w, f"missing key {key!r}")
        if lint.errors and any(e["where"] == w for e in lint.errors):
            continue

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
            if cid != f"c-{n}-{k}":
                lint.err("E071", cw, f"criterion id must be c-{n}-<k> in order, got {cid!r}")
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
    }
    (project / "lint.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
