"""Write guard - SCRIPT, enforces rule 3.

"The Builder cannot edit test files. If it could, it would change the test
instead of fixing the code."

Prose in a prompt is not enforcement. The orchestrator locks one subtree per
step; this runs as a PreToolUse hook and blocks any write outside it.

  python -m pipeline lock   <slug> app|verify|pack|skeleton
  python -m pipeline unlock <slug>

Locks live at projects/<slug>/.pipeline/LOCK. No lock means no restriction, so
ordinary work in this repo is untouched.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ALWAYS_OK = (".pipeline",)
BLOCK = 2   # exit 2 = deny the tool call and show stderr to the model

# a write reaching the filesystem through a shell instead of the Write tool
REDIRECT = re.compile(r"(>>?|\btee\b|\bcp\b|\bmv\b|\bsed\b\s+-i|\brm\b|\bdd\b|"
                      r"\btruncate\b|\bmkdir\b|\btouch\b|\bpatch\b)")


def locked_tree(path: Path) -> tuple[Path, str] | None:
    """Walk up from path to a projects/<slug>/ that holds a LOCK."""
    for parent in [path, *path.parents]:
        lock = parent / ".pipeline" / "LOCK"
        if lock.exists() and parent.parent.name == "projects":
            return parent, lock.read_text().strip()
    return None


def check_path(target: Path) -> str | None:
    target = target if target.is_absolute() else (Path.cwd() / target)
    try:
        target = target.resolve()
    except OSError:
        return None
    found = locked_tree(target.parent)
    if not found:
        return None
    project, allowed = found
    try:
        rel = target.relative_to(project)
    except ValueError:
        return None
    top = rel.parts[0] if rel.parts else ""
    if top == allowed or top in ALWAYS_OK:
        return None
    return (f"blocked by the pipeline write guard: this step may only write to "
            f"{project.name}/{allowed}/, and {rel} is outside it.\n"
            f"Rule 3 - the Builder cannot edit test files, and the Verifier cannot "
            f"edit the code it is testing.\n"
            f"If the file you need to change is genuinely wrong, say so in your "
            f"summary and fix what is inside {allowed}/ instead.")


def check_bash(command: str) -> str | None:
    if not REDIRECT.search(command):
        return None
    for token in re.findall(r"[\w./~-]*projects/[\w./-]+", command):
        msg = check_path(Path(token))
        if msg:
            return msg
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0                     # never break the session on a malformed event
    tool = event.get("tool_name", "")
    ti = event.get("tool_input", {}) or {}

    msg = None
    if tool in ("Write", "Edit", "NotebookEdit"):
        p = ti.get("file_path") or ti.get("notebook_path")
        if p:
            msg = check_path(Path(p))
    elif tool == "Bash":
        msg = check_bash(ti.get("command", "") or "")

    if msg:
        print(msg, file=sys.stderr)
        return BLOCK
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
