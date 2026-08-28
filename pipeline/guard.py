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
import os
import re
import sys
from pathlib import Path

ALWAYS_OK = (".pipeline",)
BLOCK = 2   # exit 2 = deny the tool call and show stderr to the model

# The spec, once Gate 1 has approved it. A LOCK only exists during an agent
# step, and Phase 1 sets none at all, so between steps the spec was writable by
# anything - including a finished Spec Writer that woke up an hour later and
# copied a rejected round back over the live files. This marker is written by
# `pipeline gate <slug> 1 approve` and removed by `pipeline revise`, so it
# covers every moment after approval regardless of any subtree lock.
FROZEN_MARKER = "SPEC_FROZEN"
SPEC_FILES = ("spec.json", "spec.md")

# The pipeline's own code, while an agent step is in flight.
#
# check_path only ever walked up looking for projects/<slug>/, so everything
# outside projects/ was unguarded - the checkers, the orchestrator, the agent
# prompts, and guard.py itself. Rule 1 says every agent has a checker; nothing
# said the agent could not rewrite the checker. During the phase-3 run an agent
# did exactly that: it hit a crash in cutter.py and patched cutter.py. The fix
# was good, which is luck, not a control.
#
# Keyed to a LOCK the way the spec freeze is keyed to a marker, because a
# PreToolUse hook cannot authenticate who is writing. Agent steps run under a
# lock; a person works between them. That makes this a real defence against the
# accidental case - an agent helpfully fixing a bug it should have reported -
# and no defence at all against a determined one. Worth having for the first,
# and worth being honest about for the second.
#
# learning/ is here for the same reason and a documented one: CLAUDE.md says
# lessons.md is updated between runs, never during one, and round 1 recorded it
# being edited mid-run anyway (B-08). Every agent reads it at the start, so a
# mid-run edit means two agents in the same run read different instructions.
PIPELINE_PATHS = ("pipeline", ".claude", "learning")
PIPELINE_ALLOW = (".claude/settings.local.json",)

# A shell reaches the filesystem two ways: a redirect, or a command that takes
# the file it changes as an argument. Only those are write targets. A path that
# merely appears on the line is a read - and the guard used to refuse those,
# because it scanned EVERY path token as soon as a ">" appeared anywhere on the
# line, quoted or not, so `grep ">>> CUT" app/x.ts spec.json` was blocked.
WRITES_EVERY_ARG = {"tee", "rm", "rmdir", "shred", "mv", "truncate",
                    "mkdir", "touch", "patch", "ln"}
WRITES_LAST_ARG = {"cp", "install", "rsync"}      # the sources are only read
# stepped over when looking for the command word
WRAPPERS = {"sudo", "env", "command", "time", "nohup", "exec", "nice", "xargs",
            "then", "else", "do", "!", "{", "}", "("}
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
METACHAR = "<>|;&()\n"
# a backslash before one of these is a shell escape; before anything else it is
# a Windows separator, and eating it turns C:\repo\projects\.. into C:repoprojects
ESCAPABLE = " \t'\"\\<>|;&$`"

# Git Bash hands out MSYS paths (/d/repo/projects/...) that Windows resolves
# against the wrong root, so the walk up to .pipeline/LOCK finds nothing.
MSYS_PATH = re.compile(r"^/([A-Za-z])/")


def _lex(command: str) -> list[tuple[str, str]]:
    """Tokenise a shell line into ("word"|"write"|"read"|"sep", text).

    Quote-aware, which is the whole point: a ">" inside quotes is data.
    """
    out: list[tuple[str, str]] = []
    buf: list[str] = []
    quote: str | None = None
    i, n = 0, len(command)

    def flush() -> str:
        word = "".join(buf)
        buf.clear()
        return word

    while i < n:
        c = command[i]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"' and i + 1 < n and command[i + 1] in ESCAPABLE:
                buf.append(command[i + 1])
                i += 2
                continue
            else:
                buf.append(c)
            i += 1
            continue
        if c in "'\"":
            quote = c
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            nxt = command[i + 1]
            buf.append(nxt if nxt in ESCAPABLE else c + nxt)
            i += 2
            continue
        if c in METACHAR:
            word = flush()
            if c == ">" and (word.isdigit() or word == "&"):
                word = ""                     # 2> and &> - an fd, not a path
            if word:
                out.append(("word", word))
            if c == ">":
                op = ">>" if command[i + 1:i + 2] == ">" else ">"
                i += len(op)
                if command[i:i + 1] == "|":   # >| forces the clobber
                    i += 1
                out.append(("write", op))
                continue
            if c == "<":
                i += 2 if command[i + 1:i + 2] == "<" else 1
                out.append(("read", "<"))
                continue
            if command[i + 1:i + 2] == c and c in "&|":
                i += 1
            i += 1
            out.append(("sep", c))
            continue
        if c.isspace():
            word = flush()
            if word:
                out.append(("word", word))
            i += 1
            continue
        buf.append(c)
        i += 1

    word = flush()
    if word:
        out.append(("word", word))
    return out


def _segment_targets(tokens: list[tuple[str, str]]) -> list[str]:
    """The paths one simple command writes to."""
    out: list[str] = []
    words: list[str] = []
    i = 0
    while i < len(tokens):
        kind, text = tokens[i]
        operand = (tokens[i + 1][1]
                   if i + 1 < len(tokens) and tokens[i + 1][0] == "word" else None)
        if kind == "write":
            if operand is not None:
                out.append(operand)
                i += 2
                continue
        elif kind == "read":
            i += 2 if operand is not None else 1
            continue
        else:
            words.append(text)
        i += 1

    j = 0
    while j < len(words) and (words[j] in WRAPPERS or ASSIGN.match(words[j])):
        j += 1
    if j >= len(words):
        return out
    name = re.split(r"[\\/]", words[j])[-1]
    args = words[j + 1:]
    plain = [a for a in args if not a.startswith("-")]

    if name == "sed":
        if any(a.startswith("-i") or a.startswith("--in-place") for a in args):
            out.extend(plain[1:])             # the first plain arg is the script
    elif name == "dd":
        out.extend(a.split("=", 1)[1] for a in args if a.startswith("of="))
    elif name in WRITES_EVERY_ARG:
        out.extend(plain)
    elif name in WRITES_LAST_ARG:
        named = [args[k + 1] for k, a in enumerate(args)
                 if a in ("-t", "--target-directory") and k + 1 < len(args)]
        named += [a.split("=", 1)[1] for a in args
                  if a.startswith("--target-directory=")]
        out.extend(named or plain[-1:])
    return out


def write_targets(command: str) -> list[str]:
    """Every path `command` would write, and nothing it only reads."""
    out: list[str] = []
    segment: list[tuple[str, str]] = []
    for kind, text in _lex(command):
        if kind == "sep":
            out.extend(_segment_targets(segment))
            segment = []
        else:
            segment.append((kind, text))
    out.extend(_segment_targets(segment))
    return [t for t in out if t]


def frozen_project(path: Path) -> Path | None:
    """Walk up from path to a projects/<slug>/ whose spec is frozen."""
    for parent in [path, *path.parents]:
        if parent.parent.name == "projects" and (parent / ".pipeline" / FROZEN_MARKER).exists():
            return parent
    return None


def locked_tree(path: Path) -> tuple[Path, str] | None:
    """Walk up from path to a projects/<slug>/ that holds a LOCK."""
    for parent in [path, *path.parents]:
        lock = parent / ".pipeline" / "LOCK"
        if lock.exists() and parent.parent.name == "projects":
            return parent, lock.read_text().strip()
    return None


def repo_root() -> Path:
    """The checkout this guard belongs to - guard.py lives in <root>/pipeline/."""
    return Path(__file__).resolve().parent.parent


def step_in_flight(root: Path | None = None) -> Path | None:
    """The first project holding a LOCK, meaning an agent step is running."""
    roots = [root] if root is not None else [repo_root()]
    if root is None and os.environ.get("GP_ROOT"):
        roots.append(Path(os.environ["GP_ROOT"]))
    for r in roots:
        for lock in r.glob("projects/*/.pipeline/LOCK"):
            return lock.parent.parent
    return None


def check_pipeline(target: Path) -> str | None:
    """Rule 5, the half nobody wrote down: an agent does not edit the pipeline.

    The orchestrator is plain code precisely so that no agent manages another.
    An agent that rewrites a checker manages every agent that checker judges -
    including itself.
    """
    root = repo_root()
    try:
        rel = target.relative_to(root)
    except ValueError:
        return None
    if not rel.parts or rel.parts[0] not in PIPELINE_PATHS:
        return None
    if rel.as_posix() in PIPELINE_ALLOW:
        return None
    project = step_in_flight()
    if project is None:                  # no step running: a person is working
        return None
    return (f"blocked by the pipeline write guard: {rel.as_posix()} is the pipeline's own "
            f"code, and an agent step is in flight ({project.name} holds a LOCK).\n"
            f"Rule 5 - the orchestrator is plain code, and no agent manages another. An "
            f"agent that rewrites a checker manages every agent that checker judges, "
            f"itself included.\n"
            f"If the pipeline is genuinely broken, SAY SO IN YOUR SUMMARY and stop. A "
            f"person fixes the pipeline between steps. Reporting a defect you cannot fix "
            f"is the expected outcome, not a failure.")


def check_path(target: Path) -> str | None:
    target = target if target.is_absolute() else (Path.cwd() / target)
    try:
        target = target.resolve()
    except OSError:
        return None
    # the pipeline's own code, while any agent step is running
    msg = check_pipeline(target)
    if msg:
        return msg
    # the frozen spec is refused even with no lock set
    if target.name in SPEC_FILES:
        project = frozen_project(target.parent)
        if project is not None:
            h = (project / ".pipeline" / FROZEN_MARKER).read_text().strip()[:12]
            return (f"blocked by the pipeline write guard: {project.name}/{target.name} was "
                    f"approved at Gate 1 (spec {h}) and is frozen.\n"
                    f"app/, verify/ and skeleton/ were built against it, so editing it now "
                    f"silently breaks the link between the spec and the code.\n"
                    f"If the spec is genuinely wrong, say so in your summary. Reopening it "
                    f"is a person's decision: `python -m pipeline revise {project.name}` "
                    f"archives this round and sends the spec back through Gate 1.")

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
    for token in write_targets(command):
        if sys.platform == "win32":
            token = MSYS_PATH.sub(r":/", token)
        try:
            target = Path(token)
        except ValueError:            # a token no filesystem could name
            continue
        msg = check_path(target)
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
