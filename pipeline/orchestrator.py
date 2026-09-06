"""The auto-runner. Plain code, in the spirit of rule 5 - no agent manages another.

It reads the plan out of `ui_core.plan_entries`, runs the first action that has
not happened, and repeats. It stops - it does not decide - at exactly the points
the pipeline says a person decides:

* a **gate**  -> WAITING_FOR_REVIEW. Only `pipeline gate` moves it.
* a **person** step (the stack, the timed dry run) -> WAITING_FOR_INPUT.
* a raised **ticket**, an exhausted phase, or a churning step -> BLOCKED. Those
  are rule 6 and rule 7 as `state.py` already implements them; nothing here
  raises or clears them.

The one thing this module adds is a *loop guard*. Some checkers burn a retry when
they reject - `lint`, `test`, `mutation` - and rule 6 stops those at fifteen.
Others do not: the Gate 1 stopping rule sends a spec back to the writer without
touching the counter, and spec-writer -> lint -> breaker -> gate1-check -> reject
is a cycle that would otherwise run forever on somebody's OpenRouter bill. So an
action also stops after `GUARD_REPEATS` runs in which neither the plan nor the
retry counter moved. That is not a second retry rule - rule 6 is still the
authority and both numbers are shown side by side - it is a stop on a cycle with
nothing at the end of it, and Start Workflow runs it again.
"""
from __future__ import annotations

import os
import threading
import time

from . import ui_core as core
from . import ui_runner as runner
from .state import RETRY_LIMIT, State

GUARD_REPEATS = int(os.environ.get("UI_ORCHESTRATOR_GUARD", "3"))
_THREADS: dict[str, threading.Thread] = {}
_STOP: dict[str, bool] = {}
_LOCK = threading.Lock()

IDLE = "idle"
RUNNING = "running"
PAUSED = "paused"
BLOCKED = "blocked"
WAITING_REVIEW = "waiting_review"
WAITING_INPUT = "waiting_input"
COMPLETED = "completed"


def is_running(slug: str) -> bool:
    with _LOCK:
        thread = _THREADS.get(slug)
    return bool(thread and thread.is_alive())


def status(slug: str) -> dict:
    data = core.read_workflow(slug)
    data["thread_alive"] = is_running(slug)
    if data.get("state") == RUNNING and not data["thread_alive"]:
        data["state"] = data.get("last_pause_state") or IDLE
    return data


def start(slug: str, *, single: bool = False) -> dict:
    """Start (or resume) the auto-run. Idempotent - a second call is a no-op."""
    slug = core.slugify(slug)
    core.read_state(slug)                       # raises if the project is unknown
    with _LOCK:
        if _THREADS.get(slug) and _THREADS[slug].is_alive():
            return {"slug": slug, "started": False,
                    "reason": "the workflow is already running", **status(slug)}
        _STOP[slug] = False
        thread = threading.Thread(target=_loop, args=(slug, single), daemon=True,
                                  name=f"workflow-{slug}")
        _THREADS[slug] = thread
    core.write_workflow(slug, state=RUNNING, reason="", mode="single step" if single else "auto",
                        started=core.now_iso(), stopped=None)
    core.log_event(slug, "Workflow run started" if not single else "Single step requested",
                   level="ok", kind="workflow",
                   detail="the orchestrator runs each step and stops at every human gate")
    thread.start()
    return {"slug": slug, "started": True, **status(slug)}


def stop(slug: str) -> dict:
    slug = core.slugify(slug)
    with _LOCK:
        _STOP[slug] = True
    core.log_event(slug, "Pause requested", level="warn", kind="workflow",
                   detail="the orchestrator stops after the action in flight finishes")
    core.write_workflow(slug, stop_requested=True)
    return status(slug)


def _stop_requested(slug: str) -> bool:
    with _LOCK:
        return bool(_STOP.get(slug))


def _pause(slug: str, state_name: str, reason: str, level: str = "info") -> None:
    core.write_workflow(slug, state=state_name, reason=reason,
                        last_pause_state=state_name, stopped=core.now_iso(),
                        stop_requested=False)
    core.log_event(slug, f"Workflow {state_name.replace('_', ' ')}", level=level,
                   kind="workflow", detail=reason)


def plan_signature(slug: str) -> tuple:
    project = core.project_path(slug)
    state = core.read_state(slug)
    return tuple((e["step"], e["component"], e["done"])
                 for e in core.plan_entries(project, state))


def plan_done(slug: str) -> int:
    project = core.project_path(slug)
    state = core.read_state(slug)
    return sum(1 for e in core.plan_entries(project, state) if e["done"])


def retries_burned(slug: str) -> int:
    return sum(int(v) for v in (core.read_state(slug).get("retries") or {}).values())


def hard_stop(slug: str) -> tuple[str, str] | None:
    """Rule 6 and rule 7, read straight off state.json. Never raised here."""
    st = State(slug, core.ROOT)
    ticket = st.data.get("ticket")
    if ticket:
        return (BLOCKED,
                f"a ticket is open on the {ticket.get('phase')} phase "
                f"({ticket.get('kind', 'code problem')}): {ticket.get('last_error', '')}. "
                f"Rule 6 stops the run at {RETRY_LIMIT} retries; a person fixes it "
                f"between steps.")
    churn = st.churning()
    if churn:
        return BLOCKED, churn
    return None


def next_action(slug: str) -> dict | None:
    project = core.project_path(slug)
    state = core.read_state(slug)
    return core.failed_repair(project, state) or core.next_action(project, state)


def run_action(slug: str, action: dict, *, auto: bool) -> dict:
    """Execute one planned action synchronously and return its finished record."""
    kind = action["kind"]
    if kind == "agent":
        return runner.run_agent(action["component"], slug, auto=auto,
                                step=action.get("step"), wait=True,
                                repair_of=action.get("repair_of", ""))
    if kind == "script":
        return runner.run_script(action["component"], slug, auto=auto,
                                 step=action.get("step"), wait=True)
    raise ValueError(f"{kind} steps are a human decision, not an automatic run")


def step_once(slug: str) -> dict:
    """Run exactly one action, in the foreground, and report what happened."""
    slug = core.slugify(slug)
    blocked = hard_stop(slug)
    if blocked:
        _pause(slug, *blocked, level="error")
        return {"slug": slug, "ran": False, "state": blocked[0], "reason": blocked[1]}
    action = next_action(slug)
    if action is None:
        _pause(slug, COMPLETED, "every step in the flow is done")
        return {"slug": slug, "ran": False, "state": COMPLETED,
                "reason": "the workflow is complete"}
    if action["kind"] in {"gate", "person"}:
        state_name = WAITING_REVIEW if action["kind"] == "gate" else WAITING_INPUT
        reason = f"{action['label']}: {action.get('note') or action.get('description', '')}"
        _pause(slug, state_name, reason)
        return {"slug": slug, "ran": False, "state": state_name, "reason": reason,
                "action": action}
    record = run_action(slug, action, auto=False)
    return {"slug": slug, "ran": True, "state": IDLE, "run": record, "action": action}


def _loop(slug: str, single: bool) -> None:
    # The loop guard. Some checkers burn a retry when they fail - `lint`, `test`,
    # `mutation` - and rule 6 stops those at 15. Others do not: `gate1-check`
    # rejecting sends the spec back to the writer without touching the counter,
    # and that is a cycle with nothing at the end of it. So an action also stops
    # after GUARD_REPEATS runs in which NEITHER the plan's high-water mark NOR
    # the pipeline's own retry count moved. When either moves the count resets,
    # and rule 6 stays the authority on retries.
    attempts: dict[tuple, int] = {}
    marks: dict[tuple, tuple[int, int]] = {}
    high = plan_done(slug)
    try:
        while True:
            if _stop_requested(slug):
                _pause(slug, PAUSED, "paused by a person", level="warn")
                return

            blocked = hard_stop(slug)
            if blocked:
                _pause(slug, *blocked, level="error")
                return

            project = core.project_path(slug)
            state = core.read_state(slug)
            repair = core.failed_repair(project, state)
            action = repair or core.next_action(project, state)

            if action is None:
                _pause(slug, COMPLETED, "every step in the flow is done", level="ok")
                return

            if action["kind"] == "gate":
                gate = action["component"]
                if core.gate_rejected(state, gate):
                    _pause(slug, WAITING_INPUT,
                           f"{gate} was rejected. Archive the round with Revise, or fix "
                           f"the findings and approve it - the pipeline does not step "
                           f"past a rejected gate on its own.", level="warn")
                    return
                _pause(slug, WAITING_REVIEW,
                       f"{core.GATE_TITLES.get(gate, gate)}. "
                       f"{action.get('note', '')}".strip(), level="warn")
                return

            if action["kind"] == "person":
                _pause(slug, WAITING_INPUT,
                       f"step {action['step']} needs a person: {action.get('note') or action['label']}",
                       level="warn")
                return

            phase = action["phase"]
            burned = int((state.get("retries") or {}).get(phase, 0))
            if burned >= RETRY_LIMIT:
                _pause(slug, BLOCKED,
                       f"the {phase} phase has burned {burned}/{RETRY_LIMIT} retries",
                       level="error")
                return

            if action["kind"] == "agent" and not os.environ.get("OPENROUTER_API_KEY"):
                _pause(slug, BLOCKED,
                       f"step {action['step']} needs the {action['component']} agent, but "
                       f"OPENROUTER_API_KEY is not set. Set it in .env and restart the UI, "
                       f"or run this step from Claude Code with "
                       f"{core.WORKFLOW_BY_PHASE.get(phase, '')}", level="error")
                return

            key = (action["kind"], action["component"], action.get("repair_of", ""))
            burned_now = retries_burned(slug)
            was = marks.get(key)
            if was and (high > was[0] or burned_now > was[1]):
                attempts[key] = 0              # something moved since this last ran
            marks[key] = (high, burned_now)
            attempts[key] = attempts.get(key, 0) + 1
            if attempts[key] > GUARD_REPEATS:
                _pause(slug, BLOCKED,
                       f"{action['label']} has run {attempts[key] - 1} times in this run "
                       f"without the workflow moving forward and without the pipeline "
                       f"burning a retry ({burned_now} burned, {RETRY_LIMIT} per phase is "
                       f"the limit). That is a cycle with nothing at the end of it, so the "
                       f"auto-run stops for a person to look. Nothing is blocked - Start "
                       f"Workflow runs it again.", level="error")
                return

            before = plan_signature(slug)
            record = run_action(slug, action, auto=True)
            after = plan_signature(slug)
            moved = before != after
            ok = record.get("status") == "succeeded"
            high = max(high, plan_done(slug))

            if not ok and not moved:
                core.log_event(
                    slug, f"{action['label']} failed - re-planning",
                    level="warn", kind="workflow", component=action["component"],
                    phase=phase, step=action.get("step"),
                    detail=(record.get("stderr") or record.get("stdout") or "")[-600:])

            if single:
                _pause(slug, IDLE, "single step finished")
                return
            time.sleep(0.2)
    except Exception as exc:                              # never leave it "running"
        _pause(slug, BLOCKED, f"the orchestrator crashed: {type(exc).__name__}: {exc}",
               level="error")
    finally:
        with _LOCK:
            _STOP.pop(slug, None)
        data = core.read_workflow(slug)
        if data.get("state") == RUNNING:
            core.write_workflow(slug, state=IDLE, reason="the run ended")
