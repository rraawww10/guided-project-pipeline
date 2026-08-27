"""Self-test for the deterministic core.

The scripts are the part that must give the same answer every time, so they get
a regression test. No agents, no network, no npm - runs in about a second.

  python -m pipeline.selftest
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import cli, cutter
from .spec_linter import Lint, _scan_placeholder, _scan_vague, lint_spec
from .state import RETRY_LIMIT, State

ROOT = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []


def check(name: str, got, want) -> None:
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
            {"id": "cut-api-list", "file": "app/api/todos/route.ts",
             "hint": "Return every todo from the store as JSON"},
            {"id": "cut-ui-rows", "file": "app/page.tsx",
             "hint": "Render one list item for each todo, showing its title"},
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

ROUTE_TS = """import { store } from "@/lib/store"

export async function GET() {
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


def make_project(tmp: Path, spec: dict = None, md: str = None) -> Path:
    p = tmp / "projects" / "fixture"
    (p / "app" / "api" / "todos").mkdir(parents=True)
    (p / "verify").mkdir()
    (p / ".pipeline").mkdir()
    (p / "spec.json").write_text(json.dumps(spec or GOOD_SPEC, indent=2))
    (p / "spec.md").write_text(md or GOOD_MD)
    (p / "app" / "api" / "todos" / "route.ts").write_text(ROUTE_TS)
    (p / "app" / "page.tsx").write_text(PAGE_TSX)
    return p


def test_linter(tmp: Path) -> None:
    print("spec linter")
    p = make_project(tmp)
    check("clean spec passes", lint_spec(p).errors, [])

    def codes(mutate) -> set[str]:
        spec = json.loads(json.dumps(GOOD_SPEC))
        mutate(spec)
        (p / "spec.json").write_text(json.dumps(spec))
        return {e["code"] for e in lint_spec(p).errors}

    def has(name, mutate, code):
        check(name, code in codes(mutate), True)

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


def test_cutter(tmp: Path) -> None:
    print("cutter")
    p = make_project(tmp)
    out = cutter.cut(p)
    check("both cuts applied", out["count"], 2)
    skel_route = (p / "skeleton" / "api" / "todos" / "route.ts").read_text()
    skel_page = (p / "skeleton" / "page.tsx").read_text()
    check("ts comment style", "  // TODO(cut-api-list): Return every todo from the store as JSON" in skel_route, True)
    check("jsx comment style", "      {/* TODO(cut-ui-rows): Render one list item for each todo, showing its title */}" in skel_page, True)
    check("implementation removed", "store.all()" in skel_route, False)
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
        ROUTE_TS.replace("  const todos = await store.all()",
                         "  // >>> CUT cut-ui-rows\n  const x = 1\n  // <<< CUT cut-ui-rows")))
    err("declared cut missing from code", lambda q: (q / "app" / "page.tsx").write_text(
        "export default function Page() { return null }\n"))


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
    check("files outside projects/ are never guarded", hook(w(ROOT / "Flow.md")), False)


def test_state(tmp: Path) -> None:
    print("gates and retries")
    os.environ["GP_ROOT"] = str(tmp)
    (tmp / "projects" / "gates").mkdir(parents=True, exist_ok=True)
    st = State("gates", root=tmp)
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
    st = State("rev", root=tmp)
    st.record_gate("gate1", False, "three blocking findings")
    st.save()

    ns = argparse.Namespace(slug="rev")
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
    cli.cmd_revise(ns)
    check("a second rejection makes round-2", (d / ".pipeline" / "round-2").exists(), True)
    check("round-1 survives it", (r1 / "spec.json").read_text().strip(), '{"slug": "rev"}')


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="gp-selftest-"))
    try:
        for t in (test_linter, test_cutter, test_skeleton_check, test_guard, test_state,
                  test_revise):
            t(tmp / t.__name__)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("GP_ROOT", None)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED")
        for f in FAILURES:
            print("  " + f)
        return 1
    print("all deterministic-core checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
