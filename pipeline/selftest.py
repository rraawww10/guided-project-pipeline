"""Self-test for the deterministic core.

The scripts are the part that must give the same answer every time, so they get
a regression test. No agents, no network, no npm - runs in about a second.

  python -m pipeline.selftest

Every check below that mentions a project by name is a regression test for
something that actually went wrong in round 1. See blockers_round_1.txt.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import (cli, code_check, cutter, deploy_check, gate1, guard, guide_linter,
               leak_scan, mutation, redfirst, spec_linter, watchdog)
from .deploy_check import find_advisories
from .spec_linter import Lint, _scan_placeholder, _scan_vague, lint_spec
from .state import (GATES_BY_FLOW, PHASES_BY_FLOW, RETRY_LIMIT, STEP_RUN_LIMIT,
                    State, frozen_hash, spec_drift, spec_hash)

ROOT = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []
CHECKS = 0


def check(name: str, got, want) -> None:
    global CHECKS
    CHECKS += 1
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    if not ok:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


GOOD_SPEC = {
    "slug": "fixture", "title": "Fixture", "track": "fullstack", "sessions_planned": 1,
    "stack": ["next"], "source": None,
    "endpoints": [{"id": "ep-todos-list", "method": "GET", "path": "/api/todos",
                   "request": None, "response": "Todo[]", "status": [200]}],
    "screens": [{"id": "sc-list", "route": "/", "elements": ["todo list"],
                 "states": ["empty", "loaded"]}],
    "sessions": [{
        "n": 1, "title": "List the todos", "goal": "Read todos from the store and render them",
        "teaches": ["route handlers"], "builds": ["ep-todos-list", "sc-list"],
        "criteria": [
            {"id": "c-1-1", "check": "GET /api/todos returns 200 with a JSON array of Todo",
             "target": "ep-todos-list", "cuts": ["cut-api-list"]},
            {"id": "c-1-2", "check": "Screen sc-list renders one row per todo in the store",
             "target": "sc-list", "cuts": ["cut-ui-rows"]},
            {"id": "c-1-3", "check": "Screen sc-list displays the heading Todos on first load",
             "target": "sc-list", "cuts": []},
        ],
        "cuts": [
            # Hints follow the declare-above/assign-inside pattern. The old
            # fixture said "Return every todo from the store as JSON" over code
            # whose only return sat inside the markers - it encoded the exact
            # TS2355 anti-pattern the linter and the cutter now reject.
            {"id": "cut-api-list", "file": "app/api/todos/route.ts",
             "hint": "Put every todo the store holds into body and set status to 200"},
            {"id": "cut-ui-rows", "file": "app/page.tsx",
             "hint": "Render one `li` for each todo in `rows`, showing its title"},
        ],
    }],
}

GOOD_MD = """# Fixture
## Outcome
A one page todo list.
## Out of scope
Adding todos.
## Sessions
### Session 1 - List the todos
- c-1-1 GET /api/todos returns 200 with a JSON array of Todo
- c-1-2 Screen sc-list renders one row per todo in the store
- c-1-3 Screen sc-list displays the heading Todos on first load
Cut points: cut-api-list, cut-ui-rows
"""

# The pattern proven in fixtures/runner-check: the return stays outside the
# markers and the cut assigns the values that feed it.
ROUTE_TS = """import { store } from "@/lib/store"

export async function GET(): Promise<Response> {
  let body: unknown[] = []
  let status = 501
  // >>> CUT cut-api-list
  body = await store.all()
  status = 200
  // <<< CUT cut-api-list
  return Response.json(body, { status })
}
"""

# The anti-pattern, kept so the checks can prove they catch it.
ROUTE_TS_BAD = """import { store } from "@/lib/store"

export async function GET(): Promise<Response> {
  // >>> CUT cut-api-list
  const todos = await store.all()
  return Response.json(todos)
  // <<< CUT cut-api-list
}
"""

PAGE_TSX = """export default async function Page() {
  return (
    <ul>
      {/* >>> CUT cut-ui-rows */}
      {todos.map((t) => (<li key={t.id}>{t.title}</li>))}
      {/* <<< CUT cut-ui-rows */}
    </ul>
  )
}
"""

AMBIGUITY_MD = """# Ambiguity report - fixture

**Verdict:** 1 blocking, 1 worth a look

## Blocking
### A1 - the list order is not stated
- **Where:** spec.md, Session 1, criterion c-1-2
- **Owner:** test-runner
- **Why it matters:** the Builder picks an order and the test pins it.

## Worth a look
### B1 - the heading casing is not stated
- **Where:** spec.md, Session 1
- **Owner:** nothing
- **Why it matters:** cosmetic.
"""


def legacy_state(project: Path, slug: str) -> None:
    """Pin a bare fixture to flow 1. These checks were written for the twelve-step
    flow and assert its semantics; test_flow2 covers the new one."""
    (project / ".pipeline").mkdir(parents=True, exist_ok=True)
    (project / ".pipeline" / "state.json").write_text(json.dumps({
        "slug": slug, "created": "2026-01-01T00:00:00+00:00", "flow": 1,
        "phase": "spec", "retries": {ph: 0 for ph in PHASES_BY_FLOW[1]},
        "step_runs": {}, "gates": {g: None for g in GATES_BY_FLOW[1].values()},
        "steps": [], "ticket": None, "dry_run": None, "feedback": [],
    }, indent=2) + "\n")


def make_project(tmp: Path, spec: dict = None, md: str = None,
                 route: str = None, flow: int = 1) -> Path:
    """flow defaults to 1: every check written before requirements_doc.md tests
    the twelve-step behaviour that must keep working. test_flow2 opts in to 2."""
    p = tmp / "projects" / "fixture"
    (p / "app" / "api" / "todos").mkdir(parents=True)
    (p / "verify").mkdir()
    (p / ".pipeline").mkdir()
    (p / ".pipeline" / "state.json").write_text(json.dumps({
        "slug": "fixture", "created": "2026-01-01T00:00:00+00:00", "flow": flow,
        "phase": PHASES_BY_FLOW[flow][0],
        "retries": {ph: 0 for ph in PHASES_BY_FLOW[flow]},
        "step_runs": {},
        "gates": {g: None for g in GATES_BY_FLOW[flow].values()},
        "steps": [], "ticket": None, "dry_run": None, "feedback": [],
    }, indent=2) + "\n")
    (p / "spec.json").write_text(json.dumps(spec or GOOD_SPEC, indent=2))
    (p / "spec.md").write_text(md or GOOD_MD)
    (p / "app" / "api" / "todos" / "route.ts").write_text(route or ROUTE_TS)
    (p / "app" / "page.tsx").write_text(PAGE_TSX)
    return p


# ---------------------------------------------------------------- linter ----
def test_linter(tmp: Path) -> None:
    print("spec linter")
    p = make_project(tmp)
    lint = lint_spec(p)
    check("clean spec passes", lint.errors, [])
    check("clean spec has no warnings either", lint.warnings, [])

    def report(mutate) -> Lint:
        spec = json.loads(json.dumps(GOOD_SPEC))
        mutate(spec)
        (p / "spec.json").write_text(json.dumps(spec))
        return lint_spec(p)

    def codes(mutate) -> set[str]:
        return {e["code"] for e in report(mutate).errors}

    def warns(mutate) -> set[str]:
        return {e["code"] for e in report(mutate).warnings}

    def has(name, mutate, code):
        check(name, code in codes(mutate), True)

    def warned(name, mutate, code):
        r = report(mutate)
        check(name, (code in {w["code"] for w in r.warnings},
                     code in {e["code"] for e in r.errors}), (True, False))

    has("vague goal rejected",
        lambda s: s["sessions"][0].update(goal="Handle errors properly"), "E050")
    has("untestable criterion rejected",
        lambda s: s["sessions"][0]["criteria"][0].update(check="the API works"), "E075")
    has("out-of-order criterion id rejected",
        lambda s: s["sessions"][0]["criteria"][1].update(id="c-1-9"), "E071")
    has("orphan cut rejected",
        lambda s: s["sessions"][0]["cuts"].append(
            {"id": "cut-orphan", "file": "x.ts", "hint": "nothing depends on this cut"}), "E090")
    has("undeclared cut reference rejected",
        lambda s: s["sessions"][0]["criteria"][0].update(cuts=["cut-nope"]), "E078")
    has("target that is not an endpoint or screen rejected",
        lambda s: s["sessions"][0]["criteria"][0].update(target="ep-nope"), "E077")
    has("too many criteria for 40 minutes rejected",
        lambda s: s["sessions"][0]["criteria"].extend(
            [dict(s["sessions"][0]["criteria"][2], id=f"c-1-{i}") for i in range(4, 12)]), "E070")
    has("one-word cut hint rejected",
        lambda s: s["sessions"][0]["cuts"][0].update(hint="fix"), "E063")
    has("session count mismatch rejected",
        lambda s: s.update(sessions_planned=3), "E040")
    has("bad method rejected",
        lambda s: s["endpoints"][0].update(method="FETCH"), "E022")

    # --- E110: bypassable grading cuts. recipe-box round 3 B1, and the
    # skeleton-check partial-subset blind spot, are the same defect.
    has("two cuts graded by the same criteria rejected (recipe-box R3 B1)",
        lambda s: s["sessions"][0]["criteria"][1].update(cuts=["cut-api-list", "cut-ui-rows"])
        or s["sessions"][0]["criteria"][0].update(cuts=["cut-api-list", "cut-ui-rows"]),
        "E110")
    check("a criterion that isolates one cut clears E110",
          "E110" in codes(lambda s: s["sessions"][0]["criteria"][2].update(
              cuts=["cut-api-list", "cut-ui-rows"])), False)

    # --- session load: the two round-1 overruns, moved from step 9 to step 2
    def heavy(s, n_cuts, n_builds, n_teach=6):
        ses = s["sessions"][0]
        ses["cuts"] = [{"id": f"cut-x{i}", "file": "a.ts",
                        "hint": f"Assign value number {i} to the row"} for i in range(n_cuts)]
        ses["criteria"] = [
            {"id": f"c-1-{i+1}",
             "check": f"GET /api/todos returns 200 for case number {i}",
             "target": "ep-todos-list", "cuts": [f"cut-x{i}"]} for i in range(n_cuts)]
        s["endpoints"] = s["endpoints"] * 1
        ses["builds"] = ["ep-todos-list", "sc-list"][:n_builds]
        ses["teaches"] = ["a", "b", "c", "d", "e", "f"][:n_teach]

    has("session over the 50 minute ceiling rejected (tip-split session 1)",
        lambda s: heavy(s, 5, 2), "E111")
    warned("session over the 40 minute cap warns, not errors (recipe-box session 3)",
           lambda s: heavy(s, 4, 0, 5), "W112")

    two = json.loads(json.dumps(GOOD_SPEC))
    two["sessions_planned"] = 2
    s1 = two["sessions"][0]
    s2 = json.loads(json.dumps(s1))
    s2.update(n=2, title="Add a todo", builds=[],
              criteria=[dict(c, id=f"c-2-{i+1}") for i, c in enumerate(s1["criteria"])])
    two["sessions"] = [s1, s2]
    (p / "spec.json").write_text(json.dumps(two))
    (p / "spec.md").write_text(GOOD_MD + "\n### Session 2 - Add a todo\n")
    check("setup session with as many cuts as another is rejected (tip-split lesson)",
          "E113" in {e["code"] for e in lint_spec(p).errors}, True)
    s1["cuts"] = s1["cuts"][:1]
    s1["criteria"] = [dict(s1["criteria"][0], cuts=["cut-api-list"]),
                      dict(s1["criteria"][1], cuts=[]), s1["criteria"][2]]
    (p / "spec.json").write_text(json.dumps(two))
    check("setup session with fewer cuts than the others is accepted",
          "E113" in {e["code"] for e in lint_spec(p).errors}, False)

    check("session minutes weigh setup, cuts, builds and concepts",
          spec_linter.session_minutes(
              {"cuts": [1, 2, 3, 4], "builds": [1, 2], "teaches": [1, 2, 3, 4, 5, 6]}, True),
          55.0)
    check("the same session without the setup fits",
          spec_linter.session_minutes(
              {"cuts": [1, 2, 3], "builds": [], "teaches": [1, 2, 3, 4, 5]}, False), 35.5)

    # --- hint quality: warnings, because a hint is deliberately prose
    warned("hint that names nothing concrete warns (recipe-box R3 B1)",
           lambda s: s["sessions"][0]["cuts"][0].update(
               hint="Make the thing work the way the screen needs it to"), "W066")
    warned("hint phrased as 'return ...' warns about TS2355",
           lambda s: s["sessions"][0]["cuts"][0].update(
               hint="Return every todo from the store as JSON"), "W067")

    # false positives: domain words must survive
    for text in ("Screen sc-list renders one row per todo",
                 "A handsome card displays the awesome summary",
                 "GET /api/todos returns 200 with a JSON array"):
        lint = Lint()
        _scan_vague(lint, text, "x", "E1")
        _scan_placeholder(lint, text, "x", "E2")
        check(f"not flagged: {text[:38]!r}", lint.errors, [])
    for text in ("TODO: finish this", "The list shows lorem ipsum text", "Some items are hidden"):
        lint = Lint()
        _scan_vague(lint, text, "x", "E1")
        _scan_placeholder(lint, text, "x", "E2")
        check(f"flagged: {text[:38]!r}", bool(lint.errors), True)

    # the report always carries the estimate and the hash, pass or fail
    q = make_project(tmp / "report")
    with contextlib.redirect_stdout(io.StringIO()):
        spec_linter.main(["", str(q)])
    rep = json.loads((q / "lint.json").read_text())
    check("lint.json reports session minutes", rep["session_minutes"][0]["minutes"], 35.5)
    check("lint.json reports the spec hash", rep["spec_hash"], spec_hash(q))


# ---------------------------------------------------------------- cutter ----
def test_cutter(tmp: Path) -> None:
    print("cutter")
    p = make_project(tmp)
    out = cutter.cut(p)
    check("both cuts applied", out["count"], 2)
    skel_route = (p / "skeleton" / "api" / "todos" / "route.ts").read_text()
    skel_page = (p / "skeleton" / "page.tsx").read_text()
    check("ts comment style",
          "  // TODO(cut-api-list): Put every todo the store holds into body and set "
          "status to 200" in skel_route, True)
    check("jsx comment style",
          "      {/* TODO(cut-ui-rows): Render one `li` for each todo in `rows`, "
          "showing its title */}" in skel_page, True)
    check("implementation removed", "store.all()" in skel_route, False)
    check("the return outside the markers survives",
          "return Response.json(body, { status })" in skel_route, True)
    check("surrounding code kept", 'import { store } from "@/lib/store"' in skel_route, True)
    check("no markers left behind", ">>> CUT" in skel_route + skel_page, False)
    check("cutting twice gives the same skeleton",
          (cutter.cut(p), (p / "skeleton" / "page.tsx").read_text())[1], skel_page)

    def err(name, mutate) -> None:
        q = make_project(tmp / name)
        mutate(q)
        try:
            cutter.cut(q)
            check(name, "no error", "CutError")
        except cutter.CutError as e:
            check(f"{name}: {str(e)[:60]}", True, True)

    err("unclosed marker", lambda q: (q / "app" / "api" / "todos" / "route.ts").write_text(
        ROUTE_TS.replace("  // <<< CUT cut-api-list\n", "")))
    err("undeclared marker", lambda q: (q / "app" / "page.tsx").write_text(
        PAGE_TSX.replace("cut-ui-rows", "cut-nope")))
    err("nested cuts", lambda q: (q / "app" / "api" / "todos" / "route.ts").write_text(
        ROUTE_TS.replace("  body = await store.all()",
                         "  // >>> CUT cut-ui-rows\n  const x = 1\n  // <<< CUT cut-ui-rows")))
    err("declared cut missing from code", lambda q: (q / "app" / "page.tsx").write_text(
        "export default function Page() { return null }\n"))


def test_return_safety(tmp: Path) -> None:
    """The defect that recurred across consecutive projects.

    recipe-box round 1 had six cuts that removed their function's only return;
    tip-split round 1 then did it again in both route handlers. The skeleton
    does not compile - no red test, no build at all. tsc catches it but FAILS
    OPEN with no node_modules, which is every fresh clone, so this check needs
    no toolchain.
    """
    print("cut return safety - TS2355")
    hints = {k: {"hint": "h", "file": "f", "session": 1}
             for k in ("cut-api-list", "cut-ui-rows", "cut-a")}

    def scan(code: str, name: str = "f.ts") -> list[dict]:
        d = tmp / re.sub(r"\W", "_", name + code[:24])
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(code)
        return cutter.scan_return_safety(d, hints)

    check("a cut holding the only return is flagged", len(scan(ROUTE_TS_BAD)), 1)
    check("the declared return type is noticed",
          scan(ROUTE_TS_BAD)[0]["declared_return_type"], True)
    check("declare-above / assign-inside is clean", scan(ROUTE_TS), [])
    check("a JSX block inside an outer return is clean", scan(PAGE_TSX, "page.tsx"), [])
    check("an arrow function with the only return inside a cut is flagged",
          len(scan("const f = (id: string): X | null => {\n"
                   "  // >>> CUT cut-a\n  return find(id)\n  // <<< CUT cut-a\n}\n")), 1)
    check("a second return outside the cut is enough",
          scan("export function f(): number {\n"
               "  // >>> CUT cut-a\n  return 1\n  // <<< CUT cut-a\n  return 0\n}\n"), [])
    check("a cut with no return at all is clean",
          scan("export function f(): void {\n"
               "  // >>> CUT cut-a\n  doIt()\n  // <<< CUT cut-a\n}\n"), [])

    # and the cutter refuses to generate a skeleton from it
    q = make_project(tmp / "bad", route=ROUTE_TS_BAD)
    try:
        cutter.cut(q)
        check("cut() refuses the TS2355 shape", "no error", "CutError")
    except cutter.CutError as e:
        check("cut() refuses the TS2355 shape", "only return" in str(e), True)
        check("cut() names the fix pattern", "OUTSIDE the markers" in str(e), True)
    check("no skeleton is left behind after the refusal",
          (q / "skeleton" / "api" / "todos" / "route.ts").exists(), False)

    # the fail-open is now visible instead of silent
    r = make_project(tmp / "failopen")
    cutter.cut(r)
    tc = json.loads((r / "skeleton" / ".cut-manifest.json").read_text())["typecheck"]
    check("a typecheck that could not run is marked fail_open", tc.get("fail_open"), True)


def test_skeleton_check(tmp: Path) -> None:
    print("skeleton check")
    p = make_project(tmp / "skelcheck")
    cutter.cut(p)

    def run(results: dict) -> dict:
        (p / "skeleton-results.json").write_text(json.dumps({"criteria": results}))
        return cutter.verify(p)

    check("cut criteria fail and given criterion passes",
          run({"c-1-1": {"status": "fail"}, "c-1-2": {"status": "fail"},
               "c-1-3": {"status": "pass"}})["ok"], True)
    check("cut left a working implementation behind is caught",
          run({"c-1-1": {"status": "pass"}, "c-1-2": {"status": "fail"},
               "c-1-3": {"status": "pass"}})["mismatches"],
          [{"criterion": "c-1-1", "expected": "fail", "actual": "pass"}])
    check("cut took away given code is caught",
          run({"c-1-1": {"status": "fail"}, "c-1-2": {"status": "fail"},
               "c-1-3": {"status": "fail"}})["mismatches"],
          [{"criterion": "c-1-3", "expected": "pass", "actual": "fail"}])
    check("a criterion with no test at all is caught",
          run({"c-1-1": {"status": "fail"}, "c-1-2": {"status": "fail"}})["ok"], False)

    # the blind spot is reported instead of living only in a lesson file
    rep = run({"c-1-1": {"status": "fail"}, "c-1-2": {"status": "fail"},
               "c-1-3": {"status": "pass"}})
    check("no partial-state risk on a clean spec", rep["partial_state_risks"], [])
    check("the typecheck fail-open is carried into the gate 3 report",
          rep["typecheck_fail_open"], True)

    shared = json.loads(json.dumps(GOOD_SPEC))
    for c in shared["sessions"][0]["criteria"][:2]:
        c["cuts"] = ["cut-api-list", "cut-ui-rows"]
    check("cuts sharing a grading signature are reported as a partial-state risk",
          cutter.partial_state_risks(shared),
          [{"cuts": ["cut-api-list", "cut-ui-rows"],
            "graded_only_by": ["c-1-1", "c-1-2"]}])


# ------------------------------------------------------------------ gate 1 ---
def test_gate1(tmp: Path) -> None:
    """The stopping rule. 'Reject until blocking == 0' never terminated - the
    Spec Breaker returned something blocking on all five passes it ever made."""
    print("gate 1 stopping rule")
    os.environ["GP_ROOT"] = str(tmp / "gate1")
    p = make_project(tmp / "gate1")

    def run(md: str, bind: bool = True) -> dict:
        (p / "ambiguity.md").write_text(md)
        meta = p / ".pipeline" / "ambiguity-meta.json"
        if bind:
            meta.write_text(json.dumps({"spec_hash": spec_hash(p)}))
        else:
            meta.unlink(missing_ok=True)
        return gate1.check(p)

    check("every blocking finding owned by a checker is approve-eligible",
          run(AMBIGUITY_MD)["ok"], True)
    check("a worth-a-look finding owned by nothing does not block",
          run(AMBIGUITY_MD)["counts"]["worth_a_look"], 1)

    unowned = AMBIGUITY_MD.replace("- **Owner:** test-runner", "- **Owner:** nothing")
    r = run(unowned)
    check("a blocking finding owned by nothing is a reject", r["ok"], False)
    check("the reject names the finding", "A1" in " ".join(r["reasons"]), True)

    missing = AMBIGUITY_MD.replace("- **Owner:** test-runner\n", "")
    r = run(missing)
    check("a blocking finding with no owner fails closed", r["ok"], False)
    check("an unparseable owner is treated as nothing",
          run(AMBIGUITY_MD.replace("- **Owner:** test-runner",
                                   "- **Owner:** vibes"))["ok"], False)

    check("findings are parsed with their ids and sections",
          [(f["id"], f["blocking"]) for f in gate1.classify(
              gate1.parse_findings(AMBIGUITY_MD))],
          [("A1", True), ("B1", False)])
    check("the rule is recorded in the report",
          "downstream" in run(AMBIGUITY_MD)["rule"], True)

    # a person may still overrule the rule, but only deliberately and on record
    st = State("fixture", root=tmp / "gate1")
    (p / "lint.json").write_text(json.dumps({"ok": True, "errors": []}))
    run(AMBIGUITY_MD.replace("- **Owner:** test-runner", "- **Owner:** nothing"))
    check("the rule blocks approval by default",
          any("stopping rule" in b for b in cli._gate_blockers(st, 1)), True)
    check("--override lifts it",
          any("stopping rule" in b for b in cli._gate_blockers(st, 1, override=True)), False)
    check("--override does not lift the linter",
          ((p / "lint.json").write_text(json.dumps({"ok": False, "errors": []})),
           any("linter" in b for b in cli._gate_blockers(st, 1, override=True)))[1], True)
    (p / "lint.json").write_text(json.dumps({"ok": True, "errors": []}))

    # B-04: a report on disk is not evidence it reviewed the spec on disk
    check("an unbound report is stale (recipe-box round 3)",
          run(AMBIGUITY_MD, bind=False)["ok"], False)
    r = run(AMBIGUITY_MD)
    (p / "spec.md").write_text(GOOD_MD + "\nan edit after the review\n")
    r2 = gate1.check(p)
    check("a report bound to an older spec is stale", r2["ok"], False)
    check("the staleness message names both hashes",
          "stale" in " ".join(r2["reasons"]), True)


# ------------------------------------------------------- spec freeze + drift ---
def test_spec_freeze(tmp: Path) -> None:
    """Round 1 built app/ and verify/ against a spec that existed only in the
    working tree, and a finished Spec Writer woke up an hour later and copied a
    rejected round back over the live files."""
    print("spec freeze - gate 1 onwards")
    os.environ["GP_ROOT"] = str(tmp / "freeze")
    p = make_project(tmp / "freeze")
    (p / "idea.md").write_text("# Real idea\n")
    with contextlib.redirect_stdout(io.StringIO()):
        spec_linter.main(["", str(p)])
    (p / "ambiguity.md").write_text(AMBIGUITY_MD)
    (p / ".pipeline" / "ambiguity-meta.json").write_text(
        json.dumps({"spec_hash": spec_hash(p)}))

    check("nothing is frozen before gate 1", frozen_hash(p), None)
    check("no drift to report before gate 1", spec_drift(p), None)

    ns = argparse.Namespace(slug="fixture", n=1, decision="approve",
                            note="all findings owned downstream", override=False)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.cmd_gate(ns)
    h = spec_hash(p)
    check("gate 1 approval freezes the spec", frozen_hash(p), h)
    check("gate 1 approval archives the approved bytes",
          sorted(x.name for x in (p / ".pipeline" / "approved").iterdir()),
          ["APPROVED", "ambiguity.md", "gate1.json", "lint.json", "spec.json", "spec.md"])
    check("the hash is recorded on the gate decision",
          State("fixture", root=tmp / "freeze").data["gates"]["gate1"]["spec_hash"], h)
    check("an unchanged spec has no drift", spec_drift(p), None)

    (p / "spec.json").write_text(json.dumps(GOOD_SPEC) + "\n")
    drift = spec_drift(p)
    check("an edit after approval is drift", bool(drift), True)
    check("the drift message points at the archive", ".pipeline/approved" in drift, True)

    # and every phase after gate 1 refuses to run
    st = State("fixture", root=tmp / "freeze")
    st.record_gate("gate2", True, "so the pack phase reaches the drift check")
    for phase in ("code", "pack"):
        try:
            cli._guard(st, phase)
            check(f"phase '{phase}' refuses to run on a drifted spec", "ran", "SystemExit")
        except SystemExit as e:
            check(f"phase '{phase}' refuses to run on a drifted spec",
                  "changed since Gate 1" in str(e), True)

    # the write guard refuses the spec with no LOCK at all
    def hook(path: Path) -> bool:
        r = subprocess.run([sys.executable, "-m", "pipeline.guard"],
                           input=json.dumps({"tool_name": "Write",
                                             "tool_input": {"file_path": str(path)}}),
                           capture_output=True, text=True, cwd=ROOT)
        return r.returncode == 2

    check("a frozen spec.json is refused with no lock set", hook(p / "spec.json"), True)
    check("a frozen spec.md is refused with no lock set", hook(p / "spec.md"), True)
    check("app/ is still writable while the spec is frozen",
          hook(p / "app" / "page.tsx"), False)

    # revise reopens it
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_revise(argparse.Namespace(slug="fixture"))
    check("revise clears the freeze", frozen_hash(p), None)
    check("revise archives gate1.json with the round",
          (p / ".pipeline" / "round-1" / "gate1.json").exists(), True)


# ------------------------------------------------------------ breaker binding ---
def test_breaker_binding(tmp: Path) -> None:
    """recipe-box: round 2's report was copied back over a round-3 spec, and
    `pipeline next` reported Gate 1 for a spec the Breaker had never read."""
    print("spec-breaker binding")
    root = tmp / "bind"
    os.environ["GP_ROOT"] = str(root)
    p = make_project(root)
    (p / "idea.md").write_text("# Real idea\n")
    with contextlib.redirect_stdout(io.StringIO()):
        spec_linter.main(["", str(p)])
    ns = argparse.Namespace(slug="fixture", mode="begin")

    (p / "ambiguity.md").write_text("# a stale report copied back in\n")
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_breaker(ns)
    check("begin clears any report left on disk", (p / "ambiguity.md").exists(), False)
    check("begin records the spec it opened against",
          json.loads((p / ".pipeline" / "breaker-begin.json").read_text())["spec_hash"],
          spec_hash(p))

    (p / "ambiguity.md").write_text(AMBIGUITY_MD)
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_breaker(argparse.Namespace(slug="fixture", mode="end"))
    check("end binds the report to the spec",
          json.loads((p / ".pipeline" / "ambiguity-meta.json").read_text())["spec_hash"],
          spec_hash(p))
    check("a bound report satisfies the gate 1 rule", gate1.check(p)["ok"], True)

    # the spec must not move while the Breaker is reading
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_breaker(ns)
    (p / "ambiguity.md").write_text(AMBIGUITY_MD)
    (p / "spec.md").write_text(GOOD_MD + "\nedited mid-pass\n")
    try:
        cli.cmd_breaker(argparse.Namespace(slug="fixture", mode="end"))
        check("end refuses when the spec moved mid-pass", "ran", "SystemExit")
    except SystemExit as e:
        check("end refuses when the spec moved mid-pass", "changed during" in str(e), True)

    # and `next` no longer reports the gate for a spec the Breaker never read
    (p / ".pipeline" / "ambiguity-meta.json").write_text(
        json.dumps({"spec_hash": "0" * 64}))
    with contextlib.redirect_stdout(io.StringIO()):
        spec_linter.main(["", str(p)])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.cmd_next(argparse.Namespace(slug="fixture"))
    check("next sends a stale report back to step 3",
          json.loads(buf.getvalue())["step"], 3)

    # ...but not once Gate 1 has approved. Both round-1 projects were approved
    # before the binding existed, and re-checking it walked them, shipped, back
    # to step 3. After approval the freeze and the archive are the guarantee.
    st = State("fixture", root=root)
    st.record_gate("gate1", True, "approved before the binding existed")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.cmd_next(argparse.Namespace(slug="fixture"))
    check("an approved project is not walked back over an unbound report",
          json.loads(buf.getvalue())["step"], 6)


# ------------------------------------------------------------- state + churn ---
def test_state(tmp: Path) -> None:
    print("gates and retries")
    os.environ["GP_ROOT"] = str(tmp)
    (tmp / "projects" / "gates").mkdir(parents=True, exist_ok=True)
    legacy_state(tmp / "projects" / "gates", "gates")
    st = State("gates", root=tmp)
    check("flow 1 is what a state file without a flow key means", st.flow, 1)
    check("phase 1 needs no gate", st.may_enter("spec")[0], True)
    check("phase 2 is blocked before gate 1", st.may_enter("code")[0], False)
    st.record_gate("gate1", True)
    check("phase 2 opens after gate 1", st.may_enter("code")[0], True)
    check("phase 3 is still blocked", st.may_enter("pack")[0], False)
    st.record_gate("gate2", False, "criteria c-2-1 failing")
    check("a rejected gate does not open the next phase", st.may_enter("pack")[0], False)

    for i in range(RETRY_LIMIT - 1):
        st.burn_retry("code", f"attempt {i}")
    check(f"not exhausted at {RETRY_LIMIT - 1}", st.exhausted("code"), False)
    check("no ticket yet", st.data["ticket"], None)
    st.burn_retry("code", "last error text")
    check(f"exhausted at {RETRY_LIMIT} - rule 6", st.exhausted("code"), True)
    check("ticket raised with the last error", st.data["ticket"]["last_error"], "last error text")


def test_step_churn(tmp: Path) -> None:
    """burn_retry only fires when a checker FAILS, so recipe-box logged 10 clean
    lint runs and 6 clean test runs with retries still showing 0/15."""
    print("green churn - the other half of rule 6")
    os.environ["GP_ROOT"] = str(tmp / "churn")
    (tmp / "churn" / "projects" / "spin" / ".pipeline").mkdir(parents=True, exist_ok=True)
    legacy_state(tmp / "churn" / "projects" / "spin", "spin")
    st = State("spin", root=tmp / "churn")
    check("a green step is counted", (st.log_step("lint", True), st.runs_of("lint"))[1], 1)
    check("nothing is wrong at one run", st.churning(), None)
    for _ in range(STEP_RUN_LIMIT - 2):
        st.log_step("lint", True)
    check(f"still fine at {STEP_RUN_LIMIT - 1} green runs", st.churning(), None)
    st.log_step("lint", True)
    check(f"a loop is caught at {STEP_RUN_LIMIT} green runs", bool(st.churning()), True)
    check("retries were never burned - the checker never failed",
          st.data["retries"]["spec"], 0)
    try:
        cli._guard(st, "spec")
        check("the phase is blocked on churn", "ran", "SystemExit")
    except SystemExit as e:
        check("the phase is blocked on churn", "is a loop" in str(e), True)
    check("a ticket is raised for the churn", bool(st.data.get("ticket")), True)


# ------------------------------------------------------------------- guard ----
def test_guard(tmp: Path) -> None:
    print("write guard - rule 3")
    p = make_project(tmp / "guard")

    def hook(event: dict) -> bool:
        r = subprocess.run([sys.executable, "-m", "pipeline.guard"], input=json.dumps(event),
                           capture_output=True, text=True, cwd=ROOT)
        return r.returncode == 2

    w = lambda path: {"tool_name": "Write", "tool_input": {"file_path": str(path)}}
    b = lambda cmd: {"tool_name": "Bash", "tool_input": {"command": cmd}}

    (p / ".pipeline" / "LOCK").write_text("app\n")
    check("builder may write app/", hook(w(p / "app" / "page.tsx")), False)
    check("builder may not write verify/", hook(w(p / "verify" / "test_api.py")), True)
    check("builder may not edit the settled spec", hook(w(p / "spec.json")), True)
    check("builder may not shell around it", hook(b(f"rm {p / 'verify' / 'test_api.py'}")), True)
    check("builder may still run a build", hook(b(f"cd {p / 'app'} && npm run build")), False)

    (p / ".pipeline" / "LOCK").write_text("verify\n")
    check("verifier may write verify/", hook(w(p / "verify" / "test_api.py")), False)
    check("verifier may not write app/", hook(w(p / "app" / "page.tsx")), True)

    (p / ".pipeline" / "LOCK").unlink()
    check("no lock, no restriction", hook(w(p / "verify" / "test_api.py")), False)
    # flow 2 writes the tests at step 5, before Gate 1, so locking verify/ must
    # not demand the gate that comes after it
    check("flow 1 puts verify/ in the code phase",
          cli.LOCK_PHASE_BY_FLOW[1]["verify"], "code")
    check("flow 2 puts verify/ in the spec phase",
          cli.LOCK_PHASE_BY_FLOW[2]["verify"], "spec")
    check("files outside projects/ are never guarded", hook(w(ROOT / "Flow.md")), False)

    # A read is not a write. The bash check used to scan EVERY path token as
    # soon as a ">" appeared anywhere on the line - quoted or not - so simply
    # looking inside a frozen project was refused. It fired twice in a real run.
    (p / ".pipeline" / guard.FROZEN_MARKER).write_text("abc123def456\n")
    check("a quoted > is data, not a redirect",
          hook(b(f'grep ">>> CUT" {p / "app" / "page.tsx"} {p / "spec.json"}')), False)
    check("reading the frozen spec is allowed",
          hook(b(f"cat {p / 'spec.json'} | head -40")), False)
    check("copying it out to read is allowed",
          hook(b(f"cp {p / 'spec.json'} /tmp/look.json")), False)
    check("but writing over the frozen spec is still refused",
          hook(b(f"echo x > {p / 'spec.json'}")), True)
    check("and so is deleting it",
          hook(b(f"rm -f {p / 'spec.json'}")), True)
    (p / ".pipeline" / guard.FROZEN_MARKER).unlink()

    (p / ".pipeline" / "LOCK").write_text("app\n")
    check("a redirect into a locked tree is a write",
          hook(b(f"npm run build > {p / 'verify' / 'log.txt'}")), True)
    check("the same path only read is not",
          hook(b(f"npm run build < {p / 'verify' / 'log.txt'}")), False)
    check("cp writes its destination",
          hook(b(f"cp /tmp/t.py {p / 'verify' / 't.py'}")), True)
    check("cp only reads its source",
          hook(b(f"cp {p / 'verify' / 't.py'} /tmp/t.py")), False)
    # a second line is a second command; scanning the line as one string missed it
    check("a write on the second line of a script still counts",
          hook(b(f"cd {p / 'app'}\nrm {p / 'verify' / 't.py'}")), True)
    (p / ".pipeline" / "LOCK").unlink()

    # The path pattern once required a forward slash, so on Windows - where the
    # command carries a drive letter and backslashes - it matched nothing and
    # rule 3 went unenforced for EVERY Bash call. Pin both separators and Git
    # Bash's MSYS form here, because the machine running the suite only ever
    # exercises its own.
    check("a forward-slash path is a write target",
          guard.write_targets("rm /repo/projects/fixture/verify/t.py"),
          ["/repo/projects/fixture/verify/t.py"])
    check("a backslash path is a write target too",
          guard.write_targets(r"rm C:\repo\projects\fixture\verify\t.py"),
          [r"C:\repo\projects\fixture\verify\t.py"])
    check("the MSYS drive form is rewritten to a drive",
          guard.MSYS_PATH.sub(r"\1:/", "/d/repo/projects/fixture/verify/t.py"),
          "d:/repo/projects/fixture/verify/t.py")


# ------------------------------------------------------------------ revise ----
def test_revise(tmp: Path) -> None:
    """`revise` archives the rejected round and leaves nothing behind that would
    make `next` still report the spec as waiting at gate 1."""
    print("revise archives the rejected round")
    os.environ["GP_ROOT"] = str(tmp)
    d = tmp / "projects" / "rev"
    (d / ".pipeline").mkdir(parents=True, exist_ok=True)
    (d / "idea.md").write_text("# Real idea\n")
    (d / "spec.md").write_text("# spec\n")
    (d / "spec.json").write_text('{"slug": "rev"}\n')
    (d / "lint.json").write_text('{"ok": true, "error_count": 0, "errors": []}\n')
    (d / "ambiguity.md").write_text("# ambiguity\n")
    legacy_state(d, "rev")
    st = State("rev", root=tmp)
    st.record_gate("gate1", False, "three blocking findings")
    st.save()

    ns = argparse.Namespace(slug="rev")
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_revise(ns)

    r1 = d / ".pipeline" / "round-1"
    check("round-1 holds the rejected spec", (r1 / "spec.json").exists(), True)
    check("round-1 records why", "rejected" in (r1 / "why.md").read_text(), True)
    check("the stale lint.json is gone", (d / "lint.json").exists(), False)
    check("the stale ambiguity.md is gone", (d / "ambiguity.md").exists(), False)
    check("the rejected spec.md is gone", (d / "spec.md").exists(), False)
    check("gate1 is reset", State("rev", root=tmp).gate_passed("gate1"), False)

    # the bug this test exists for: `revise` says "back to step 2", so `next`
    # must agree instead of pointing at the gate the round was just rejected at.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.cmd_next(ns)
    check("next agrees - back to step 2", json.loads(buf.getvalue())["step"], 2)

    # a second rejection archives to round-2, not back over round-1
    (d / "spec.json").write_text('{"slug": "rev2"}\n')
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_revise(ns)
    check("a second rejection makes round-2", (d / ".pipeline" / "round-2").exists(), True)
    check("round-1 survives it", (r1 / "spec.json").read_text().strip(), '{"slug": "rev"}')


def test_revise_flow2(tmp: Path) -> None:
    """Flow 2 writes the tests at step 5, BEFORE gate 1, so a rejected round
    leaves a suite written against the spec being archived.

    Step 5 completes on "verify/ exists and redfirst.json is ok" with no hash
    binding, so leaving them behind marked step 5 done for the NEXT round: the
    tests were never rewritten and Gate 1 would approve a round-2 spec graded by
    round-1 tests. The findings that force a revise are usually about criteria
    nothing grades, so the criteria the new spec extends are exactly the ones
    whose tests would be missing."""
    print("revise on flow 2 archives the tests too")
    os.environ["GP_ROOT"] = str(tmp)
    d = tmp / "projects" / "rev2"
    (d / ".pipeline").mkdir(parents=True, exist_ok=True)
    (d / "idea.md").write_text("# Real idea\n")
    (d / "spec.md").write_text("# spec\n")
    (d / "spec.json").write_text('{"slug": "rev2"}\n')
    (d / "lint.json").write_text('{"ok": true, "error_count": 0, "errors": []}\n')
    (d / "ambiguity.md").write_text("# ambiguity\n")
    (d / "verify").mkdir(exist_ok=True)
    (d / "verify" / "test_c_2_3.py").write_text("def test(): assert 1\n")
    (d / "redfirst.json").write_text('{"ok": true, "vacuous_tests": []}\n')
    legacy_state(d, "rev2")
    st = State("rev2", root=tmp)
    st.data["flow"] = 2
    st.data["phase"] = "spec"
    st.data["retries"] = {ph: 0 for ph in st.phases}
    st.data["gates"] = {g: None for g in st.gates.values()}
    st.record_gate("gate1", False, "B1 is owned by nothing")
    st.save()

    check("before revise, step 5 reads complete",
          dict(cli._flow2_checks(State("rev2", root=tmp)))[5], True)

    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_revise(argparse.Namespace(slug="rev2"))

    r1 = d / ".pipeline" / "round-1"
    check("the round-1 tests are archived", (r1 / "verify" / "test_c_2_3.py").exists(), True)
    check("verify/ is gone from the project", (d / "verify").exists(), False)
    check("the stale redfirst.json is gone", (d / "redfirst.json").exists(), False)
    check("so step 5 no longer reads complete",
          dict(cli._flow2_checks(State("rev2", root=tmp)))[5], False)
    check("and the round-1 spec is archived beside them",
          (r1 / "spec.json").exists(), True)

    # flow 1 writes the tests at step 6, AFTER gate 1, so a flow-1 revise must
    # not reach for a verify/ that belongs to an approved round
    e = tmp / "projects" / "rev1"
    (e / ".pipeline").mkdir(parents=True, exist_ok=True)
    (e / "spec.json").write_text('{"slug": "rev1"}\n')
    (e / "verify").mkdir(exist_ok=True)
    (e / "verify" / "test_api.py").write_text("def test(): assert 1\n")
    legacy_state(e, "rev1")
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_revise(argparse.Namespace(slug="rev1"))
    check("flow 1 leaves verify/ alone", (e / "verify" / "test_api.py").exists(), True)


# ------------------------------------------------------------ deploy + watch ---
def test_deploy_advisories(tmp: Path) -> None:
    """tip-split shipped next@15.1.6 / CVE-2025-66478 with step 10 green."""
    print("deploy check - install advisories")
    observed = ("added 402 packages in 14s\n"
                "npm warn deprecated foo@1.0.0: use bar\n"
                "next@15.1.6: This version has a security vulnerability, "
                "please upgrade. CVE-2025-66478\n")
    check("the advisory tip-split shipped is found", len(find_advisories(observed)), 1)
    check("the matched line is reported verbatim",
          "CVE-2025-66478" in find_advisories(observed)[0], True)
    check("a clean install reports nothing",
          find_advisories("added 31 packages in 2s\nup to date, audited 42 packages"), [])
    check("an npm audit summary is found",
          len(find_advisories("found 3 vulnerabilities (1 moderate, 2 high)")), 1)
    check("a deprecation notice on its own is not an advisory",
          find_advisories("npm warn deprecated inflight@1.0.6: this is not supported"), [])


def test_watchdog(tmp: Path) -> None:
    """One broken project used to take the whole nightly run down with it, and
    the report never said what it had not checked."""
    print("nightly watchdog")
    root = tmp / "watch"
    (root / "projects").mkdir(parents=True)
    for name in ("alpha", "beta"):
        d = root / "projects" / name
        (d / ".pipeline").mkdir(parents=True)
        (d / ".pipeline" / "SHIPPED").write_text("2026-08-27\n")
    (root / "projects" / "gamma" / ".pipeline").mkdir(parents=True)   # not shipped

    check("only shipped projects are picked up",
          [p.name for p in watchdog.shipped(root)], ["alpha", "beta"])

    real = watchdog.test_runner.main

    def boom(argv):
        if "alpha" in argv[0]:
            raise RuntimeError("venv could not be created")
        Path(argv[0], "watchdog-results.json").write_text(json.dumps(
            {"criteria": {"c-1-1": {"status": "pass"}}, "counts": {"pass": 1, "fail": 0}}))
        return 0

    watchdog.test_runner.main = boom
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = watchdog.main(["--root", str(root)])
    finally:
        watchdog.test_runner.main = real

    rep = json.loads((root / "projects" / "watchdog-latest.json").read_text())
    check("a project that raises does not take the run down", rc, 1)
    check("both projects were still attempted", rep["checked"], 2)
    check("the shipped total is reported", rep["shipped_total"], 2)
    check("the broken one is named", [r["slug"] for r in rep["broken"]], ["alpha"])
    check("the error is recorded", "venv could not be created" in rep["runs"][0]["error"], True)
    check("the healthy one still passed", rep["runs"][1]["ok"], True)

    watchdog.test_runner.main = boom
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            watchdog.main(["--root", str(root), "--only", "beta"])
    finally:
        watchdog.test_runner.main = real
    rep = json.loads((root / "projects" / "watchdog-latest.json").read_text())
    check("--only records what it skipped", rep["skipped"], ["alpha"])
    with contextlib.redirect_stdout(io.StringIO()):
        watchdog.main(["--root", str(root), "--only", "nope"])
    rep = json.loads((root / "projects" / "watchdog-latest.json").read_text())
    check("an unknown slug is reported, not silently ignored", rep["unknown_slugs"], ["nope"])


# ------------------------------------------------------- code checks ---------
def test_code_checks(tmp: Path) -> None:
    """habit-tracker Gate 1 round 3, B3: "date arithmetic must give the same
    answer in every timezone" was called make-or-break in the idea and nothing
    could assert it - the Verifier cannot change the server's TZ. The suggested
    resolution was a person reading lib/week.ts at Gate 3. A person reading code
    at Gate 3 is what this pipeline exists to avoid, and the rule is statically
    checkable, so it is a check.
    """
    print("named code checks")
    root = tmp / "app" / "lib"
    root.mkdir(parents=True)
    (root / "bad.ts").write_text(
        "export function weekDates(t: string): string[] {\n"
        "  const d = new Date(t)\n"
        "  d.setDate(d.getDate() - d.getDay() + 1)\n"
        "  return build(d)\n"
        "}\n")
    v = code_check.check_utc_dates(root.parent)
    check("the round-3 Monday bug is flagged", len(v), 3)
    check("the fix names the UTC counterpart",
          sorted({x["fix"] for x in v}),
          ["use .getUTCDate() instead", "use .getUTCDay() instead",
           "use .setUTCDate() instead"])

    (root / "bad.ts").write_text(
        "export function weekDates(t: string): string[] {\n"
        "  const d = new Date(t)\n"
        "  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7))\n"
        "  return build(d)\n"
        "}\n")
    check("the correct UTC version is clean", code_check.check_utc_dates(root.parent), [])

    (root / "bad.ts").write_text("const today = new Date()\nconst t = Date.now()\n")
    v = code_check.check_utc_dates(root.parent)
    check("reading the real clock is flagged", len(v), 2)
    check("both clock reads are named",
          sorted(x["found"] for x in v), ["Date.now()", "new Date()"])

    (root / "bad.ts").write_text(
        "// never call d.getDay() here\nconst s = \"getDay()\"\nconst u = `getDay()`\n")
    check("comments and string bodies do not count",
          code_check.check_utc_dates(root.parent), [])

    # opt-in: a spec that declares nothing runs nothing
    proj = make_project(tmp / "optin")
    (proj / "app" / "lib").mkdir(parents=True, exist_ok=True)
    (proj / "app" / "lib" / "week.ts").write_text("const d = new Date().getDay()\n")
    r = code_check.run(proj, "app")
    check("a spec declaring no code checks passes", (r["ok"], r["checks"]), (True, {}))

    spec = json.loads(json.dumps(GOOD_SPEC))
    spec["code_checks"] = ["utc-dates"]
    (proj / "spec.json").write_text(json.dumps(spec))
    r = code_check.run(proj, "app")
    check("a declared check runs and fails on the violation", r["ok"], False)
    check("the failure names the rule", "utc-dates" in r["checks"], True)
    check("the violation count is reported", r["checks"]["utc-dates"]["count"], 2)

    (proj / "app" / "lib" / "week.ts").write_text(
        "const d = new Date(t).getUTCDay()\n")
    check("and passes once the code is fixed", code_check.run(proj, "app")["ok"], True)

    # the linter refuses a check that does not exist
    spec["code_checks"] = ["no-such-check"]
    (proj / "spec.json").write_text(json.dumps(spec))
    check("the linter rejects an unknown code check",
          "E120" in {e["code"] for e in lint_spec(proj).errors}, True)
    spec["code_checks"] = ["utc-dates"]
    (proj / "spec.json").write_text(json.dumps(spec))
    check("and accepts a known one",
          "E120" in {e["code"] for e in lint_spec(proj).errors}, False)


# ------------------------------------------------------- flow 2 --------------
IDEA_PAGE = ("# Idea {n} - a small board app\n\n"
             "## Theme\nA one page board that lists things and lets the learner "
             "toggle a state on each row, so the session teaches state and a "
             "route handler together in one place.\n\n"
             "## Scope\n- one screen that lists rows\n- one endpoint that reads them\n"
             "- one endpoint that toggles a row and writes it back to disk\n\n"
             "## Out of scope\n- accounts, editing the list, anything on a schedule\n\n"
             "## Why it fits\nIt fits the stack, it fits three sessions of forty "
             "minutes, and every session ends with something that runs.\n")


def test_flow2(tmp: Path) -> None:
    """requirements_doc.md: stack -> 5 ideas -> Gate 0 -> tests before code ->
    mutation -> leak scan -> guide lint -> timed dry run -> Gate 3 -> feedback."""
    print("flow 2 - requirements_doc.md")
    root = tmp / "f2"
    os.environ["GP_ROOT"] = str(root)
    (root / "projects").mkdir(parents=True)

    # --- new --flow 2
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_new(argparse.Namespace(slug="acme", flow=2))
    d = root / "projects" / "acme"
    st = State("acme", root=root)
    check("new --flow 2 records the flow", st.flow, 2)
    check("and starts in the idea phase", st.data["phase"], "idea")
    check("and scaffolds ideas/", (d / "ideas").exists(), True)
    check("and does NOT invent an idea", (d / "idea.md").exists(), False)
    check("the spec phase is blocked until gate 0", st.may_enter("spec")[0], False)
    check("gate0 is the gate that blocks it", "gate0" in st.may_enter("spec")[1], True)

    # --- flow 1 is untouched by any of this
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_new(argparse.Namespace(slug="legacy", flow=1))
    st1 = State("legacy", root=root)
    check("new --flow 1 still gives the twelve-step project", st1.flow, 1)
    check("with an idea template to write", (root / "projects" / "legacy" / "idea.md").exists(), True)
    check("and no gate in front of its first phase", st1.may_enter("spec")[0], True)

    # --- step 0: the human gives the stack
    ns = argparse.Namespace(slug="acme", stack="next,react,typescript", sessions=3,
                            minutes=40, track="fullstack", limits="no external db", by="me")
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_stack(ns)
    stack = json.loads((d / "stack.json").read_text())
    check("step 0 records the stack the human gave",
          (stack["stack"], stack["sessions"], stack["minutes_per_session"]),
          (["next", "react", "typescript"], 3, 40))

    # --- step 1's checker
    def ideas(rc_only=True, count=5, mutate=None):
        for f in (d / "ideas").glob("idea-*.md"):
            f.unlink()
        for i in range(1, count + 1):
            text = IDEA_PAGE.format(n=i)
            if mutate and i == 1:
                text = mutate(text)
            (d / "ideas" / f"idea-{i:02d}.md").write_text(text)
        with contextlib.redirect_stdout(io.StringIO()):
            return cli.cmd_ideas(argparse.Namespace(slug="acme"))

    check("four ideas is not five", ideas(count=4), 1)
    check("five real ideas pass", ideas(count=5), 0)
    check("a placeholder in an idea is rejected",
          ideas(mutate=lambda t: t + "\nTODO: decide the rest\n"), 1)
    check("a stub instead of a page is rejected",
          ideas(mutate=lambda t: "# Idea 1\n\ntoo short\n"), 1)
    ideas(count=5)

    # --- gates are approved in order (checked before the pick opens gate 0)
    check("gate 1 cannot be approved while gate 0 is open",
          any("gate0 has not been approved" in b
              for b in cli._gate_blockers(State("acme", root=root), 1)), True)

    # --- GATE 0: the human picks, the AI does not
    try:
        cli.cmd_pick(argparse.Namespace(slug="acme", n=9, note=""))
        check("picking an idea that does not exist is refused", "ran", "SystemExit")
    except SystemExit as e:
        check("picking an idea that does not exist is refused", "does not exist" in str(e), True)
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_pick(argparse.Namespace(slug="acme", n=3, note="fits the stack"))
    st = State("acme", root=root)
    check("gate 0 approves on a pick", st.gate_passed("gate0"), True)
    check("and records which idea was chosen",
          st.data["gates"]["gate0"]["picked"], "idea-03.md")
    check("the chosen idea becomes idea.md", (d / "idea.md").exists(), True)
    check("which is the one that was picked",
          (d / "idea.md").read_text(), (d / "ideas" / "idea-03.md").read_text())
    check("the spec phase opens", State("acme", root=root).may_enter("spec")[0], True)

    # --- gate 1 now also wants the tests, and proof they were red
    (d / "lint.json").write_text(json.dumps({"ok": True, "errors": []}))
    (d / "ambiguity.md").write_text(AMBIGUITY_MD)
    (d / ".pipeline" / "ambiguity-meta.json").write_text(
        json.dumps({"spec_hash": spec_hash(d)}))
    st = State("acme", root=root)
    blockers = cli._gate_blockers(st, 1)
    check("gate 1 refuses without the tests",
          any("verify/ is missing" in b for b in blockers), True)
    (d / "verify").mkdir()
    check("gate 1 refuses without the red-first check",
          any("red-first" in b for b in cli._gate_blockers(st, 1)), True)
    (d / "redfirst.json").write_text(json.dumps({"ok": True}))
    check("and stops asking once both are there",
          [b for b in cli._gate_blockers(st, 1) if "red-first" in b or "verify/" in b], [])

    # a flow-1 project's gate 1 never asks for either
    l = root / "projects" / "legacy"
    (l / "lint.json").write_text(json.dumps({"ok": True, "errors": []}))
    (l / "ambiguity.md").write_text(AMBIGUITY_MD)
    (l / ".pipeline" / "ambiguity-meta.json").write_text(
        json.dumps({"spec_hash": spec_hash(l)}))
    check("flow 1 gate 1 does not require red-first",
          any("red-first" in b for b in cli._gate_blockers(State("legacy", root=root), 1)),
          False)

    # --- gate 2 wants the mutation check
    check("gate 2 refuses without the mutation check",
          any("mutation" in b for b in cli._gate_blockers(st, 2)), True)
    (d / "mutation.json").write_text(json.dumps({"ok": True}))
    check("and stops once it has passed",
          any("mutation" in b for b in cli._gate_blockers(st, 2)), False)

    # --- gate 3 wants the leak scan, the guide linter and the dry run.
    # Gates are approved in order, so the two before it are recorded first.
    st.record_gate("gate1", True, "plan and tests approved")
    st.record_gate("gate2", True, "criteria green")
    st = State("acme", root=root)
    (d / "skeleton-check.json").write_text(json.dumps({"ok": True}))
    (d / "deploy.json").write_text(json.dumps({"ok": True}))
    (d / "pack").mkdir()
    b3 = cli._gate_blockers(st, 3)
    for want in ("leak scan", "guide linter", "dry run"):
        check(f"gate 3 refuses without the {want}", any(want in x for x in b3), True)
    (d / "leak-scan.json").write_text(json.dumps({"ok": True}))
    (d / "guide-lint.json").write_text(json.dumps({"ok": True}))
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_dryrun(argparse.Namespace(slug="acme", session=2, minutes=38,
                                         by="someone else", could_not_teach=False, note=""))
    st = State("acme", root=root)
    check("the dry run is recorded with who taught it",
          (st.data["dry_run"]["by"], st.data["dry_run"]["minutes"]), ("someone else", 38))
    check("gate 3 is satisfied", cli._gate_blockers(st, 3), [])
    try:
        cli.cmd_dryrun(argparse.Namespace(slug="acme", session=2, minutes=38, by="",
                                          could_not_teach=False, note=""))
        check("a dry run with no name is refused", "ran", "SystemExit")
    except SystemExit:
        check("a dry run with no name is refused", True, True)
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_dryrun(argparse.Namespace(slug="acme", session=2, minutes=52,
                                         by="someone else", could_not_teach=True,
                                         note="ran out of time"))
    check("a dry run that could not be taught blocks gate 3",
          any("could NOT be taught" in b
              for b in cli._gate_blockers(State("acme", root=root), 3)), True)

    # --- step 15: feedback re-enters at step 3
    st = State("acme", root=root)
    entry = st.record_feedback("session 2 ran 8 minutes over", session=2, by="instructor")
    check("feedback routes back to step 3", entry["re_enter_at"], 3)
    check("and is kept on the project", len(State("acme", root=root).data["feedback"]), 1)

    # --- rule 7: the ticket says which kind of problem
    st = State("acme", root=root)
    for _ in range(RETRY_LIMIT):
        st.burn_retry("code", "criteria red", kind="spec problem")
    check("a spec problem re-enters at step 3", st.data["ticket"]["re_enter_at"], 3)
    check("and says so", st.data["ticket"]["kind"], "spec problem")
    st.data["retries"]["code"] = 0
    st.data["ticket"] = None
    for _ in range(RETRY_LIMIT):
        st.burn_retry("code", "criteria red")
    check("a code problem stays in the code phase", st.data["ticket"]["re_enter_at"], 7)
    check("and says so", st.data["ticket"]["kind"], "code problem")


def test_flow2_next(tmp: Path) -> None:
    """`next` must walk requirements_doc.md's sixteen steps in order."""
    print("flow 2 - what the pipeline wants next")
    root = tmp / "n2"
    os.environ["GP_ROOT"] = str(root)
    (root / "projects").mkdir(parents=True)
    with contextlib.redirect_stdout(io.StringIO()):
        cli.cmd_new(argparse.Namespace(slug="walk", flow=2))
    d = root / "projects" / "walk"

    def step() -> int:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.cmd_next(argparse.Namespace(slug="walk"))
        return json.loads(buf.getvalue())["step"]

    check("step 0 first - the human gives the stack", step(), 0)
    (d / "stack.json").write_text("{}")
    check("then step 1 - five ideas", step(), 1)
    for i in range(1, 6):
        (d / "ideas" / f"idea-{i:02d}.md").write_text("x")
    check("then step 2 - gate 0", step(), 2)
    st = State("walk", root=root)
    st.record_gate("gate0", True, "picked")
    (d / "idea.md").write_text("# idea\n")
    check("then step 3 - the spec writer", step(), 3)
    (d / "lint.json").write_text(json.dumps({"ok": True}))
    check("then step 4 - the ambiguity check", step(), 4)
    (d / "ambiguity.md").write_text(AMBIGUITY_MD)
    (d / ".pipeline" / "ambiguity-meta.json").write_text(
        json.dumps({"spec_hash": spec_hash(d)}))
    check("then step 5 - the tests, BEFORE the code", step(), 5)
    (d / "verify").mkdir()
    (d / "redfirst.json").write_text(json.dumps({"ok": True}))
    check("then step 6 - gate 1 over the plan and the tests", step(), 6)
    State("walk", root=root).record_gate("gate1", True, "ok")
    check("then step 7 - the builder", step(), 7)
    (d / "app").mkdir()
    (d / "results.json").write_text(json.dumps({"ok": True}))
    check("then step 8 - the verifier, with the mutation check", step(), 8)
    (d / "mutation.json").write_text(json.dumps({"ok": True}))
    check("then step 9 - gate 2", step(), 9)
    State("walk", root=root).record_gate("gate2", True, "ok")
    (d / "skeleton-check.json").write_text(json.dumps({"ok": True}))
    check("then step 10 - the cutter, with the leak scan", step(), 10)
    (d / "leak-scan.json").write_text(json.dumps({"ok": True}))
    (d / "pack").mkdir()
    check("then step 11 - the guide, with the guide linter", step(), 11)
    (d / "guide-lint.json").write_text(json.dumps({"ok": True}))
    check("then step 12 - the deploy check", step(), 12)
    (d / "deploy.json").write_text(json.dumps({"ok": True}))
    check("then step 13 - the timed dry run", step(), 13)
    State("walk", root=root).record_dry_run(1, 39, "someone else", True)
    check("then step 14 - gate 3", step(), 14)
    State("walk", root=root).record_gate("gate3", True, "ok")
    check("then step 15 - ship", step(), 15)
    (d / ".pipeline" / "SHIPPED").write_text("2026-08-28\n")
    check("then nothing - shipped", step(), None)


def test_new_checkers(tmp: Path) -> None:
    """The four checkers requirements_doc.md asks for that had no script."""
    print("red-first, mutation, leak scan, guide linter")

    # --- rule 2: a test that cannot go red
    proj = make_project(tmp / "rf")
    v = proj / "verify"
    (v / "test_good.py").write_text(
        "def test_one(page):\n    assert page.title() == 'Todos'\n")
    (v / "test_empty.py").write_text(
        "def test_two(page):\n    page.goto('/')\n")
    (v / "test_trivial.py").write_text(
        "def test_three(page):\n    assert True\n")
    (v / "test_helper.py").write_text(
        "import pytest\n\ndef test_four(client):\n"
        "    with pytest.raises(ValueError):\n        boom()\n")
    found = {f["test"].split("::")[1]: f["problem"]
             for f in redfirst.scan_assertions(proj)}
    check("a test with a real assertion is fine", "test_one" in found, False)
    check("a test with no assertion is caught", "no assertion" in found.get("test_two", ""), True)
    check("assert True is caught",
          "trivially true" in found.get("test_three", ""), True)
    check("pytest.raises counts as an assertion", "test_four" in found, False)

    # --- rule 3: single-task mutants
    proj = make_project(tmp / "mut")
    spec = json.loads((proj / "spec.json").read_text())
    hints = cutter.load_hints(spec)
    out = tmp / "mut" / "mutant"
    removed = mutation.mutate_one(proj / "app", out, "cut-api-list", hints)
    route = (out / "api" / "todos" / "route.ts").read_text()
    page = (out / "page.tsx").read_text()
    check("the mutated task is removed", "store.all()" in route, False)
    check("and replaced by its TODO", "TODO(cut-api-list)" in route, True)
    check("every other task is left written", "todos.map" in page, True)
    check("and its markers are stripped", ">>> CUT" in page, False)
    check("the removal is counted", removed > 0, True)
    check("graded_by reads the requirement list",
          mutation.graded_by(spec, "cut-ui-rows"), ["c-1-2"])

    # --- rule 6: leaks
    proj = make_project(tmp / "leak")
    cutter.cut(proj)
    r = leak_scan.run(proj, check_history=False)
    check("a clean skeleton has no leaks", (r["ok"], r["leaks"]), (True, []))
    leaked = "body = await store.all()"      # a real answer line of cut-api-list
    (proj / "skeleton" / "README.md").write_text(
        f"# Starter\n\nHint for the impatient:\n\n    {leaked}\n")
    r = leak_scan.run(proj, check_history=False)
    check("an answer line in the README is a leak", r["ok"], False)
    check("and it names the file and the task",
          [(h["file"], h["task"]) for h in r["leaks"]],
          [("README.md", "cut-api-list")])
    (proj / "skeleton" / "README.md").write_text("# Starter\n\nreturn\n}\n")
    check("structural lines are not leaks", leak_scan.run(proj, check_history=False)["ok"], True)

    # --- step 11's checker
    proj = make_project(tmp / "guide")
    cutter.cut(proj)
    g = proj / "pack"
    g.mkdir()
    (g / "session-1.md").write_text(
        "# Session 1\n\n**Time:** 35 minutes\n\n"
        "Cut points: cut-api-list and cut-ui-rows.\n"
        "Criteria c-1-1, c-1-2 and c-1-3.\n\n"
        "```ts\n  body = await store.all()\n```\n")
    r = guide_linter.lint(proj)
    check("a guide that covers everything passes", r["ok"], True)
    check("and reports the session timing", r["sessions"][0]["minutes"], 35)

    (g / "session-1.md").write_text("# Session 1\n\n**Time:** 35 minutes\n")
    check("an unmentioned student task is an error",
          "G020" in {e["code"] for e in guide_linter.lint(proj)["errors"]}, True)
    (g / "session-1.md").write_text(
        "# Session 1\n\nCut points: cut-api-list, cut-ui-rows.\n")
    check("a session with no stated time is an error",
          "G030" in {e["code"] for e in guide_linter.lint(proj)["errors"]}, True)
    (g / "session-1.md").write_text(
        "# Session 1\n\n**Time:** 47 minutes\n\ncut-api-list, cut-ui-rows\n")
    check("an undisclosed overrun is an error",
          "G031" in {e["code"] for e in guide_linter.lint(proj)["errors"]}, True)
    (g / "session-1.md").write_text(
        "# Session 1\n\n**Time:** 47 minutes\n\nThis session does not fit - two "
        "trims below.\n\ncut-api-list, cut-ui-rows\n")
    r = guide_linter.lint(proj)
    check("a disclosed overrun is a warning, not an error",
          ("G031" in {e["code"] for e in r["errors"]},
           "G032" in {w["code"] for w in r["warnings"]}), (False, True))
    (g / "session-1.md").write_text(
        "# Session 1\n\n**Time:** 35 minutes\n\ncut-api-list, cut-ui-rows\n\n"
        "```ts\n  const rows = await database.fetchEverything()\n```\n")
    check("a snippet that is in no source file is an error",
          "G040" in {e["code"] for e in guide_linter.lint(proj)["errors"]}, True)


def test_doc_vocabulary(tmp: Path) -> None:
    """requirements_doc.md's ids and marker form, alongside the existing ones."""
    print("the doc's ids and markers")
    hints = {"S03-T01": {"hint": "Put every habit into `body` and set `status` to 200",
                         "file": "route.ts", "session": 3}}
    doc = ("export async function GET(): Promise<Response> {\n"
           "  let body: unknown = null\n"
           "  let status = 501\n"
           "  # >>> STUDENT S03-T01 START\n"
           "  #     goal: answer with every habit\n"
           "  body = await store.all()\n"
           "  status = 200\n"
           "  # <<< STUDENT S03-T01 END\n"
           "  return Response.json(body, { status })\n"
           "}\n")
    text, applied = cutter.cut_file(Path("route.ts"), doc, hints)
    check("the STUDENT marker form is cut", [a["id"] for a in applied], ["S03-T01"])
    check("the goal line goes with the block", "goal:" in text, False)
    check("the hint from the spec is what the student reads",
          "TODO(S03-T01): Put every habit into `body` and set `status` to 200" in text, True)
    check("the return outside the markers survives",
          "return Response.json(body, { status })" in text, True)

    spec = json.loads(json.dumps(GOOD_SPEC))
    ses = spec["sessions"][0]
    ses["id"] = "S01"
    for i, c in enumerate(ses["criteria"], start=1):
        c["id"] = f"S01-AC{i:02d}"
    ses["cuts"][0]["id"] = "S01-T01"
    ses["cuts"][1]["id"] = "S01-T02"
    ses["criteria"][0]["cuts"] = ["S01-T01"]
    ses["criteria"][1]["cuts"] = ["S01-T02"]
    q = make_project(tmp / "vocab", spec=spec,
                     md=GOOD_MD.replace("c-1-1", "S01-AC01").replace("c-1-2", "S01-AC02")
                     .replace("c-1-3", "S01-AC03").replace("cut-api-list", "S01-T01")
                     .replace("cut-ui-rows", "S01-T02"))
    (q / "app" / "api" / "todos" / "route.ts").write_text(
        ROUTE_TS.replace("cut-api-list", "S01-T01"))
    (q / "app" / "page.tsx").write_text(PAGE_TSX.replace("cut-ui-rows", "S01-T02"))
    lint = lint_spec(q)
    check("the doc's id vocabulary lints clean", lint.errors, [])
    check("a session id that disagrees with n is rejected",
          "E043" in {e["code"] for e in
                     (lambda: (ses.update(id="S07"),
                               (q / "spec.json").write_text(json.dumps(spec)),
                               lint_spec(q))[2])().errors}, True)
    ses["id"] = "S01"
    (q / "spec.json").write_text(json.dumps(spec))
    check("and the cutter cuts them", cutter.cut(q)["count"], 2)


# ------------------------------------------------------- runtime state -------
def test_runtime_state(tmp: Path) -> None:
    """habit-tracker Gate 1 round 3: a project with a mutable file store had no
    way to reset it, and its live copy shipped to the student.

    The test process was handed only BASE_URL with cwd=project, while the same
    suite runs from three different (cwd, verify-location) combinations - so no
    relative path to the app's own files worked for all three. And `data/` is
    correctly not in SKIP_DIRS, because a seed file the student needs lives
    there, so the live store was copied into skeleton/ and into the step-10
    fresh copy alongside it.
    """
    print("runtime state - the app's own files")

    # the runner must tell the test process which target it is testing
    src = (ROOT / "pipeline" / "test_runner.py").read_text()
    check("the test process is told which target it is testing",
          '"APP_DIR": str(target)' in src, True)

    root = tmp / "app"
    (root / "data").mkdir(parents=True)
    (root / ".gitignore").write_text(
        "node_modules\n"
        "data/habits.json\n"
        "!data/habits.seed.json\n"
        "*.log\n"
        "tmp/\n")
    for rel, body in (("data/habits.json", "{}"), ("data/habits.seed.json", "{}"),
                      ("page.tsx", "x"), ("debug.log", "x"),
                      ("tmp/scratch.ts", "x"), ("lib/keep.ts", "x")):
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)

    ig = cutter.gitignore_matcher(root)
    check("a gitignored path is excluded", ig(Path("data/habits.json")), True)
    check("an un-ignored path survives the negation", ig(Path("data/habits.seed.json")), False)
    check("a basename glob is excluded", ig(Path("debug.log")), True)
    check("a directory-only pattern is excluded", ig(Path("tmp/scratch.ts")), True)
    check("an ordinary source file is kept", ig(Path("lib/keep.ts")), False)
    check("no .gitignore means no exclusions",
          cutter.gitignore_matcher(tmp / "nothing-here")(Path("data/habits.json")), False)

    kept = sorted(q.relative_to(root).as_posix() for q in cutter.walk_source(root))
    check("the cutter drops the live store and keeps the seed", kept,
          [".gitignore", "data/habits.seed.json", "lib/keep.ts", "page.tsx"])

    # ...but the return-safety scan must still read every source file, because a
    # gitignored file with a bad cut marker is still a bad cut marker
    (root / "tmp" / "bad.ts").write_text(
        "export function f(): number {\n"
        "  // >>> CUT cut-a\n  return 1\n  // <<< CUT cut-a\n}\n")
    hints = {"cut-a": {"hint": "h", "file": "f", "session": 1}}
    check("the return-safety scan still sees a gitignored source file",
          len(cutter.scan_return_safety(root, hints)), 1)

    # build artifacts never ship, whatever .gitignore says. Both round-1
    # projects carry a stale tsconfig.tsbuildinfo in their skeleton purely
    # because those projects happened to list it themselves.
    (root / "tsconfig.tsbuildinfo").write_text("junk")
    (root / ".DS_Store").write_text("junk")
    kept = sorted(q.relative_to(root).as_posix() for q in cutter.walk_source(root))
    check("a build artifact never reaches the skeleton",
          [k for k in kept if "tsbuildinfo" in k or "DS_Store" in k], [])

    # ...and a sweep afterwards, because step 8's own typecheck and build write
    # artifacts INTO the skeleton after the copy is made. habit-tracker round 4
    # B4: excluding them from the copy alone left them in the shipped skeleton.
    proj = tmp / "sweep"
    (proj / "skeleton" / "node_modules").mkdir(parents=True)
    (proj / "skeleton" / "tsconfig.tsbuildinfo").write_text("generated by tsc")
    (proj / "skeleton" / ".DS_Store").write_text("junk")
    (proj / "skeleton" / "page.tsx").write_text("source")
    (proj / "skeleton" / "node_modules" / "x.tsbuildinfo").write_text("not ours")
    swept = cutter.sweep_generated(proj)
    check("the sweep removes artifacts the checks generated",
          sorted(swept), [".DS_Store", "tsconfig.tsbuildinfo"])
    check("the sweep keeps the source", (proj / "skeleton" / "page.tsx").exists(), True)
    check("the sweep does not reach inside node_modules",
          (proj / "skeleton" / "node_modules" / "x.tsbuildinfo").exists(), True)

    out = tmp / "fresh"
    deploy_check.fresh_copy(root, out)
    copied = sorted(q.relative_to(out).as_posix() for q in out.rglob("*") if q.is_file())
    check("the deploy check's fresh copy drops the live store",
          "data/habits.json" in copied, False)
    check("the deploy check's fresh copy keeps the seed",
          "data/habits.seed.json" in copied, True)
    check("the deploy check's fresh copy drops build artifacts",
          [c for c in copied if "tsbuildinfo" in c or "DS_Store" in c], [])
    # EXCLUDE is a pattern list. Rewriting fresh_copy to take the gitignore
    # matcher had quietly turned its glob match into an equality test.
    check("EXCLUDE still matches as globs, not by equality",
          any("*" in pat for pat in deploy_check.EXCLUDE), True)


# --------------------------------------------------------- relative paths ----
def test_relative_paths(tmp: Path) -> None:
    """The bug the selftest could not see. The test runner passed a relative
    interpreter path while setting cwd=project, so it resolved against the new
    directory and vanished. Every fixture here used an absolute tempdir, so the
    whole class was structurally invisible - and the watchdog builds its paths
    from Path("."), so every scheduled run would have died this way."""
    print("relative project paths")
    root = tmp / "rel"
    p = make_project(root)
    was = Path.cwd()
    try:
        os.chdir(root)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = spec_linter.main(["", "projects/fixture"])
        check("the linter takes a relative project path", rc, 0)
        check("and writes its report where the project is",
              (p / "lint.json").exists(), True)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cutter.main(["", "cut", "projects/fixture"])
        check("the cutter takes a relative project path", rc, 0)
        check("and generates the skeleton in the project",
              (p / "skeleton" / "page.tsx").exists(), True)
        (p / "skeleton-results.json").write_text(json.dumps(
            {"criteria": {"c-1-1": {"status": "fail"}, "c-1-2": {"status": "fail"},
                          "c-1-3": {"status": "pass"}}}))
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cutter.main(["", "verify", "projects/fixture"])
        check("the skeleton check takes a relative project path", rc, 0)
    finally:
        os.chdir(was)

    # every script that takes a path must resolve it before handing it to a
    # subprocess that runs with cwd= somewhere else
    for mod in ("test_runner", "deploy_check", "cutter", "spec_linter", "watchdog"):
        text = (ROOT / "pipeline" / f"{mod}.py").read_text()
        check(f"{mod} resolves the path it is given", ".resolve()" in text, True)


# ------------------------------------------------------------------- docs ----
def test_readme_count() -> None:
    """The README said 45 checks when there were 59. A stale number in the one
    document that tells you whether to trust a change is worth one check."""
    print("docs")
    md = (ROOT / "README.md").read_text()
    m = re.search(r"(\d+)\s+checks on the deterministic core", md)
    check("README states the selftest check count", bool(m), True)
    if m:
        check(f"README's count matches the {CHECKS + 1} checks that ran",
              int(m.group(1)), CHECKS + 1)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="gp-selftest-"))
    try:
        for t in (test_linter, test_cutter, test_return_safety, test_skeleton_check,
                  test_gate1, test_spec_freeze, test_breaker_binding, test_state,
                  test_step_churn, test_guard, test_revise, test_revise_flow2,
                  test_deploy_advisories,
                  test_watchdog, test_code_checks, test_runtime_state,
                  test_relative_paths, test_flow2, test_flow2_next,
                  test_new_checkers, test_doc_vocabulary):
            t(tmp / t.__name__)
        test_readme_count()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("GP_ROOT", None)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} of {CHECKS} FAILED")
        for f in FAILURES:
            print("  " + f)
        return 1
    print(f"all {CHECKS} deterministic-core checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
