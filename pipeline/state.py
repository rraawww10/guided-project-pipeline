"""Run state: which phase, how many retries burned, what the gates decided.

Rule 6 - retries stop at about 15, then the run stops and raises a ticket.

Two additions after round 1:

* `spec_hash` / `SPEC_FROZEN`. Nothing tied the approved spec to the code built
  from it. recipe-box built app/ and verify/ against a round-4 spec that existed
  only in the working tree, and a finished Spec Writer woke up an hour later and
  copied a rejected round over the live files. The hash is the binding; the
  freeze marker is the lock.
* `step_runs`. `burn_retry` only fires when a checker FAILS, so recipe-box
  logged 10 clean lint runs and 6 clean test runs with retries still at 0/15.
  Rule 6 guarded a failing loop and not a thrashing green one.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RETRY_LIMIT = 15
# A cap on *successful* re-runs of one step. Not a retry - a green step that
# keeps being re-run. recipe-box's worst observed was 10 lint runs in 15
# minutes, so this is deliberately well above normal churn and only stops a
# genuine loop.
STEP_RUN_LIMIT = 30

# requirements_doc.md adds a phase in front (stack -> ideas -> Gate 0) and a
# fourth gate. The three projects already shipped were built under the old
# three-gate flow and must keep working, so the flow is versioned:
#
#   flow 1  legacy: spec -> code -> pack, gates 1-3. No gate0.
#   flow 2  current: idea -> spec -> code -> pack, gates 0-3.
#
# A state file with no "flow" key is flow 1. `pipeline new` writes flow 2.
FLOW_LATEST = 2

PHASES_BY_FLOW = {
    1: ("spec", "code", "pack"),
    2: ("idea", "spec", "code", "pack"),
}
GATES_BY_FLOW = {
    1: {"spec": "gate1", "code": "gate2", "pack": "gate3"},
    2: {"idea": "gate0", "spec": "gate1", "code": "gate2", "pack": "gate3"},
}

# Module-level names kept for the callers that predate the flow split. They are
# the union, so `GATES[phase]` still answers for every phase either flow has.
PHASES = PHASES_BY_FLOW[2]
GATES = GATES_BY_FLOW[2]

# Rule 7: the ticket says whether the run stopped on a code problem, which stays
# in the code phase, or a spec problem, which goes back to the spec writer.
TICKET_KINDS = ("code problem", "spec problem")

# the files that make up "the spec", in hash order
SPEC_FILES = ("spec.json", "spec.md")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def project_dir(slug: str, root: Path | None = None) -> Path:
    root = root or Path(os.environ.get("GP_ROOT", Path.cwd()))
    return root / "projects" / slug


def spec_hash(project: Path) -> str | None:
    """A stable digest of the spec as a whole. None if either file is missing.

    Both files, in a fixed order, with the name mixed in - so moving text from
    spec.md to spec.json changes the hash.
    """
    h = hashlib.sha256()
    for name in SPEC_FILES:
        p = project / name
        if not p.exists():
            return None
        h.update(name.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def verify_hash(project: Path) -> str | None:
    """A stable digest of the whole verify/ tree. None if there is no tree.

    Gate 1 approves the tests as well as the plan, and pipeline-test-02's Gate 2
    note claimed "verify/ byte-identical to the Gate 1 commit" - which was true,
    and which nothing checked. It was read off git by hand. In flow 2 the
    Verifier legitimately writes verify/ at step 8, AFTER Gate 1, so byte
    identity is not a property Gate 2 can assume; pipeline-test-03's Verifier
    added a timeout to helpers.py and the claim would have been false.

    What Gate 2 can do is say plainly whether the suite moved, so the human
    reads the diff instead of assuming either way. Paths are mixed in, so a
    renamed or deleted test changes the hash.
    """
    root = project / "verify"
    if not root.is_dir():
        return None
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        if "__pycache__" in f.parts:
            continue
        h.update(str(f.relative_to(root)).replace(chr(92), "/").encode())
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def app_hash(project: Path) -> str | None:
    """A stable digest of app/ source, ignoring build and install output.

    The skeleton is a snapshot of app/ taken at step 10, and nothing bound the
    two. demo-run-03 shipped with app/ on next 16.1.1 and an awaited `params`,
    while skeleton/ - cut twenty minutes earlier - still pinned next@14.2.5,
    which npm flags as vulnerable. Every gate was truthful when it ran: Gate 2
    was approved before the fix, `cut` ran before the fix, and `deploy` only
    ever builds app/. Rule 8 says a later edit re-enters at step 7, but that was
    a rule for people and nothing enforced it.

    Same idea as ambiguity.md bound to a spec hash (rule 7): a report has to
    name the thing it read.
    """
    root = project / "app"
    if not root.is_dir():
        return None
    skip = {"node_modules", ".next", "__pycache__", ".turbo", "dist", "build",
            ".git", "coverage"}
    h = hashlib.sha256()
    for f in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = f.relative_to(root)
        if skip & set(rel.parts):
            continue
        if rel.suffix in {".db", ".sqlite", ".sqlite3", ".log", ".tsbuildinfo"}:
            continue          # runtime state, not source
        h.update(str(rel).replace(chr(92), "/").encode())
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def skeleton_stale(project: Path) -> str:
    """'' when the skeleton was cut from the app that is on disk now."""
    import json as _json
    report = project / "skeleton-check.json"
    if not (project / "skeleton").is_dir() or not report.exists():
        return ""
    try:
        was = (_json.loads(report.read_text(encoding="utf-8")) or {}).get("app_hash")
    except Exception:
        return ""
    if not was:
        return ""                     # cut before this check existed
    now = app_hash(project)
    if now and was != now:
        return (f"skeleton/ was cut from app {was[:12]} but app/ is now {now[:12]} - "
                f"the student tree is a snapshot of code that has since changed. "
                f"Re-run `pipeline cut`.")
    return ""


def frozen_hash(project: Path) -> str | None:
    """The spec hash recorded when Gate 1 was approved, if it was."""
    marker = project / ".pipeline" / "SPEC_FROZEN"
    if not marker.exists():
        return None
    return marker.read_text(encoding="utf-8").strip() or None


def spec_drift(project: Path) -> str | None:
    """Fail-closed check: has the spec changed since Gate 1 approved it?

    Returns None when there is nothing to check or nothing has changed, else a
    message naming the drift. Every phase after Gate 1 calls this.
    """
    want = frozen_hash(project)
    if want is None:
        return None
    got = spec_hash(project)
    if got is None:
        return ("spec.json or spec.md is missing, but Gate 1 approved a spec "
                f"(frozen {want[:12]}). The code was built against a spec that is "
                "no longer on disk.")
    if got != want:
        return (f"the spec has changed since Gate 1 approved it.\n"
                f"  approved: {want}\n  on disk:  {got}\n"
                f"The approved copy is in .pipeline/approved/. Either restore it, or "
                f"run `pipeline revise <slug>` and take the new spec through Gate 1 "
                f"on its own merits - app/ and verify/ were built against the "
                f"approved one.")
    return None


class State:
    def __init__(self, slug: str, root: Path | None = None):
        self.slug = slug
        self.dir = project_dir(slug, root)
        self.path = self.dir / ".pipeline" / "state.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            d = json.loads(self.path.read_text(encoding="utf-8"))
            d.setdefault("step_runs", {})
            d.setdefault("flow", 1)          # written before the flow was versioned
            d.setdefault("dry_run", None)
            d.setdefault("feedback", [])
            for ph in PHASES_BY_FLOW[d["flow"]]:
                d.setdefault("retries", {}).setdefault(ph, 0)
            return d
        return {
            "slug": self.slug,
            "created": now(),
            "flow": FLOW_LATEST,
            "phase": PHASES_BY_FLOW[FLOW_LATEST][0],
            "retries": {p: 0 for p in PHASES_BY_FLOW[FLOW_LATEST]},
            "step_runs": {},
            "gates": {g: None for g in GATES_BY_FLOW[FLOW_LATEST].values()},
            "steps": [],
            "ticket": None,
            "dry_run": None,
            "feedback": [],
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")

    # -- retries ----------------------------------------------------------
    def burn_retry(self, phase: str, last_error: str,
                   kind: str = "code problem") -> int:
        """Rule 7: on the fifteenth try the run stops and files a ticket, and the
        ticket says which kind of problem it is - a code problem stays in the
        code phase, a spec problem goes back to the spec writer at step 3."""
        n = self.data["retries"][phase] + 1
        self.data["retries"][phase] = n
        if n >= RETRY_LIMIT:
            if kind not in TICKET_KINDS:
                kind = "code problem"
            self.data["ticket"] = {
                "raised": now(),
                "phase": phase,
                "kind": kind,
                "retries": n,
                "last_error": last_error,
                "re_enter_at": 3 if kind == "spec problem" else 7,
            }
        self.save()
        return n

    # -- step 13, the timed dry run --------------------------------------
    def record_dry_run(self, session: int, minutes: int, by: str,
                       taught: bool, note: str = "") -> None:
        self.data["dry_run"] = {
            "at": now(), "session": session, "minutes": minutes,
            "by": by, "taught_without_the_code": taught, "note": note,
        }
        self.save()

    # -- step 15, feedback intake ----------------------------------------
    def record_feedback(self, note: str, session: int | None = None,
                        by: str = "") -> dict:
        entry = {"at": now(), "session": session, "by": by, "note": note,
                 "re_enter_at": 3}
        self.data.setdefault("feedback", []).append(entry)
        self.save()
        return entry

    def exhausted(self, phase: str) -> bool:
        return self.data["retries"][phase] >= RETRY_LIMIT

    def remaining(self, phase: str) -> int:
        return max(0, RETRY_LIMIT - self.data["retries"][phase])

    # -- step runs --------------------------------------------------------
    def runs_of(self, step: str) -> int:
        return self.data.get("step_runs", {}).get(step, 0)

    def churning(self) -> str | None:
        """Any step past STEP_RUN_LIMIT, pass or fail. Fail-closed on a loop
        that never goes red."""
        for step, n in sorted(self.data.get("step_runs", {}).items()):
            if n >= STEP_RUN_LIMIT:
                return (f"step '{step}' has run {n} times (limit {STEP_RUN_LIMIT}). "
                        f"A step that keeps re-running while its checker stays green "
                        f"is a loop, not progress.")
        return None

    # -- gates ------------------------------------------------------------
    def record_gate(self, gate: str, approved: bool, note: str = "",
                    extra: dict | None = None) -> None:
        self.data["gates"][gate] = {
            "approved": approved,
            "at": now(),
            "note": note,
            **(extra or {}),
        }
        self.save()

    def gate_passed(self, gate: str) -> bool:
        g = self.data["gates"].get(gate)
        return bool(g and g["approved"])

    # -- flow ------------------------------------------------------------
    @property
    def flow(self) -> int:
        return self.data.get("flow", 1)

    @property
    def phases(self) -> tuple[str, ...]:
        return PHASES_BY_FLOW[self.flow]

    @property
    def gates(self) -> dict[str, str]:
        return GATES_BY_FLOW[self.flow]

    def may_enter(self, phase: str) -> tuple[bool, str]:
        """A phase is blocked until the gate before it is approved.

        Flow-aware: a legacy project has no gate0, so its first phase is 'spec'
        and nothing stands in front of it.
        """
        order = list(self.phases)
        if phase not in order:
            return True, ""            # a phase this flow does not have
        i = order.index(phase)
        if i == 0:
            return True, ""
        prev_gate = self.gates[order[i - 1]]
        if self.gate_passed(prev_gate):
            return True, ""
        return False, f"{prev_gate} has not been approved - phase '{phase}' is blocked"

    # -- log --------------------------------------------------------------
    def log_step(self, step: str, ok: bool, detail: str = "") -> None:
        runs = self.data.setdefault("step_runs", {})
        runs[step] = runs.get(step, 0) + 1
        self.data["steps"].append(
            {"step": step, "ok": ok, "at": now(), "detail": detail[:500],
             "run": runs[step]}
        )
        self.save()
