"""Run state: which phase, how many retries burned, what the gates decided.

Rule 6 - retries stop at about 15, then the run stops and raises a ticket.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

RETRY_LIMIT = 15

PHASES = ("spec", "code", "pack")
GATES = {"spec": "gate1", "code": "gate2", "pack": "gate3"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def project_dir(slug: str, root: Path | None = None) -> Path:
    root = root or Path(os.environ.get("GP_ROOT", Path.cwd()))
    return root / "projects" / slug


class State:
    def __init__(self, slug: str, root: Path | None = None):
        self.slug = slug
        self.dir = project_dir(slug, root)
        self.path = self.dir / ".pipeline" / "state.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {
            "slug": self.slug,
            "created": now(),
            "phase": "spec",
            "retries": {p: 0 for p in PHASES},
            "gates": {g: None for g in GATES.values()},
            "steps": [],
            "ticket": None,
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n")

    # -- retries ----------------------------------------------------------
    def burn_retry(self, phase: str, last_error: str) -> int:
        n = self.data["retries"][phase] + 1
        self.data["retries"][phase] = n
        if n >= RETRY_LIMIT:
            self.data["ticket"] = {
                "raised": now(),
                "phase": phase,
                "retries": n,
                "last_error": last_error,
            }
        self.save()
        return n

    def exhausted(self, phase: str) -> bool:
        return self.data["retries"][phase] >= RETRY_LIMIT

    def remaining(self, phase: str) -> int:
        return max(0, RETRY_LIMIT - self.data["retries"][phase])

    # -- gates ------------------------------------------------------------
    def record_gate(self, gate: str, approved: bool, note: str = "") -> None:
        self.data["gates"][gate] = {
            "approved": approved,
            "at": now(),
            "note": note,
        }
        self.save()

    def gate_passed(self, gate: str) -> bool:
        g = self.data["gates"].get(gate)
        return bool(g and g["approved"])

    def may_enter(self, phase: str) -> tuple[bool, str]:
        """A phase is blocked until the gate before it is approved."""
        order = list(PHASES)
        i = order.index(phase)
        if i == 0:
            return True, ""
        prev_gate = GATES[order[i - 1]]
        if self.gate_passed(prev_gate):
            return True, ""
        return False, f"{prev_gate} has not been approved - phase '{phase}' is blocked"

    # -- log --------------------------------------------------------------
    def log_step(self, step: str, ok: bool, detail: str = "") -> None:
        self.data["steps"].append(
            {"step": step, "ok": ok, "at": now(), "detail": detail[:500]}
        )
        self.save()
