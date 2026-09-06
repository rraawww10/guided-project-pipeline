"""Read model for the UI: it derives everything from the pipeline's own files.

Nothing here decides anything. The pipeline's state.json, the checker reports on
disk and the run ledger this module appends to are the only sources; every field
the UI shows is computed from one of those three. There is no mock data path and
no simulated progress - a value the pipeline does not record is reported as
unknown rather than invented.

Three things live here:

* the derivation layer - phases, steps, current execution, artifacts, gates
* the event log        - `.pipeline/ui-events.jsonl`, append-only, back-filled
                         from state.json so a project that predates the UI still
                         has a history
* the run ledger       - `.pipeline/ui-runs.jsonl` plus `.pipeline/ui-logs/`, so
                         what the UI executed survives a server restart

`pipeline/ui_runner.py` executes; `pipeline/orchestrator.py` decides what runs
next; `pipeline/ui.py` serves. All three read this.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .cli import STEPS_BY_FLOW
from .state import PHASES_BY_FLOW, RETRY_LIMIT, STEP_RUN_LIMIT, spec_hash
from .test_runner import BOOT_FAILED_RC

ROOT = Path(os.environ.get("GP_ROOT", Path.cwd())).resolve()
PROJECTS = ROOT / "projects"
STATIC = Path(__file__).with_name("ui_static")

# Live run registry. Persisted per project so a restart does not lose history.
RUNS: dict[str, dict] = {}
RUNS_LOCK = threading.RLock()
EVENT_LOCK = threading.RLock()
_SEQ: dict[str, int] = {}

TEXT_TYPES = {
    ".css", ".csv", ".html", ".js", ".json", ".jsx", ".md", ".py", ".tsx",
    ".ts", ".txt", ".yaml", ".yml", ".cfg", ".toml", ".env", ".sql",
}
ARTIFACT_NAMES = {
    "idea.md", "stack.json", "ideas.json", "lint.json", "gate1.json",
    "redfirst.json", "results.json", "mutation.json", "skeleton-results.json",
    "skeleton-check.json", "deploy.json", "leak-scan.json", "guide-lint.json",
    "watchdog-results.json", "spec.md", "spec.json", "ambiguity.md",
    "coverage.json",
}

# Every deterministic script the UI can run, mapped to the real CLI subcommand.
SCRIPT_COMMANDS = {
    "ideas": {"args": ["ideas"], "phase": "idea",
              "purpose": "Five real idea pages, none a placeholder."},
    "lint": {"args": ["lint"], "phase": "spec",
             "purpose": "spec.md and spec.json against the contract and the teaching rules."},
    "breaker begin": {"args": ["breaker"], "mode": "begin", "phase": "spec",
                      "purpose": "Open a Spec Breaker pass bound to the current spec hash."},
    "breaker end": {"args": ["breaker"], "mode": "end", "phase": "spec",
                    "purpose": "Bind ambiguity.md to the spec hash the breaker actually read."},
    "gate1-check": {"args": ["gate1-check"], "phase": "spec",
                    "purpose": "The Gate 1 stopping rule (rule 8)."},
    "redfirst": {"args": ["redfirst"], "phase": "spec",
                 "purpose": "Prove the tests can fail before any code exists (rule 2)."},
    "test": {"args": ["test"], "phase": "code",
             "purpose": "Run the acceptance suite against app/."},
    "mutation": {"args": ["mutation"], "phase": "code",
                 "purpose": "Prove every student task can turn a requirement red (rule 3)."},
    "cut": {"args": ["cut"], "phase": "pack",
            "purpose": "Generate skeleton/ from the cut markers and check it fails the right tests."},
    "leak": {"args": ["leak"], "phase": "pack",
             "purpose": "No answer line anywhere in the student tree (rule 6)."},
    "guide-lint": {"args": ["guide-lint"], "phase": "pack",
                   "purpose": "The instructor guide has what an instructor needs."},
    "handover-checks": {"args": ["handover-checks"], "phase": "pack",
                        "purpose": "Leak scan and guide linter in one call."},
    "deploy": {"args": ["deploy"], "phase": "pack",
               "purpose": "Fresh install, build and preview link."},
    "spec-status": {"args": ["spec-status"], "phase": "code",
                    "purpose": "Is the spec still the one Gate 1 froze?"},
    "ship": {"args": ["ship"], "phase": "pack",
             "purpose": "Mark an approved project shipped."},
    "watch": {"args": ["watch"], "phase": "pack", "no_slug": True,
              "purpose": "Replay every shipped suite (the watchdog, on demand)."},
}
AGENT_PHASES = {
    "idea-generator": "idea",
    "spec-writer": "spec",
    "spec-breaker": "spec",
    "test-writer": "spec",
    "builder": "code",
    "verifier": "code",
    "pack-writer": "pack",
}
AGENT_STEPS = {
    1: {"idea-generator"}, 3: {"spec-writer"}, 4: {"spec-breaker"},
    5: {"test-writer"}, 7: {"builder"}, 8: {"verifier"}, 11: {"pack-writer"},
}
STEP_AGENT_ALIASES = {"guide-writer": "pack-writer"}
SCRIPT_LABELS = {
    "breaker begin": "Open Breaker Pass",
    "breaker end": "Bind Breaker Report",
    "gate1-check": "Gate 1 Stopping Rule",
    "guide-lint": "Guide Linter",
    "leak": "Leak Scan",
    "redfirst": "Red-First Check",
    "test": "Test Runner",
    "mutation": "Mutation Check",
    "cut": "Cutter",
    "deploy": "Deploy Check",
    "lint": "Spec Linter",
    "ideas": "Ideas Checker",
    "ship": "Ship",
    "spec-status": "Spec Status",
    "handover-checks": "Handover Checks",
    "watch": "Watchdog",
}

# A red report names the component that has to fix it. This is the routing the
# pipeline documents in its own retry messages, not a new rule.
FAILED_REPORT_REPAIRS = {
    "ideas.json": {"kind": "agent", "component": "idea-generator", "phase": "idea",
                   "reason": "The ideas checker rejected the idea set, so the idea-generator rewrites it.",
                   "then": ["ideas"]},
    "lint.json": {"kind": "agent", "component": "spec-writer", "phase": "spec",
                  "reason": "The spec linter rejected the spec, so the spec-writer revises spec.md and spec.json.",
                  "then": ["lint"]},
    "gate1.json": {"kind": "agent", "component": "spec-writer", "phase": "spec",
                   "reason": "The Gate 1 stopping rule says reject, so the spec-writer resolves the blocking findings.",
                   "then": ["lint", "breaker begin", "breaker end", "gate1-check"]},
    "redfirst.json": {"kind": "agent", "component": "test-writer", "phase": "spec",
                      "reason": "Red-first failed: a test that passes before the code exists proves nothing.",
                      "then": ["redfirst"]},
    "results.json": {"kind": "agent", "component": "builder", "phase": "code",
                     "reason": "The acceptance suite is red, so the builder repairs app/.",
                     "then": ["test"]},
    "mutation.json": {"kind": "agent", "component": "verifier", "phase": "code",
                      "reason": "A student task grades nothing, so the verifier strengthens the suite.",
                      "then": ["mutation"]},
    "skeleton-check.json": {"kind": "script", "component": "cut", "phase": "pack",
                            "reason": "The skeleton does not fail the right tests - regenerate it from the cut markers.",
                            "then": ["leak"]},
    "leak-scan.json": {"kind": "agent", "component": "builder", "phase": "pack",
                       "reason": "The student tree leaks an answer line - the cut markers in app/ have to move (rule 4: never edit skeleton/).",
                       "then": ["cut", "leak"]},
    "guide-lint.json": {"kind": "agent", "component": "pack-writer", "phase": "pack",
                        "reason": "The guide linter rejected the instructor guide.",
                        "then": ["guide-lint"]},
    "deploy.json": {"kind": "agent", "component": "builder", "phase": "pack",
                    "reason": "A fresh install or build of app/ failed, so the builder repairs it. "
                              "Rule 8: an edit to app/ makes the skeleton stale, so the cutter "
                              "and the leak scan run again before the deploy check.",
                    "then": ["cut", "leak", "deploy"]},
}

CHECKERS_BY_FLOW_STEP = {
    1: {2: ["lint"], 3: ["breaker end", "gate1-check"], 6: ["test"],
        8: ["cut"], 10: ["deploy"], 12: ["ship"]},
    2: {1: ["ideas"], 3: ["lint"], 4: ["breaker end", "gate1-check"],
        5: ["redfirst"], 7: ["test"], 8: ["mutation"],
        10: ["cut", "leak"], 11: ["guide-lint"], 12: ["deploy"], 15: ["ship"]},
}
WORKFLOW_BY_PHASE = {
    "idea": '/workflow gp-phase0-ideas {"slug":"<slug>"}',
    "spec": '/workflow gp-phase1-spec {"slug":"<slug>"}',
    "code": '/workflow gp-phase2-code {"slug":"<slug>"}',
    "pack": '/workflow gp-phase3-pack {"slug":"<slug>"}',
}
PHASE_TITLES = {
    "idea": "Idea", "spec": "Specification", "code": "Code", "pack": "Handover",
}
GATE_TITLES = {
    "gate0": "Gate 0 - pick an idea",
    "gate1": "Gate 1 - approve the plan and the tests",
    "gate2": "Gate 2 - read the pass or fail list",
    "gate3": "Gate 3 - approve the pack",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-5"

# Project-level status vocabulary, as the UI reports it.
PENDING = "PENDING"
QUEUED = "QUEUED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
BLOCKED = "BLOCKED"


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and not os.environ.get(key):
            os.environ[key] = value


load_dotenv()


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def safe_text(path: Path, limit: int = 1200) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[:limit]


def slugify(value: str) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-._")
    if not value:
        raise ValueError("project slug is required")
    return value[:80]


def project_path(slug: str) -> Path:
    return PROJECTS / slugify(slug)


def pipeline_dir(slug: str) -> Path:
    d = project_path(slug) / ".pipeline"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_state(slug: str) -> dict:
    state = safe_json(project_path(slug) / ".pipeline" / "state.json")
    if not isinstance(state, dict):
        raise FileNotFoundError(slug)
    state.setdefault("slug", slugify(slug))
    return state


def project_state_paths() -> list[Path]:
    if not PROJECTS.exists():
        return []
    return sorted(PROJECTS.glob("*/.pipeline/state.json"))


def ok_json(path: Path, key: str = "ok") -> bool:
    data = safe_json(path, {})
    return bool(isinstance(data, dict) and data.get(key))


def json_rejected(path: Path) -> bool:
    data = safe_json(path)
    if not isinstance(data, dict):
        return False
    if data.get("ok") is False:
        return True
    return data.get("verdict") == "reject"


def report_matches_current_spec(project: Path, report: dict) -> bool:
    """A report that names a different spec is not a verdict on this one."""
    report_hash = report.get("spec_hash") or report.get("reviewed_spec_hash")
    return not report_hash or report_hash == spec_hash(project)


def fresh_report(project: Path, name: str) -> bool:
    """ok, and about the spec that is on disk right now."""
    data = safe_json(project / name, {})
    if not isinstance(data, dict) or not data.get("ok"):
        return False
    return report_matches_current_spec(project, data)


def ambiguity_bound(project: Path, state: dict) -> bool:
    if gate_passed(state, "gate1"):
        return True
    want = spec_hash(project)
    if want is None:                    # no spec yet - nothing can be bound to it
        return False
    meta = safe_json(project / ".pipeline" / "ambiguity-meta.json", {})
    return bool(isinstance(meta, dict) and meta.get("spec_hash") == want)


def breaker_pass_open(project: Path) -> bool:
    want = spec_hash(project)
    if want is None:
        return False
    began = safe_json(project / ".pipeline" / "breaker-begin.json", {})
    return bool(isinstance(began, dict) and began.get("spec_hash") == want)


def gate1_report_stale(report: dict) -> bool:
    """Did the Gate 1 rule reject only because the report outran the spec?

    gate1.check stops at staleness and never reaches the findings, so a stale
    report says nothing about whether the spec has unowned blocking findings.
    """
    reviewed = report.get("reviewed_spec_hash")
    return bool(reviewed and reviewed != report.get("spec_hash"))


def gate1_report_current(project: Path) -> bool:
    report = safe_json(project / "gate1.json", {})
    return bool(isinstance(report, dict) and report_matches_current_spec(project, report))


def gate1_check_passed(project: Path, state: dict) -> bool:
    return gate_passed(state, "gate1") or (
        ok_json(project / "gate1.json") and gate1_report_current(project))


def gate_passed(state: dict, gate: str) -> bool:
    gate_data = (state.get("gates") or {}).get(gate)
    return bool(gate_data and gate_data.get("approved"))


def gate_rejected(state: dict, gate: str) -> bool:
    gate_data = (state.get("gates") or {}).get(gate)
    return bool(gate_data and gate_data.get("approved") is False)


def gate_name_of(description: str, step_no: int) -> str:
    match = re.search(r"gate\s*(\d)", description, re.IGNORECASE)
    return f"gate{match.group(1)}" if match else f"gate{step_no}"


def agent_or_script(step: tuple | None) -> str:
    if not step:
        return ""
    number, _phase, who, text = step
    if who in {"AGENT", "SCRIPT"}:
        return text.split("->", 1)[0].strip()
    if who == "GATE":
        return gate_name_of(text, number)
    return "human"


def flow_steps(flow: int) -> list[tuple]:
    return STEPS_BY_FLOW.get(int(flow), STEPS_BY_FLOW[1])


def step_tuple(flow: int, number: int) -> tuple | None:
    return next((s for s in flow_steps(flow) if s[0] == number), None)


# --------------------------------------------------------------------------
# the plan: what actually has to happen, in order, for every step
# --------------------------------------------------------------------------
def plan_entries(project: Path, state: dict) -> list[dict]:
    """Every concrete action the workflow needs, in order, with whether it is done.

    A step in `STEPS_BY_FLOW` is one line of the flow diagram; running it is
    usually more than one action - an agent writes, then its checker runs. This
    expands the diagram into the actions themselves, which is what both the
    timeline and the orchestrator need. Every `done` value is read off the same
    files the CLI reads.
    """
    flow = int(state.get("flow", 1))
    out: list[dict] = []

    def add(number: int, kind: str, component: str, done: bool, label: str = "",
            note: str = "") -> None:
        step = step_tuple(flow, number)
        out.append({
            "step": number,
            "phase": step[1] if step else state.get("phase", ""),
            "kind": kind,
            "component": component,
            "label": label or component_label(kind, component),
            "done": bool(done),
            "note": note,
            "description": step[3] if step else "",
        })

    has = lambda rel: (project / rel).exists()          # noqa: E731
    slug = state.get("slug", project.name)
    ideas_dir = project / "ideas"
    n_ideas = len(list(ideas_dir.glob("idea-*.md"))) if ideas_dir.is_dir() else 0

    if flow == 2:
        add(0, "person", "stack input", has("stack.json"),
            note="The human gives the stack, the sessions and the minutes.")
        add(1, "agent", "idea-generator", n_ideas >= 5)
        add(1, "script", "ideas", ok_json(project / "ideas.json"))
        add(2, "gate", "gate0", gate_passed(state, "gate0") and has("idea.md"),
            note="A person picks one idea. The AI does not pick.")
        add(3, "agent", "spec-writer", has("spec.md") and has("spec.json"))
        add(3, "script", "lint", fresh_report(project, "lint.json"))
        add(4, "script", "breaker begin", breaker_pass_open(project) or has("ambiguity.md"))
        add(4, "agent", "spec-breaker", has("ambiguity.md"))
        add(4, "script", "breaker end", ambiguity_bound(project, state))
        add(4, "script", "gate1-check",
            gate1_check_passed(project, state) or gate_passed(state, "gate1"))
        add(5, "agent", "test-writer", has("verify"))
        add(5, "script", "redfirst", ok_json(project / "redfirst.json"))
        add(6, "gate", "gate1", gate_passed(state, "gate1"),
            note="A person approves the plan and the tests before any code exists.")
        add(7, "agent", "builder", has("app"))
        add(7, "script", "test", ok_json(project / "results.json"))
        # The Verifier strengthens a suite that already exists, so it leaves no
        # file of its own that nothing else writes. It is done when the UI has a
        # successful run of it on record, or when something downstream of it -
        # the mutation check, or Gate 2 - has already happened.
        add(8, "agent", "verifier",
            agent_ran(slug, 8, "verifier") or has("mutation.json")
            or gate_passed(state, "gate2"))
        add(8, "script", "mutation", ok_json(project / "mutation.json"))
        add(9, "gate", "gate2", gate_passed(state, "gate2"),
            note="A person reads the pass or fail list, every criterion.")
        add(10, "script", "cut", ok_json(project / "skeleton-check.json"))
        add(10, "script", "leak", ok_json(project / "leak-scan.json"))
        add(11, "agent", "pack-writer", has("pack"))
        add(11, "script", "guide-lint", ok_json(project / "guide-lint.json"))
        add(12, "script", "deploy", ok_json(project / "deploy.json"))
        add(13, "person", "dry run", bool(state.get("dry_run")),
            note="A person who did not build it teaches one session, with a timer.")
        add(14, "gate", "gate3", gate_passed(state, "gate3"),
            note="A person approves the pack.")
        add(15, "script", "ship", has(".pipeline/SHIPPED"))
        return out

    add(1, "person", "idea.md",
        has("idea.md") and "<Project title>" not in safe_text(project / "idea.md", 400),
        note="A person writes the one-page idea.")
    add(2, "agent", "spec-writer", has("spec.md") and has("spec.json"))
    add(2, "script", "lint", fresh_report(project, "lint.json"))
    add(3, "script", "breaker begin", breaker_pass_open(project) or has("ambiguity.md"))
    add(3, "agent", "spec-breaker", has("ambiguity.md"))
    add(3, "script", "breaker end", ambiguity_bound(project, state))
    add(3, "script", "gate1-check", gate1_check_passed(project, state))
    add(4, "gate", "gate1", gate_passed(state, "gate1"))
    add(5, "agent", "builder", has("app"))
    add(5, "script", "test", ok_json(project / "results.json"))
    add(6, "agent", "verifier", agent_ran(slug, 6, "verifier") or has("verify"))
    add(7, "gate", "gate2", gate_passed(state, "gate2"))
    add(8, "script", "cut", ok_json(project / "skeleton-check.json"))
    add(9, "agent", "pack-writer", has("pack"))
    add(10, "script", "deploy", ok_json(project / "deploy.json"))
    add(11, "gate", "gate3", gate_passed(state, "gate3"))
    add(12, "script", "ship", has(".pipeline/SHIPPED"))
    return out


def component_label(kind: str, component: str) -> str:
    if kind == "agent":
        return STEP_AGENT_ALIASES.get(component, component)
    if kind == "script":
        return SCRIPT_LABELS.get(component, component)
    if kind == "gate":
        return GATE_TITLES.get(component, component)
    return component


def next_action(project: Path, state: dict) -> dict | None:
    """The first action in the plan that has not happened. None when shipped."""
    for entry in plan_entries(project, state):
        if not entry["done"]:
            return entry
    return None


def suite_did_not_run(project: Path) -> bool:
    """Did the test runner produce a verdict, or fail to run at all?

    `cli._checker` says a checker has three outcomes and not two - pass, fail,
    and DID NOT RUN - and that mapping the third onto one of the first two is
    how the pipeline has quietly gone wrong before. A collection error is the
    third: pytest exits 2, nothing passed, nothing failed, every criterion is
    "missing". That supports no conclusion about `app/`, so it must not be
    handed to the Builder as if the code were wrong.
    """
    report = safe_json(project / "results.json", {})
    if not isinstance(report, dict) or report.get("ok"):
        return False
    counts = report.get("counts") or {}
    ran = sum(int(counts.get(k) or 0) for k in ("pass", "fail", "skip"))
    rc = int(report.get("pytest_returncode") or 0)
    # The fourth outcome. BOOT_FAILED_RC is not pytest's - the test runner sets
    # it when the app fails to install or build, so the suite was never asked
    # anything and this says nothing about the tests. It is the plainest kind of
    # code problem and the Builder owns it. demo-run-01's builder wrote no
    # package.json; npm run build died on ENOENT, every criterion came back
    # "missing", and four consecutive repairs went to the Test Writer to rewrite
    # tests that were never wrong.
    if rc == BOOT_FAILED_RC:
        return False
    return ran == 0 and rc != 0


def failed_repair(project: Path, state: dict) -> dict | None:
    """A red checker report re-opens the step that owns it.

    Only reports that are about the spec on disk count, and only reports for
    phases the project has actually reached - a red lint.json left behind by a
    revised round is not a verdict on the round now in flight.
    """
    slug = state.get("slug", project.name)
    order = list(PHASES_BY_FLOW.get(int(state.get("flow", 1)), PHASES_BY_FLOW[1]))
    reached = order.index(state.get("phase")) if state.get("phase") in order else len(order)
    for filename, meta in FAILED_REPORT_REPAIRS.items():
        path = project / filename
        if not path.exists():
            continue
        report = safe_json(path, {})
        if not isinstance(report, dict) or not report_matches_current_spec(project, report):
            continue
        if not json_rejected(path):
            continue
        phase = meta.get("phase", "")
        if phase in order and order.index(phase) > reached:
            continue
        if filename == "results.json" and suite_did_not_run(project):
            meta = {
                "kind": "agent", "component": "test-writer", "phase": "code",
                "reason": "The suite did not run at all - pytest could not even "
                          "collect it, so nothing passed and nothing failed. That "
                          "is a test problem, not a code problem: no conclusion "
                          "about app/ can be drawn from it, and the Builder cannot "
                          "edit the tests (rule 3).",
                "then": ["test"],
            }
        # Rule 7 rejects a report the spec outran. The owner of a blocking
        # finding is the Spec Writer, but staleness is the one rejection the
        # Spec Writer cannot fix - rewriting the spec is what moved the hash out
        # from under the report. Sending it there spins: spec-writer, lint,
        # breaker, reject, spec-writer. demo-run-01 went round four times and
        # burned three spec retries before the repeat guard stopped it. What
        # settles it is a fresh Breaker pass against the spec on disk, and that
        # has to start at `breaker begin` - `breaker end` refuses outright when
        # the pass was opened against a different hash.
        if filename == "gate1.json" and gate1_report_stale(report):
            meta = {
                "kind": "script", "component": "breaker begin", "phase": "spec",
                "reason": "The ambiguity report reviewed an older spec than the "
                          "one on disk. A fresh Spec Breaker pass settles that; "
                          "the Spec Writer cannot, because rewriting the spec is "
                          "what made the report stale.",
                "then": [],
            }
        # The owner has already had this report and rewritten its files. Running
        # it again on the same report just repeats the same run; what settles it
        # is the checker, so let the plan fall through to it. (A spec report also
        # carries a hash, and a spec that has moved invalidates it above - but
        # results.json and its kind carry no hash, so this is the general rule.)
        try:
            written = path.stat().st_mtime
        except OSError:
            written = 0.0
        if succeeded_after(slug, meta["component"], written):
            continue
        return {
            "step": None,
            "phase": phase,
            "kind": meta["kind"],
            "component": meta["component"],
            "label": component_label(meta["kind"], meta["component"]),
            "done": False,
            "note": meta["reason"],
            "repair_of": filename,
            "then": meta.get("then", []),
            "description": meta["reason"],
        }
    return None


def step_checks(project: Path, state: dict) -> list[tuple[int, bool]]:
    """One pass/fail per step, for progress. Derived from the plan."""
    by_step: dict[int, bool] = {}
    for entry in plan_entries(project, state):
        by_step[entry["step"]] = by_step.get(entry["step"], True) and entry["done"]
    return sorted(by_step.items())


def next_step(project: Path, state: dict) -> dict:
    flow = int(state.get("flow", 1))
    completed = [n for n, ok in step_checks(project, state) if ok]
    action = next_action(project, state)
    if action is None:
        return {"flow": flow, "step": None, "phase": state.get("phase"), "who": "",
                "do": "done - shipped", "completed": completed, "retries_left": 0}
    step = step_tuple(flow, action["step"])
    who = step[2] if step else action["kind"].upper()
    return {
        "flow": flow,
        "step": action["step"],
        "phase": action["phase"],
        "who": who,
        "do": step[3] if step else action["note"],
        "completed": completed,
        "retries_left": max(0, RETRY_LIMIT - int((state.get("retries") or {}).get(action["phase"], 0))),
    }


# --------------------------------------------------------------------------
# run ledger
# --------------------------------------------------------------------------
def runs_file(slug: str) -> Path:
    return pipeline_dir(slug) / "ui-runs.jsonl"


def log_file(slug: str, run_id: str) -> Path:
    d = pipeline_dir(slug) / "ui-logs"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{run_id}.log"


def persist_run(record: dict) -> None:
    slug = record.get("slug")
    if not slug:
        return
    row = {k: v for k, v in record.items() if k not in {"stdout", "stderr"}}
    row["stdout_tail"] = (record.get("stdout") or "")[-4000:]
    row["stderr_tail"] = (record.get("stderr") or "")[-4000:]
    try:
        with runs_file(slug).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        pass


def load_persisted_runs() -> None:
    """Rebuild the registry after a restart. A run that was live when the server
    stopped is recorded as interrupted, never as succeeded."""
    for state_path in project_state_paths():
        slug = state_path.parents[1].name
        path = state_path.parents[1] / ".pipeline" / "ui-runs.jsonl"
        if not path.exists():
            continue
        rows: dict[str, dict] = {}
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("id"):
                rows[row["id"]] = row
        with RUNS_LOCK:
            for run_id, row in rows.items():
                if run_id in RUNS:
                    continue
                row.setdefault("slug", slug)
                if row.get("status") == "running":
                    row["status"] = "interrupted"
                    row["finished"] = row.get("finished") or row.get("started")
                row["stdout"] = row.pop("stdout_tail", "")
                row["stderr"] = row.pop("stderr_tail", "")
                row["restored"] = True
                RUNS[run_id] = row


def register_run(record: dict) -> dict:
    with RUNS_LOCK:
        RUNS[record["id"]] = record
    persist_run(record)
    return record


def update_run(run_id: str, **fields) -> dict:
    with RUNS_LOCK:
        record = RUNS.get(run_id)
        if not record:
            return {}
        record.update(fields)
        snapshot = record.copy()
    if fields.get("status") in {"succeeded", "failed", "interrupted"}:
        persist_run(snapshot)
    return snapshot


def append_run_output(run_id: str, text: str) -> None:
    with RUNS_LOCK:
        record = RUNS.get(run_id)
        if not record:
            return
        record["stdout"] = (record.get("stdout", "") + text)[-60_000:]
        slug = record.get("slug")
    if slug:
        try:
            with log_file(slug, run_id).open("a", encoding="utf-8") as fh:
                fh.write(text)
        except OSError:
            pass


def get_run(run_id: str) -> dict | None:
    with RUNS_LOCK:
        record = RUNS.get(run_id)
        record = record.copy() if record else None
    if record and record.get("slug"):
        path = log_file(record["slug"], run_id)
        if path.exists():
            record["stdout"] = safe_text(path, 400_000)
    return record


def project_runs(slug: str, limit: int = 60) -> list[dict]:
    with RUNS_LOCK:
        runs = [r.copy() for r in RUNS.values() if r.get("slug") == slug]
    runs.sort(key=lambda r: r.get("started") or 0, reverse=True)
    for run in runs:
        run["stdout"] = (run.get("stdout") or "")[-4000:]
        run["stderr"] = (run.get("stderr") or "")[-4000:]
    return runs[:limit]


def all_runs(limit: int = 80) -> list[dict]:
    with RUNS_LOCK:
        runs = [r.copy() for r in RUNS.values()]
    runs.sort(key=lambda r: r.get("started") or 0, reverse=True)
    for run in runs:
        run["stdout"] = (run.get("stdout") or "")[-1500:]
        run["stderr"] = (run.get("stderr") or "")[-1500:]
    return runs[:limit]


def live_runs(slug: str | None = None) -> list[dict]:
    with RUNS_LOCK:
        return [r.copy() for r in RUNS.values()
                if r.get("status") == "running" and (slug is None or r.get("slug") == slug)]


def has_running(slug: str) -> bool:
    return bool(live_runs(slug))


def agent_ran(slug: str, step: int | None, agent: str) -> bool:
    """Has this agent completed a run for this project, recorded in the ledger?

    Used only where the agent leaves no artifact of its own that the pipeline
    already checks - in practice the Verifier, which strengthens a suite that
    already exists. Everything else is answered by a file on disk.
    """
    with RUNS_LOCK:
        for record in RUNS.values():
            if (record.get("slug") == slug and record.get("kind") == "agent"
                    and record.get("component") == agent
                    and record.get("status") == "succeeded"):
                return True
    return False


def succeeded_after(slug: str, component: str, when: float) -> bool:
    """Has this component finished a successful run since `when`?

    Used to tell a red report that is still waiting for its owner from one the
    owner has already answered. The second kind must not re-trigger the owner -
    what it needs is the checker, run again.
    """
    with RUNS_LOCK:
        for record in RUNS.values():
            if (record.get("slug") == slug and record.get("component") == component
                    and record.get("status") == "succeeded"
                    and float(record.get("finished") or 0) > when):
                return True
    return False


def attempt_number(slug: str, component: str) -> int:
    with RUNS_LOCK:
        return 1 + sum(1 for r in RUNS.values()
                       if r.get("slug") == slug and r.get("component") == component)


# --------------------------------------------------------------------------
# event log
# --------------------------------------------------------------------------
def events_file(slug: str) -> Path:
    return pipeline_dir(slug) / "ui-events.jsonl"


def events_meta_file(slug: str) -> Path:
    return pipeline_dir(slug) / "ui-events-meta.json"


def _next_seq(slug: str) -> int:
    if slug not in _SEQ:
        path = events_file(slug)
        count = 0
        if path.exists():
            try:
                count = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
            except OSError:
                count = 0
        _SEQ[slug] = count
    _SEQ[slug] += 1
    return _SEQ[slug]


def log_event(slug: str, message: str, *, level: str = "info", kind: str = "workflow",
              detail: str = "", phase: str = "", step=None, component: str = "",
              run_id: str = "", at: str = "", source: str = "ui") -> dict:
    slug = slugify(slug)
    with EVENT_LOCK:
        event = {
            "seq": _next_seq(slug),
            "at": at or now_iso(),
            "ts": time.time(),
            "level": level,
            "kind": kind,
            "message": message,
            "detail": (detail or "")[:2000],
            "phase": phase,
            "step": step,
            "component": component,
            "run_id": run_id,
            "source": source,
        }
        try:
            with events_file(slug).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")
        except OSError:
            pass
    return event


def read_events(slug: str, after: int = 0, limit: int = 400) -> list[dict]:
    sync_state_events(slug)
    path = events_file(slug)
    if not path.exists():
        return []
    out = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if int(event.get("seq") or 0) > after:
                out.append(event)
    except OSError:
        return []
    # Back-filled history arrives in state.json order, which is not always the
    # order things happened in - a gate recorded before a later checker run is
    # appended after it. Sort for display; `after` still filters on seq.
    out.sort(key=lambda e: (str(e.get("at") or ""), int(e.get("seq") or 0)))
    return out[-limit:]


def sync_state_events(slug: str) -> None:
    """Mirror state.json into the event log.

    The CLI is still a first-class entry point and writes only state.json, so
    anything run outside the UI would otherwise be invisible here. This walks
    what state.json records and appends whatever the event log has not seen -
    which also back-fills a project that existed before the UI did.
    """
    slug = slugify(slug)
    project = project_path(slug)
    state = safe_json(project / ".pipeline" / "state.json")
    if not isinstance(state, dict):
        return
    with EVENT_LOCK:
        meta = safe_json(events_meta_file(slug), {}) or {}
        changed = False
        if not meta.get("created"):
            log_event(slug, "Project created", level="ok", kind="workflow",
                      detail=f"flow {state.get('flow', 1)}",
                      at=state.get("created", ""), source="state.json")
            meta["created"] = True
            changed = True
        steps = state.get("steps") or []
        seen = int(meta.get("steps") or 0)
        for item in steps[seen:]:
            name = item.get("step", "")
            kind = "script" if name.split(":")[0] in SCRIPT_COMMANDS else "workflow"
            log_event(slug,
                      f"{name} {'passed' if item.get('ok') else 'FAILED'}",
                      level="ok" if item.get("ok") else "error",
                      kind=kind, component=name.split(":")[0],
                      detail=item.get("detail", ""),
                      phase=SCRIPT_COMMANDS.get(name.split(":")[0], {}).get("phase", ""),
                      at=item.get("at", ""), source="state.json")
            changed = True
        meta["steps"] = len(steps)
        gates = meta.get("gates") or {}
        for name, gate in (state.get("gates") or {}).items():
            if not gate:
                continue
            stamp = gate.get("at", "")
            if gates.get(name) == stamp:
                continue
            log_event(slug,
                      f"{name} {'approved' if gate.get('approved') else 'rejected'}",
                      level="ok" if gate.get("approved") else "error",
                      kind="gate", component=name, detail=(gate.get("note") or "")[:500],
                      at=stamp, source="state.json")
            gates[name] = stamp
            changed = True
        meta["gates"] = gates
        dry = state.get("dry_run")
        if dry and meta.get("dry_run") != dry.get("at"):
            log_event(slug, "Dry run recorded", level="ok", kind="human",
                      detail=f"session {dry.get('session')}, {dry.get('minutes')} min, "
                             f"by {dry.get('by')}, taught without the code: "
                             f"{dry.get('taught_without_the_code')}",
                      at=dry.get("at", ""), source="state.json")
            meta["dry_run"] = dry.get("at")
            changed = True
        feedback = state.get("feedback") or []
        if len(feedback) > int(meta.get("feedback") or 0):
            for item in feedback[int(meta.get("feedback") or 0):]:
                log_event(slug, "Instructor feedback recorded", level="warn",
                          kind="human", detail=item.get("note", ""),
                          at=item.get("at", ""), source="state.json")
            meta["feedback"] = len(feedback)
            changed = True
        ticket = state.get("ticket")
        if ticket and meta.get("ticket") != ticket.get("raised"):
            log_event(slug, f"TICKET raised in the {ticket.get('phase')} phase",
                      level="error", kind="workflow",
                      detail=f"{ticket.get('kind', '')}: {ticket.get('last_error', '')}",
                      at=ticket.get("raised", ""), source="state.json")
            meta["ticket"] = ticket.get("raised")
            changed = True
        if changed:
            try:
                events_meta_file(slug).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
            except OSError:
                pass


# --------------------------------------------------------------------------
# workflow (auto-run) state
# --------------------------------------------------------------------------
def workflow_file(slug: str) -> Path:
    return pipeline_dir(slug) / "ui-workflow.json"


def read_workflow(slug: str) -> dict:
    data = safe_json(workflow_file(slug), {}) or {}
    if data.get("state") == "running" and data.get("pid") != os.getpid():
        data["state"] = "interrupted"
        data["reason"] = "the UI server restarted while this run was in flight"
    return data


def write_workflow(slug: str, **fields) -> dict:
    data = safe_json(workflow_file(slug), {}) or {}
    data.update(fields)
    data["pid"] = os.getpid()
    data["updated"] = now_iso()
    try:
        workflow_file(slug).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    return data


# --------------------------------------------------------------------------
# derived views
# --------------------------------------------------------------------------
def project_status(project: Path, state: dict, action: dict | None,
                   workflow: dict) -> str:
    slug = state.get("slug", project.name)
    if (project / ".pipeline" / "SHIPPED").exists():
        return COMPLETED
    if state.get("ticket"):
        return FAILED
    if has_running(slug) or workflow.get("state") == "running":
        return RUNNING
    if action is None:
        return COMPLETED
    if workflow.get("state") == "blocked":
        return BLOCKED
    if action["kind"] == "gate":
        return WAITING_FOR_REVIEW
    if action["kind"] == "person":
        return WAITING_FOR_INPUT
    # A gate rejected earlier is history once the workflow has moved past it -
    # the next action is what the project is waiting on, and the gate panel says
    # what was rejected and why.
    last = (state.get("steps") or [])[-1:]
    if last and not last[0].get("ok"):
        return FAILED
    return QUEUED


def phase_items(project: Path, state: dict) -> list[dict]:
    flow = int(state.get("flow", 1))
    entries = plan_entries(project, state)
    current = next_action(project, state)
    slug = state.get("slug", project.name)
    running = live_runs(slug)
    running_components = {r.get("component") for r in running}
    running_phases = {r.get("phase") for r in running if r.get("phase")}
    ticket_phase = (state.get("ticket") or {}).get("phase")
    stopped = read_workflow(slug).get("state") == "blocked"
    phases = []
    for phase in PHASES_BY_FLOW.get(flow, PHASES_BY_FLOW[1]):
        mine = [e for e in entries if e["phase"] == phase]
        numbers = sorted({e["step"] for e in mine})
        done_numbers = sorted({n for n in numbers
                               if all(e["done"] for e in mine if e["step"] == n)})
        if ticket_phase == phase:
            status = FAILED
        elif stopped and current and current["phase"] == phase:
            status = BLOCKED
        elif current and current["phase"] == phase and current["kind"] == "gate":
            status = WAITING_FOR_REVIEW
        elif phase in running_phases or (
                current and current["phase"] == phase and running_components):
            status = RUNNING
        elif current and current["phase"] == phase and current["kind"] == "person":
            status = WAITING_FOR_INPUT
        elif current and current["phase"] == phase:
            # the phase the workflow is sitting in, with nothing executing in it
            status = QUEUED
        elif numbers and len(done_numbers) == len(numbers):
            status = COMPLETED
        else:
            status = PENDING
        phases.append({
            "name": phase,
            "title": PHASE_TITLES.get(phase, phase),
            "status": status,
            "steps": phase_steps(project, state, phase, entries, current, running_components),
            "completed_steps": len(done_numbers),
            "total_steps": len(numbers),
            "retry_count": int((state.get("retries") or {}).get(phase, 0)),
            "retry_limit": RETRY_LIMIT,
            "workflow_command": WORKFLOW_BY_PHASE.get(phase, "").replace("<slug>", slug),
        })
    return phases


def phase_steps(project: Path, state: dict, phase: str, entries: list[dict],
                current: dict | None, running_components: set) -> list[dict]:
    flow = int(state.get("flow", 1))
    out = []
    for number in sorted({e["step"] for e in entries if e["phase"] == phase}):
        step = step_tuple(flow, number)
        mine = [e for e in entries if e["step"] == number]
        done = all(e["done"] for e in mine)
        is_current = bool(current and current["step"] == number)
        if done:
            status = COMPLETED
        elif (state.get("ticket") or {}).get("phase") == phase:
            status = BLOCKED
        elif is_current and current["kind"] == "gate":
            status = (WAITING_FOR_REVIEW if not gate_rejected(state, current["component"])
                      else FAILED)
        elif is_current and current["kind"] == "person":
            status = WAITING_FOR_INPUT
        elif is_current:
            status = RUNNING if running_components else QUEUED
        else:
            status = PENDING
        out.append({
            "number": number,
            "phase": phase,
            "who": step[2] if step else "",
            "description": step[3] if step else "",
            "component": agent_or_script(step),
            "status": status,
            "actions": [{
                "kind": e["kind"], "component": e["component"], "label": e["label"],
                "done": e["done"],
                "status": (COMPLETED if e["done"]
                           else RUNNING if e["component"] in running_components
                           else QUEUED if (current and current["component"] == e["component"])
                           else PENDING),
            } for e in mine],
            "run_count": int((state.get("step_runs") or {}).get(agent_or_script(step), 0)),
            "checkers": CHECKERS_BY_FLOW_STEP.get(flow, {}).get(number, []),
            "artifacts": step_artifacts(project, flow, number),
        })
    return out


def step_artifacts(project: Path, flow: int, number: int) -> list[str]:
    by_step = {
        1: {1: ["idea.md"], 2: ["spec.md", "spec.json", "lint.json"],
            3: ["ambiguity.md", "gate1.json"], 5: ["app"],
            6: ["verify", "results.json"], 8: ["skeleton", "skeleton-check.json"],
            9: ["pack"], 10: ["deploy.json"]},
        2: {0: ["stack.json"], 1: ["ideas", "ideas.json"], 2: ["idea.md"],
            3: ["spec.md", "spec.json", "lint.json"],
            4: ["ambiguity.md", "gate1.json"],
            5: ["verify", "coverage.json", "redfirst.json"],
            7: ["app", "results.json"], 8: ["mutation.json"],
            10: ["skeleton", "skeleton-check.json", "leak-scan.json"],
            11: ["pack", "guide-lint.json"], 12: ["deploy.json"]},
    }
    return [rel for rel in by_step.get(flow, {}).get(number, []) if (project / rel).exists()]


def artifact_list(project: Path, limit: int = 4000) -> list[dict]:
    out: list[dict] = []
    if not project.exists():
        return out
    skip_dirs = {"node_modules", ".next", "__pycache__", ".git", "dist", "build",
                 ".venv", "venv", ".pytest_cache", "ui-logs", "playwright-report",
                 "test-results", ".turbo"}
    files: list[Path] = []
    for root, dirs, names in os.walk(project):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in names:
            files.append(Path(root) / name)
        if len(files) > limit:
            break
    for path in sorted(files):
        rel = path.relative_to(project)
        first = rel.parts[0]
        include = (
            path.name in ARTIFACT_NAMES
            or first in {"ideas", "verify", "pack", "app", "skeleton", "uploads"}
            or (first == ".pipeline" and path.name in {"state.json", "SHIPPED", "SPEC_FROZEN"})
        )
        if not include:
            continue
        try:
            size = path.stat().st_size
            mtime = path.stat().st_mtime
        except OSError:
            size, mtime = 0, 0
        out.append({
            "path": str(rel).replace("\\", "/"),
            "name": path.name,
            "kind": artifact_kind(rel),
            "size": size,
            "modified": mtime,
            "viewable": path.suffix.lower() in TEXT_TYPES or size < 512_000,
        })
    return out


def artifact_kind(rel: Path) -> str:
    first = rel.parts[0]
    mapping = {
        "pack": "Instructor guide", "verify": "Test suite",
        "app": "Working project", "skeleton": "Student version",
        "ideas": "Project ideas", "uploads": "Reference material",
    }
    if first in mapping:
        return mapping[first]
    if rel.name in {"spec.md", "spec.json"}:
        return "Specification"
    if rel.name == "ambiguity.md":
        return "Ambiguity report"
    if rel.suffix == ".json":
        return "Checker report"
    return "Artifact"


def project_summary(path: Path) -> dict | None:
    state = safe_json(path / ".pipeline" / "state.json")
    if not isinstance(state, dict):
        return None
    state.setdefault("slug", path.name)
    slug = state["slug"]
    workflow = read_workflow(slug)
    action = next_action(path, state)
    repair = failed_repair(path, state)
    checks = step_checks(path, state)
    completed = sum(1 for _, ok in checks if ok)
    total = len(checks) or 1
    entries = plan_entries(path, state)
    actions_done = sum(1 for e in entries if e["done"])
    stack = safe_json(path / "stack.json", {}) or {}
    running = live_runs(slug)
    status = project_status(path, state, action, workflow)
    phase = action["phase"] if action else state.get("phase")
    return {
        "slug": slug,
        "name": slug,
        "created": state.get("created", ""),
        "flow": int(state.get("flow", 1)),
        "phase": phase,
        "phase_title": PHASE_TITLES.get(phase, phase or ""),
        "status": status,
        "workflow_state": workflow.get("state", "idle"),
        "workflow_reason": workflow.get("reason", ""),
        "auto": workflow.get("state") == "running",
        "progress": round((actions_done / (len(entries) or 1)) * 100),
        "completed_steps": completed,
        "total_steps": total,
        "completed_actions": actions_done,
        "total_actions": len(entries),
        "step": action["step"] if action else None,
        "step_description": action["description"] if action else "done - shipped",
        "next_action": action,
        "repair": repair,
        "current_component": (running[0]["component"] if running
                              else (repair or action or {}).get("component", "")),
        "current_kind": (running[0]["kind"] if running
                         else (repair or action or {}).get("kind", "")),
        "retry_count": int((state.get("retries") or {}).get(phase, 0)) if phase else 0,
        "retry_limit": RETRY_LIMIT,
        "step_run_limit": STEP_RUN_LIMIT,
        "ticket": state.get("ticket"),
        "shipped": (path / ".pipeline" / "SHIPPED").exists(),
        "spec_frozen": (path / ".pipeline" / "SPEC_FROZEN").exists(),
        "stack": ", ".join(stack.get("stack", [])) if isinstance(stack, dict) else "",
        "sessions": stack.get("sessions") if isinstance(stack, dict) else None,
        "minutes": stack.get("minutes_per_session") if isinstance(stack, dict) else None,
        "track": stack.get("track") if isinstance(stack, dict) else "",
    }


def all_projects() -> list[dict]:
    out = []
    for state_path in project_state_paths():
        summary = project_summary(state_path.parents[1])
        if summary:
            out.append(summary)
    return sorted(out, key=lambda p: p.get("created") or "", reverse=True)


def current_execution(path: Path, state: dict, summary: dict,
                      events: list[dict]) -> dict:
    slug = state.get("slug", path.name)
    running = live_runs(slug)
    run = running[0] if running else None
    recent = [e for e in reversed(events)]
    latest = recent[0] if recent else {}
    repair = summary.get("repair")
    action = repair or summary.get("next_action") or {}
    started = run.get("started") if run else None
    description = summary.get("step_description")
    if repair:
        description = (f"repair {repair.get('repair_of')} - "
                       f"{repair.get('note', '')}")
    return {
        "phase": summary.get("phase"),
        "phase_title": summary.get("phase_title"),
        "step": summary.get("step"),
        "step_description": description,
        "component": run.get("component") if run else action.get("component", ""),
        "component_label": (run.get("label") if run else action.get("label", "")),
        "kind": run.get("kind") if run else action.get("kind", ""),
        "status": RUNNING if run else summary.get("status"),
        "started_at": started,
        "elapsed_seconds": int(time.time() - started) if started else None,
        "attempt": run.get("attempt") if run else None,
        "retry_count": summary.get("retry_count", 0),
        "retry_limit": RETRY_LIMIT,
        "model": run.get("model") if run else "",
        "provider": run.get("provider") if run else "",
        "run_id": run.get("id") if run else "",
        "latest_event": latest.get("message", ""),
        "latest_event_at": latest.get("at", ""),
        "output": ((run.get("stdout") or run.get("stderr") or "")[-4000:] if run else ""),
        "reason": action.get("note", ""),
        "repair_of": action.get("repair_of", ""),
    }


def gate_reviews_for(path: Path, state: dict, include_all: bool = False) -> list[dict]:
    flow = int(state.get("flow", 1))
    action = next_action(path, state)
    reviews = []
    for step_no, phase, who, description in flow_steps(flow):
        if who != "GATE":
            continue
        gate = gate_name_of(description, step_no)
        data = (state.get("gates") or {}).get(gate)
        waiting = bool(action and action["kind"] == "gate" and action["component"] == gate)
        if data and data.get("approved") is False:
            waiting = True
        if not include_all and not waiting:
            continue
        blockers = gate_blockers(path, state, gate)
        reviews.append({
            "project": state.get("slug", path.name),
            "phase": phase,
            "phase_title": PHASE_TITLES.get(phase, phase),
            "gate": gate,
            "number": int(gate[-1]),
            "step": step_no,
            "waiting": waiting,
            "status": ("approved" if data and data.get("approved")
                       else "rejected" if data else "waiting" if waiting else "not reached"),
            "title": GATE_TITLES.get(gate, description),
            "summary": description,
            "note": (data.get("note") or "")[:2000] if isinstance(data, dict) else "",
            "at": (data or {}).get("at", "") if isinstance(data, dict) else "",
            "artifacts": gate_artifacts(path, gate),
            "findings": review_findings(path, gate),
            "blockers": blockers,
            "can_approve": not blockers,
            "ideas": ([p.name for p in sorted((path / "ideas").glob("idea-*.md"))]
                      if gate == "gate0" and (path / "ideas").is_dir() else []),
        })
    return reviews


def gate_blockers(path: Path, state: dict, gate: str) -> list[str]:
    """What the CLI would refuse to approve on. Read-only mirror of
    `cli._gate_blockers`, so the UI can grey out a button the CLI would reject -
    the CLI is still the thing that decides."""
    out: list[str] = []
    order = [f"gate{i}" for i in range(4) if f"gate{i}" in (state.get("gates") or {})]
    if gate in order:
        i = order.index(gate)
        if i > 0 and not gate_passed(state, order[i - 1]):
            out.append(f"{order[i - 1]} has not been approved - gates are approved in order")
    if int(state.get("flow", 1)) == 2:
        if gate == "gate0":
            if not (path / "stack.json").exists():
                out.append("no stack.json - step 0 is the human giving the stack")
            if not ok_json(path / "ideas.json"):
                out.append("the idea set has not passed (run the ideas checker)")
        if gate == "gate1":
            if not (path / "verify").exists():
                out.append("verify/ is missing - the tests are written at step 5, before the builder")
            if not ok_json(path / "redfirst.json"):
                out.append("the red-first check has not passed")
        if gate == "gate2":
            if not ok_json(path / "mutation.json"):
                out.append("the mutation check has not passed")
        if gate == "gate3":
            if not ok_json(path / "leak-scan.json"):
                out.append("the leak scan has not passed")
            if not ok_json(path / "guide-lint.json"):
                out.append("the guide linter has not passed")
            dry = state.get("dry_run")
            if not dry:
                out.append("no dry run on record - step 13 is a timed session taught by someone else")
            elif not dry.get("taught_without_the_code"):
                out.append("the dry run recorded that the session could NOT be taught from the guide alone")
    if gate == "gate1":
        if not ok_json(path / "lint.json"):
            out.append("the spec linter has not passed")
        if not (path / "ambiguity.md").exists():
            out.append("the spec-breaker has not run (ambiguity.md missing)")
        elif not ok_json(path / "gate1.json"):
            out.append("the Gate 1 stopping rule says reject (approve with an override and a reason, or send it back)")
    if gate == "gate2":
        if not ok_json(path / "results.json"):
            out.append("the test runner has not passed")
    if gate == "gate3":
        if not ok_json(path / "skeleton-check.json"):
            out.append("the skeleton does not fail the right tests")
        if not (path / "pack").exists():
            out.append("the pack-writer has not run (pack/ missing)")
        if not ok_json(path / "deploy.json"):
            out.append("the deploy check has not passed")
    return out


def gate_artifacts(path: Path, gate: str) -> list[str]:
    by_gate = {
        "gate0": ["stack.json", "ideas.json"] + [f"ideas/idea-{i:02d}.md" for i in range(1, 6)],
        "gate1": ["spec.md", "spec.json", "lint.json", "ambiguity.md", "gate1.json",
                  "redfirst.json", "coverage.json"],
        "gate2": ["results.json", "mutation.json", "spec.json"],
        "gate3": ["pack", "deploy.json", "skeleton-check.json", "leak-scan.json",
                  "guide-lint.json"],
    }
    out = []
    for name in by_gate.get(gate, []):
        target = path / name
        if target.is_dir():
            out.extend(sorted(str(p.relative_to(path)).replace("\\", "/")
                              for p in target.rglob("*.md"))[:12])
        elif target.exists():
            out.append(name)
    return out


def review_findings(path: Path, gate: str) -> str:
    if gate == "gate1":
        report = safe_json(path / "gate1.json", {})
        if isinstance(report, dict):
            bits = []
            counts = report.get("counts")
            if counts:
                bits.append(json.dumps(counts))
            for reason in (report.get("reasons") or [])[:8]:
                bits.append(f"- {reason}")
            if bits:
                return "\n".join(bits)
        return safe_text(path / "ambiguity.md", 1500)
    if gate == "gate2":
        results = safe_json(path / "results.json", {}) or {}
        mutation = safe_json(path / "mutation.json", {}) or {}
        bits = [f"test runner ok: {bool(results.get('ok'))}"]
        if results.get("counts"):
            bits.append(json.dumps(results["counts"]))
        failing = [c for c, v in (results.get("criteria") or {}).items()
                   if isinstance(v, dict) and v.get("status") != "pass"]
        if failing:
            bits.append("failing criteria: " + ", ".join(failing[:12]))
        bits.append(f"mutation ok: {bool(mutation.get('ok'))}")
        if mutation.get("ungraded_tasks"):
            bits.append("ungraded tasks: " + ", ".join(mutation["ungraded_tasks"][:12]))
        return "\n".join(bits)
    if gate == "gate3":
        bits = []
        for name in ("leak-scan.json", "guide-lint.json", "deploy.json",
                     "skeleton-check.json"):
            report = safe_json(path / name, {}) or {}
            bits.append(f"{name}: ok={bool(report.get('ok'))}")
        return "\n".join(bits)
    report = safe_json(path / "ideas.json", {}) or {}
    return json.dumps(report, indent=2)[:1500]


def agents_view(projects: list[dict]) -> list[dict]:
    out = []
    agent_dir = ROOT / ".claude" / "agents"
    for name, phase in AGENT_PHASES.items():
        path = agent_dir / f"{name}.md"
        text = safe_text(path, 4000)
        purpose = ""
        for line in text.splitlines():
            if line.startswith("description:"):
                purpose = line.split(":", 1)[1].strip()
                break
        with RUNS_LOCK:
            runs = sorted([r.copy() for r in RUNS.values() if r.get("component") == name
                           and r.get("kind") == "agent"],
                          key=lambda r: r.get("started") or 0, reverse=True)
        last = runs[0] if runs else None
        running = next((r for r in runs if r.get("status") == "running"), None)
        active = running or last
        out.append({
            "name": name,
            "type": "LLM agent",
            "purpose": purpose or name,
            "phase": phase,
            "phase_title": PHASE_TITLES.get(phase, phase),
            "status": (RUNNING if running else
                       {"succeeded": COMPLETED, "failed": FAILED,
                        "interrupted": "INTERRUPTED"}.get((last or {}).get("status"), "IDLE")),
            "provider": "OpenRouter",
            "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            "project": (active or {}).get("slug", ""),
            "run_id": (active or {}).get("id", ""),
            "started": (active or {}).get("started"),
            "finished": (last or {}).get("finished"),
            "duration": (round((last["finished"] - last["started"]), 1)
                         if last and last.get("finished") and last.get("started") else None),
            "attempt": (active or {}).get("attempt"),
            "runs": len(runs),
            "output": ((active or {}).get("stdout") or (active or {}).get("stderr") or "")[-1500:],
            "retry_count": sum(int((safe_json(PROJECTS / p["slug"] / ".pipeline" / "state.json", {})
                                    .get("retries") or {}).get(phase, 0)) for p in projects),
            "retry_limit": RETRY_LIMIT,
            "prompt_path": f".claude/agents/{name}.md",
            "skill_path": f".claude/skills/{name}/SKILL.md",
            "workflow": WORKFLOW_BY_PHASE.get(phase, ""),
        })
    return out


def scripts_view() -> list[dict]:
    out = []
    for name, meta in SCRIPT_COMMANDS.items():
        with RUNS_LOCK:
            runs = sorted([r.copy() for r in RUNS.values()
                           if r.get("component") == name and r.get("kind") == "script"],
                          key=lambda r: r.get("started") or 0, reverse=True)
        last = runs[0] if runs else None
        running = next((r for r in runs if r.get("status") == "running"), None)
        active = running or last
        report = ""
        if active and active.get("slug"):
            report = script_report_summary(project_path(active["slug"]), name)
        out.append({
            "name": name,
            "label": SCRIPT_LABELS.get(name, name),
            "type": "Deterministic script",
            "purpose": meta["purpose"],
            "phase": meta.get("phase", ""),
            "command": "python -m pipeline " + " ".join(meta["args"]) + (
                "" if meta.get("no_slug") else " <slug>") + (
                f" {meta['mode']}" if meta.get("mode") else ""),
            "status": (RUNNING if running else
                       {"succeeded": COMPLETED, "failed": FAILED,
                        "interrupted": "INTERRUPTED"}.get((last or {}).get("status"), "IDLE")),
            "project": (active or {}).get("slug", ""),
            "run_id": (active or {}).get("id", ""),
            "started": (active or {}).get("started"),
            "finished": (last or {}).get("finished"),
            "duration": (round((last["finished"] - last["started"]), 1)
                         if last and last.get("finished") and last.get("started") else None),
            "returncode": (last or {}).get("returncode"),
            "result": report,
            "output": ((active or {}).get("stdout") or "")[-1500:],
            "error": ((active or {}).get("stderr") or "")[-1500:],
            "runs": len(runs),
        })
    return out


SCRIPT_REPORTS = {
    "ideas": "ideas.json", "lint": "lint.json", "gate1-check": "gate1.json",
    "redfirst": "redfirst.json", "test": "results.json", "mutation": "mutation.json",
    "cut": "skeleton-check.json", "leak": "leak-scan.json",
    "guide-lint": "guide-lint.json", "deploy": "deploy.json",
}


def script_report_summary(project: Path, script: str) -> str:
    name = SCRIPT_REPORTS.get(script)
    if not name:
        return ""
    report = safe_json(project / name, {})
    if not isinstance(report, dict):
        return ""
    bits = [f"{name}: {'PASSED' if report.get('ok') else 'FAILED'}"]
    counts = report.get("counts")
    if isinstance(counts, dict):
        bits.append(", ".join(f"{k}: {v}" for k, v in list(counts.items())[:6]))
    for key in ("problems", "ungraded_tasks", "leaks", "mismatches", "vacuous_tests"):
        value = report.get(key)
        if isinstance(value, list) and value:
            bits.append(f"{key}: {len(value)}")
    return " | ".join(bits)


def project_detail(slug: str) -> dict:
    slug = slugify(slug)
    path = project_path(slug)
    state = read_state(slug)
    summary = project_summary(path) or {}
    events = read_events(slug, limit=300)
    runs = project_runs(slug)
    workflow = read_workflow(slug)
    entries = plan_entries(path, state)
    return {
        **summary,
        "workflow": workflow,
        "state": {
            "slug": state.get("slug"),
            "created": state.get("created"),
            "flow": state.get("flow"),
            "phase": state.get("phase"),
            "retries": state.get("retries"),
            "step_runs": state.get("step_runs"),
            "gates": state.get("gates"),
            "ticket": state.get("ticket"),
            "dry_run": state.get("dry_run"),
            "feedback": state.get("feedback"),
        },
        "phases": phase_items(path, state),
        "plan": entries,
        "artifacts": artifact_list(path),
        "runs": runs,
        "events": events[-200:],   # oldest first; the page appends new ones
        "event_seq": max([int(e.get("seq") or 0) for e in events] or [0]),
        "current_execution": current_execution(path, state, summary, events),
        "gates": gate_reviews_for(path, state, include_all=True),
        "agents": [a for a in agents_view([summary]) if a["project"] in ("", slug)],
        "scripts": [s for s in scripts_view() if s["project"] in ("", slug)],
        "openrouter": openrouter_info(),
    }


def project_status_payload(slug: str, after: int = 0) -> dict:
    """The small, cheap payload the UI polls while a workflow runs."""
    slug = slugify(slug)
    path = project_path(slug)
    state = read_state(slug)
    summary = project_summary(path) or {}
    recent = read_events(slug, limit=200)          # one read, one state.json sync
    events = [e for e in recent if int(e.get("seq") or 0) > after]
    workflow = read_workflow(slug)
    runs = project_runs(slug, limit=12)
    return {
        "slug": slug,
        "status": summary.get("status"),
        "phase": summary.get("phase"),
        "phase_title": summary.get("phase_title"),
        "step": summary.get("step"),
        "step_description": summary.get("step_description"),
        "progress": summary.get("progress"),
        "completed_actions": summary.get("completed_actions"),
        "total_actions": summary.get("total_actions"),
        "retry_count": summary.get("retry_count"),
        "retry_limit": summary.get("retry_limit"),
        "ticket": summary.get("ticket"),
        "workflow": workflow,
        "phases": phase_items(path, state),
        "current_execution": current_execution(path, state, summary, recent[-5:]),
        "events": events,
        "event_seq": max([int(e.get("seq") or 0) for e in recent] or [after]),
        "runs": runs,
        "gates": [g for g in gate_reviews_for(path, state, include_all=True)
                  if g["waiting"] or g["status"] in {"approved", "rejected"}],
        "artifacts_count": len(artifact_list(path)),
        "polling": summary.get("status") in {RUNNING, QUEUED},
    }


def openrouter_info() -> dict:
    return {
        "available": bool(os.environ.get("OPENROUTER_API_KEY")),
        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
        "url": OPENROUTER_URL,
    }


def recent_activity(projects: list[dict], limit: int = 40) -> list[dict]:
    rows = []
    for project in projects:
        for event in read_events(project["slug"], limit=12):
            rows.append({**event, "project": project["slug"]})
    rows.sort(key=lambda r: str(r.get("at") or ""), reverse=True)
    return rows[:limit]


def overview() -> dict:
    projects = all_projects()
    counts = {name: 0 for name in (RUNNING, QUEUED, COMPLETED, FAILED,
                                   WAITING_FOR_REVIEW, WAITING_FOR_INPUT, BLOCKED)}
    counts["TOTAL"] = len(projects)
    for project in projects:
        counts[project["status"]] = counts.get(project["status"], 0) + 1
    reviews = []
    for project in projects:
        state = safe_json(PROJECTS / project["slug"] / ".pipeline" / "state.json", {}) or {}
        state.setdefault("slug", project["slug"])
        reviews.extend(gate_reviews_for(PROJECTS / project["slug"], state))
    return {
        "root": str(ROOT),
        "openrouter": openrouter_info(),
        "counts": counts,
        "projects": projects,
        "running": [p for p in projects if p["status"] == RUNNING],
        "queued": [p for p in projects if p["status"] in {QUEUED, WAITING_FOR_INPUT}],
        "review": [p for p in projects if p["status"] == WAITING_FOR_REVIEW],
        "completed": [p for p in projects if p["status"] == COMPLETED],
        "failed": [p for p in projects if p["status"] in {FAILED, BLOCKED}],
        "reviews": reviews,
        "activity": recent_activity(projects),
        "agents": agents_view(projects),
        "scripts": scripts_view(),
        "runs": all_runs(40),
        "retry_limit": RETRY_LIMIT,
        "step_run_limit": STEP_RUN_LIMIT,
    }


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def read_artifact(slug: str, rel_path: str) -> dict:
    slug = slugify(slug)
    project = project_path(slug).resolve()
    path = (project / rel_path).resolve()
    if not is_inside(path, project) or not path.is_file():
        raise FileNotFoundError(rel_path)
    data = path.read_bytes()
    viewable = path.suffix.lower() in TEXT_TYPES or len(data) < 512_000
    text = data.decode("utf-8", errors="replace") if viewable else ""
    return {
        "project": slug,
        "path": rel_path,
        "size": len(data),
        "kind": artifact_kind(Path(rel_path)),
        "viewable": viewable,
        "content": text[:400_000],
        "truncated": len(text) > 400_000,
    }
