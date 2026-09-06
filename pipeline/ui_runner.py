"""Execution layer: the two things the UI can actually run.

* a **script** step is `python -m pipeline <subcommand> <slug>` - the same CLI a
  person runs in a terminal, in a subprocess, with its real exit code.
* an **agent** step is the agent's own prompt (`.claude/agents/<name>.md`) plus
  its skill (`.claude/skills/<name>/SKILL.md`) driven against OpenRouter with a
  small filesystem tool set.

Nothing here decides what should run - `orchestrator.py` does that - and nothing
here writes pipeline state. The CLI owns state.json; this module owns only the
run ledger and the event log.

Three rules from CLAUDE.md are enforced on the agent tool calls, because
`guard.py` is a Claude Code hook and cannot see this runner:

* rule 3 - the Builder may not write `verify/`
* rule 4 - nothing may write `skeleton/` by hand
* rule 5 - no agent may write `pipeline/`, `.claude/` or `learning/`, and no
  agent may run a gate command. Humans decide.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError

from . import ui_core as core
from . import test_runner
from .test_runner import PYTEST_DEPS
from .ui_core import (AGENT_PHASES, DEFAULT_OPENROUTER_MODEL, OPENROUTER_URL,
                      PROJECTS, ROOT, SCRIPT_COMMANDS, STEP_AGENT_ALIASES)

# Where each agent is allowed to write, relative to its project directory.
# Anything else in the repo is refused by the tool layer.
AGENT_WRITE_SCOPES = {
    "idea-generator": ["ideas/"],
    "spec-writer": ["spec.md", "spec.json"],
    "spec-breaker": ["ambiguity.md"],
    "test-writer": ["verify/"],
    "builder": ["app/"],
    "verifier": ["verify/"],
    "pack-writer": ["pack/"],
}
# Subcommands an agent may never run: the gates and the human records.
HUMAN_ONLY_COMMANDS = ("gate", "pick", "dryrun", "feedback", "ship", "revise", "new")
BANNED_COMMAND_FRAGMENTS = ("git reset --hard", "git checkout --", "git clean",
                            "rm -rf", "remove-item", "del /s", "rmdir /s",
                            "format ", "shutdown", "mkfs")
MAX_TOOL_ROUNDS = int(os.environ.get("UI_AGENT_MAX_ROUNDS", "80"))
AGENT_TIMEOUT = int(os.environ.get("UI_AGENT_HTTP_TIMEOUT", "300"))
# Cap the output OpenRouter reserves per call. Without it OpenRouter reserves the
# model's ceiling - 65536 tokens, $0.66 at gpt-5 - and returns 402 whenever the
# key's remaining balance is under that, however few tokens the call would really
# use. A step that spends $0.08 must not be refused against a $0.62 balance.
# Kept well above what a tool call needs: a reasoning model bills its thinking as
# output too, and a turn cut off at the cap is a truncated tool call, so the
# ceiling is checked below rather than trusted.
MAX_OUTPUT_TOKENS = int(os.environ.get("UI_AGENT_MAX_OUTPUT_TOKENS", "16000"))
# A dropped connection is not a verdict about the work. demo-run-02's pack
# writer "failed" three times at 16:52:37, :38 and :39 - one second apart, all
# three `getaddrinfo failed`, because the orchestrator re-planned instantly into
# the same dead resolver. DNS was back a few minutes later and the same step
# succeeded untouched. Retry the transport, with room for it to recover.
NETWORK_RETRIES = int(os.environ.get("UI_AGENT_NETWORK_RETRIES", "3"))
NETWORK_BACKOFF = float(os.environ.get("UI_AGENT_NETWORK_BACKOFF", "4"))


def pipeline_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GP_ROOT"] = str(ROOT)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # Python block-buffers stdout when it is a pipe, so without this a checker's
    # output arrives all at once when it exits - which is the whole minute the
    # page is meant to be showing progress for.
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def pipeline_python_args() -> list[str]:
    return [sys.executable, "-X", "utf8", "-m", "pipeline"]


def require(value, name: str) -> None:
    if value in (None, ""):
        raise ValueError(f"{name} is required")


def new_run(slug: str | None, kind: str, component: str, label: str, *,
            phase: str = "", step=None, args=None, auto: bool = False,
            model: str = "", provider: str = "") -> dict:
    run_id = uuid.uuid4().hex[:12]
    record = {
        "id": run_id,
        "slug": slug,
        "kind": kind,
        "component": component,
        "label": label,
        "phase": phase,
        "step": step,
        "attempt": core.attempt_number(slug, component) if slug else 1,
        "args": args or [],
        "status": "running",
        "started": time.time(),
        "started_at": core.now_iso(),
        "finished": None,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "auto": auto,
        "model": model,
        "provider": provider,
    }
    core.register_run(record)
    if slug:
        core.log_event(
            slug, f"{label} started", level="info", kind=kind, component=component,
            phase=phase, step=step, run_id=run_id,
            detail=(f"attempt {record['attempt']}"
                    + (f" - {provider} {model}" if provider else "")
                    + (" (auto)" if auto else "")))
    return record


def finish_run(record: dict, ok: bool, *, returncode: int | None = None,
               stdout: str = "", stderr: str = "", detail: str = "") -> dict:
    finished = core.update_run(
        record["id"], status="succeeded" if ok else "failed", finished=time.time(),
        finished_at=core.now_iso(), returncode=returncode,
        stdout=(stdout or core.get_run(record["id"]).get("stdout", ""))[-60_000:],
        stderr=stderr[-20_000:])
    if record.get("slug"):
        duration = round((finished.get("finished") or 0) - (finished.get("started") or 0), 1)
        core.log_event(
            record["slug"],
            f"{record['label']} {'completed' if ok else 'FAILED'}",
            level="ok" if ok else "error", kind=record["kind"],
            component=record["component"], phase=record.get("phase", ""),
            step=record.get("step"), run_id=record["id"],
            detail=(detail or (stderr or stdout or ""))[:800] + f" [{duration}s]")
    return finished


# --------------------------------------------------------------------------
# scripts
# --------------------------------------------------------------------------
def script_args(script: str, slug: str | None) -> list[str]:
    meta = SCRIPT_COMMANDS.get(script)
    if not meta:
        raise ValueError(f"unsupported script: {script}")
    args = list(meta["args"])
    if not meta.get("no_slug"):
        require(slug, "slug")
        args.append(slug)
    if meta.get("mode"):
        args.append(meta["mode"])
    return args


def run_script(script: str, slug: str | None, *, auto: bool = False,
               step=None, wait: bool = False) -> dict:
    args = script_args(script, slug)
    meta = SCRIPT_COMMANDS[script]
    record = new_run(slug, "script", script, core.SCRIPT_LABELS.get(script, script),
                     phase=meta.get("phase", ""), step=step, args=args, auto=auto)
    return _spawn(record, lambda: _run_cli(args, record["id"]),
                  wait=wait, slug=slug, script=script)


def run_command(args: list[str], slug: str | None, component: str, label: str, *,
                kind: str = "human", auto: bool = False, wait: bool = False) -> dict:
    record = new_run(slug, kind, component, label, args=args, auto=auto)
    return _spawn(record, lambda: _run_cli(args, record["id"]), wait=wait, slug=slug)


def _run_cli(args: list[str], run_id: str = "") -> tuple[int, str, str]:
    """Run a pipeline subcommand, streaming its output into the run ledger.

    A line at a time rather than one buffer at the end: `test` and `deploy` do
    an npm install and a build, which is minutes of silence otherwise, and a
    blank box for minutes is exactly what this UI exists to stop.
    """
    proc = subprocess.Popen(
        [*pipeline_python_args(), *args], cwd=str(ROOT), env=pipeline_env(),
        text=True, encoding="utf-8", errors="replace", bufsize=1,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    chunks: list[str] = []
    if proc.stdout is not None:
        for line in proc.stdout:
            chunks.append(line)
            if run_id:
                core.append_run_output(run_id, line)
    proc.wait()
    return proc.returncode, "".join(chunks), ""


def _spawn(record: dict, work, *, wait: bool, slug: str | None = None,
           script: str | None = None) -> dict:
    result: dict = {}

    def worker() -> None:
        try:
            code, out, err = work()
        except Exception as exc:                       # a crash is a failed run
            finish_run(record, False, returncode=1, stderr=f"{type(exc).__name__}: {exc}")
            result.update(core.get_run(record["id"]) or {})
            return
        detail = ""
        if slug and script:
            detail = core.script_report_summary(core.project_path(slug), script)
        finished = finish_run(record, code == 0, returncode=code, stdout=out,
                              stderr=err, detail=detail)
        result.update(finished)

    if wait:
        worker()
        return core.get_run(record["id"]) or result or record
    threading.Thread(target=worker, daemon=True).start()
    return record


# --------------------------------------------------------------------------
# agents
# --------------------------------------------------------------------------
def run_agent(agent_name: str, slug: str, *, auto: bool = False, step=None,
              wait: bool = False, repair_of: str = "") -> dict:
    agent_name = STEP_AGENT_ALIASES.get(agent_name, agent_name)
    if agent_name not in AGENT_PHASES:
        raise ValueError(f"unsupported agent: {agent_name}")
    slug = core.slugify(slug)
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    record = new_run(slug, "agent", agent_name, agent_name,
                     phase=AGENT_PHASES[agent_name], step=step, auto=auto,
                     model=model, provider="OpenRouter")
    if repair_of:
        core.update_run(record["id"], repair_of=repair_of)

    def work() -> tuple[int, str, str]:
        output = drive_agent(agent_name, slug, record["id"], repair_of=repair_of)
        return 0, output, ""

    return _spawn(record, work, wait=wait, slug=slug)


def agent_context(agent_name: str, slug: str, repair_of: str = "") -> list[str]:
    project = PROJECTS / slug
    bits = [
        f"Project slug: {slug}",
        f"Project directory: projects/{slug}",
        f"Repository root: {ROOT}",
        f"You are the `{agent_name}` agent. Follow the agent file and the skill "
        f"above exactly, and write only the files they tell you to write.",
        "Write scope enforced by this runner: "
        + ", ".join(f"projects/{slug}/{p}" for p in AGENT_WRITE_SCOPES.get(agent_name, [])),
        "You may not edit pipeline/, .claude/ or learning/, you may not run any "
        "gate command, and you may not hand-edit skeleton/. A person decides at "
        "the gates; the orchestrator runs the checkers.",
        "When you are finished, reply with a short summary: what you wrote, and "
        "anything a human needs to know at the next gate. Do not ask questions - "
        "there is nobody to answer mid-run.",
    ]

    def add(rel: str, limit: int = 12_000, title: str = "") -> None:
        path = project / rel if not rel.startswith("/") else Path(rel)
        if path.exists() and path.is_file():
            bits.append(f"--- {title or rel} ---\n" + core.safe_text(path, limit))

    lessons = ROOT / "learning" / "lessons.md"
    if lessons.exists():
        bits.append("--- learning/lessons.md (every agent reads this) ---\n"
                    + core.safe_text(lessons, 20_000))
    add(".pipeline/CONTRACT.md", 16_000, "spec.json contract")
    if agent_name == "idea-generator":
        add("stack.json", 4_000)
        existing = sorted(p.name for p in PROJECTS.iterdir() if p.is_dir())
        bits.append("Projects that already exist (do not repeat them): "
                    + ", ".join(existing))
    if agent_name in {"spec-writer", "spec-breaker", "test-writer", "builder",
                      "verifier", "pack-writer"}:
        add("idea.md", 12_000)
        add("stack.json", 4_000)
    if agent_name in {"spec-breaker", "test-writer", "builder", "verifier", "pack-writer"}:
        add("spec.md", 40_000)
        add("spec.json", 40_000)
    if agent_name in {"test-writer", "verifier"}:
        bits.append(
            "The test runner builds one venv per project and installs exactly "
            + ", ".join(PYTEST_DEPS) + " into it. Import nothing else from the "
            "standard library's outside: a suite that imports a module the venv "
            "does not have fails collection, which means nothing ran and no "
            "conclusion about the code is possible. Use httpx for HTTP, not "
            "requests.")
    if agent_name in {"builder", "verifier", "pack-writer"}:
        if repair_of != "results.json":            # the repair block adds it in full
            add("results.json", 12_000)
        # what already exists, so a repair run extends the tree instead of
        # rebuilding it and a first run knows what the test suite expects
        for tree in ("app", "verify"):
            listing = tree_listing(project / tree)
            if listing:
                bits.append(f"--- files already in {tree}/ ---\n" + listing)
    if agent_name == "pack-writer":
        add("skeleton-check.json", 8_000)
    # results.json says a criterion is missing; WHY is in the boot/build log the
    # runner writes next to it, and nothing else surfaces that to the agent.
    for name in (".pipeline/server-app.log", ".pipeline/server-skeleton.log"):
        log = project / name
        if log.exists() and agent_name in {"builder", "verifier"}:
            bits.append(f"--- {name} (the app's own build and boot output) ---"
                        + chr(10) + core.safe_text(log, 8_000)[-8_000:])
    if repair_of:
        bits.append(
            f"THIS IS A REPAIR RUN. The checker report `{repair_of}` came back "
            f"red and this step is being re-run because of it. Read it, fix the "
            f"cause, and change nothing else.")
        add(repair_of, 24_000)
        if repair_of == "gate1.json":
            add("ambiguity.md", 24_000)
        if repair_of == "leak-scan.json":
            bits.append("Rule 4: fix the cut markers in app/, never skeleton/ - "
                        "the skeleton is regenerated from them.")
    state_path = project / ".pipeline" / "state.json"
    if state_path.exists():
        bits.append("--- .pipeline/state.json ---\n" + core.safe_text(state_path, 8_000))
    return bits


def tree_listing(root: Path, limit: int = 300) -> str:
    if not root.is_dir():
        return ""
    skip = {"node_modules", ".next", "__pycache__", ".venv", "venv", "dist", "build"}
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in skip for part in path.parts):
            continue
        out.append(f"{root.name}/{path.relative_to(root).as_posix()}  "
                   f"({path.stat().st_size} bytes)")
        if len(out) >= limit:
            out.append("...")
            break
    return "\n".join(out)


def drive_agent(agent_name: str, slug: str, run_id: str, repair_of: str = "") -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Put it in .env next to this repo, or "
            "run this step from Claude Code with the matching /workflow command.")
    agent_path = ROOT / ".claude" / "agents" / f"{agent_name}.md"
    skill_path = ROOT / ".claude" / "skills" / agent_name / "SKILL.md"
    if not agent_path.exists() or not skill_path.exists():
        raise RuntimeError(f"agent prompt or skill missing for {agent_name}")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

    messages = [
        {"role": "system", "content":
            "You are one agent of a guided-project production pipeline, running "
            "inside a local repository. Use the tools to read and write files. "
            "The orchestrator runs every checker; you never run a gate. Work "
            "until the files you own are complete, then stop and summarise."},
        {"role": "user", "content":
            "--- .claude/agents/%s.md ---\n%s\n\n--- .claude/skills/%s/SKILL.md ---\n%s\n\n%s"
            % (agent_name, agent_path.read_text(encoding="utf-8", errors="replace"),
               agent_name, skill_path.read_text(encoding="utf-8", errors="replace"),
               "\n\n".join(agent_context(agent_name, slug, repair_of)))},
    ]
    final = ""
    for round_no in range(MAX_TOOL_ROUNDS):
        response = openrouter_chat(model, key, messages)
        choice = response["choices"][0]["message"]
        messages.append(choice)
        content = choice.get("content") or ""
        if content:
            core.append_run_output(run_id, content + "\n")
            final = content
        tool_calls = choice.get("tool_calls") or []
        if not tool_calls:
            return final or "(the agent returned no text)"
        for call in tool_calls:
            name = (call.get("function") or {}).get("name", "")
            raw = (call.get("function") or {}).get("arguments", "{}")
            core.append_run_output(run_id, f"\n$ {name} {raw[:400]}\n")
            result = execute_agent_tool(name, raw, agent_name, slug)
            messages.append({"role": "tool", "tool_call_id": call.get("id"),
                             "content": result[-20_000:]})
            core.append_run_output(run_id, result[-3000:] + "\n")
        # keep the transcript from growing without bound on long builder runs.
        # Cut only at a safe boundary: a `tool` message whose assistant
        # `tool_calls` has been dropped is a protocol error, not a shorter prompt.
        if len(messages) > 120:
            messages = messages[:2] + messages[_trim_from(messages, 80):]
    raise RuntimeError(f"the agent used all {MAX_TOOL_ROUNDS} tool rounds without finishing")


def _trim_from(messages: list[dict], keep: int) -> int:
    """First index at or after len-keep that can legally start a transcript tail."""
    start = max(2, len(messages) - keep)
    for i in range(start, len(messages)):
        role = messages[i].get("role")
        if role == "user":
            return i
        if role == "assistant" and not (messages[i].get("tool_calls") or []):
            return i
    return len(messages) - 1


def openrouter_chat(model: str, key: str, messages: list[dict]) -> dict:
    payload = {"model": model, "messages": messages, "tools": agent_tools(),
               "tool_choice": "auto", "max_tokens": MAX_OUTPUT_TOKENS}
    req = request.Request(
        OPENROUTER_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"authorization": f"Bearer {key}",
                 "content-type": "application/json",
                 "http-referer": "http://localhost",
                 "x-title": "Guided Project Pipeline UI"},
        method="POST")
    # Only the transport is retried, and only where the request cannot have been
    # served: a URLError never reached OpenRouter, and a 429 is OpenRouter saying
    # "not now". An HTTP 5xx is left alone deliberately - the server may have
    # done the work and billed for it, and a silent second call would pay twice.
    body = None
    for attempt in range(NETWORK_RETRIES + 1):
        try:
            with request.urlopen(req, timeout=AGENT_TIMEOUT) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1500]
            if exc.code == 429 and attempt < NETWORK_RETRIES:
                time.sleep(NETWORK_BACKOFF * (2 ** attempt))
                continue
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            if attempt < NETWORK_RETRIES:
                time.sleep(NETWORK_BACKOFF * (2 ** attempt))
                continue
            raise RuntimeError(
                f"OpenRouter request failed after {NETWORK_RETRIES + 1} attempts "
                f"over {int(NETWORK_BACKOFF * (2 ** NETWORK_RETRIES))}s: {exc}. "
                f"The request never reached OpenRouter, so this says nothing "
                f"about the step - check the network and run it again.") from exc
    if body.get("error"):
        raise RuntimeError(f"OpenRouter error: {json.dumps(body['error'])[:1000]}")
    if not body.get("choices"):
        raise RuntimeError(f"OpenRouter returned no choices: {json.dumps(body)[:1000]}")
    # A turn that stops on `length` is cut mid-sentence - and mid tool call, whose
    # arguments then parse as nothing. Fail loudly here; a silent truncation would
    # read downstream as "the agent chose to do nothing".
    if body["choices"][0].get("finish_reason") == "length":
        raise RuntimeError(
            f"OpenRouter stopped the reply at the {MAX_OUTPUT_TOKENS}-token output "
            f"cap, so it is truncated. Raise UI_AGENT_MAX_OUTPUT_TOKENS and run the "
            f"step again.")
    return body


def agent_tools() -> list[dict]:
    def fn(name, description, properties, required):
        return {"type": "function", "function": {
            "name": name, "description": description,
            "parameters": {"type": "object", "properties": properties,
                           "required": required}}}
    return [
        fn("read_file", "Read a text file from the repository.",
           {"path": {"type": "string"}}, ["path"]),
        fn("write_file", "Write a text file inside this agent's write scope.",
           {"path": {"type": "string"}, "content": {"type": "string"}},
           ["path", "content"]),
        fn("list_files", "List repository files matching a glob pattern.",
           {"pattern": {"type": "string"}}, []),
        fn("grep", "Search the repository for a regular expression.",
           {"pattern": {"type": "string"}, "glob": {"type": "string"}}, ["pattern"]),
        fn("run_command",
           "Run a shell command from the repository root. Gate and human-record "
           "pipeline commands are refused.",
           {"command": {"type": "string"}, "timeout": {"type": "integer"}}, ["command"]),
    ]


def repo_path(rel: str) -> Path:
    path = (ROOT / str(rel).replace("\\", "/").lstrip("/")).resolve()
    if not core.is_inside(path, ROOT):
        raise ValueError("path escapes the repository root")
    return path


def write_allowed(path: Path, agent_name: str, slug: str) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if any(rel.startswith(p + "/") or rel == p for p in ("pipeline", ".claude", "learning")):
        return "rule 5: no agent edits pipeline/, .claude/ or learning/"
    if not rel.startswith(f"projects/{slug}/"):
        return f"outside this project - {agent_name} may only write under projects/{slug}/"
    inner = rel[len(f"projects/{slug}/"):]
    if inner.startswith("skeleton/"):
        return "rule 4: skeleton/ is generated by the cutter and never hand-edited"
    if inner.startswith(".pipeline/"):
        return "the orchestrator owns .pipeline/ - it is not an agent's to write"
    scopes = AGENT_WRITE_SCOPES.get(agent_name, [])
    for scope in scopes:
        if scope.endswith("/") and inner.startswith(scope):
            return ""
        if inner == scope:
            return ""
    if agent_name == "builder" and inner.startswith("verify/"):
        return ("rule 3: the builder cannot edit the tests. Fix app/ instead, and "
                "say so in your summary if a test looks wrong.")
    return (f"{agent_name} may only write {', '.join(scopes) or 'nothing'} in this "
            f"project; {inner} is outside that scope")


def execute_agent_tool(name: str, raw_args: str, agent_name: str, slug: str) -> str:
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError as exc:
        return f"invalid tool arguments: {exc}"
    try:
        if name == "read_file":
            path = repo_path(args.get("path", ""))
            if not path.is_file():
                return f"not found: {args.get('path')}"
            return path.read_text(encoding="utf-8", errors="replace")[:200_000]
        if name == "write_file":
            path = repo_path(args.get("path", ""))
            refusal = write_allowed(path, agent_name, slug)
            if refusal:
                return f"blocked: {refusal}"
            path.parent.mkdir(parents=True, exist_ok=True)
            content = str(args.get("content", ""))
            path.write_text(content, encoding="utf-8")
            core.log_event(slug, f"{agent_name} wrote {path.relative_to(ROOT).as_posix()}",
                           level="info", kind="artifact", component=agent_name,
                           detail=f"{len(content)} characters")
            return f"wrote {path.relative_to(ROOT).as_posix()} ({len(content)} chars)"
        if name == "list_files":
            pattern = args.get("pattern") or f"projects/{slug}/**/*"
            files = []
            for p in ROOT.glob(pattern):
                if not p.is_file():
                    continue
                parts = p.relative_to(ROOT).parts
                if any(part in {"node_modules", ".next", "__pycache__", ".git"}
                       for part in parts):
                    continue
                files.append(p.relative_to(ROOT).as_posix())
                if len(files) >= 600:
                    break
            return "\n".join(files) or "(no matches)"
        if name == "grep":
            cmd = ["rg", "--hidden", "--line-number", "--max-count", "40",
                   str(args.get("pattern", ""))]
            if args.get("glob"):
                cmd += ["-g", str(args["glob"])]
            try:
                proc = subprocess.run(cmd, cwd=str(ROOT), text=True,
                                      capture_output=True, timeout=120,
                                      encoding="utf-8", errors="replace")
            except FileNotFoundError:
                return "ripgrep is not installed on this machine"
            return ((proc.stdout or "") + (proc.stderr or ""))[:60_000] or "(no matches)"
        if name == "run_command":
            command = str(args.get("command", ""))
            refusal = command_refusal(command)
            if refusal:
                return f"blocked: {refusal}"
            proc = subprocess.run(
                command, cwd=str(ROOT), env=pipeline_env(), text=True,
                encoding="utf-8", errors="replace", capture_output=True,
                shell=True, timeout=int(args.get("timeout") or 900))
            return (f"returncode={proc.returncode}\n--- stdout ---\n"
                    f"{(proc.stdout or '')[-30_000:]}\n--- stderr ---\n"
                    f"{(proc.stderr or '')[-15_000:]}")
    except subprocess.TimeoutExpired:
        return "the command timed out"
    except Exception as exc:
        return f"tool error: {type(exc).__name__}: {exc}"
    return f"unknown tool: {name}"


def command_refusal(command: str) -> str:
    lowered = command.lower()
    for fragment in BANNED_COMMAND_FRAGMENTS:
        if fragment in lowered:
            return f"destructive command ({fragment.strip()})"
    if "pipeline" in lowered:
        for word in HUMAN_ONLY_COMMANDS:
            if f" {word} " in f" {lowered} " or lowered.rstrip().endswith(f" {word}"):
                return (f"`pipeline {word}` is a human decision or an orchestrator "
                        f"step, not an agent's")
    return ""


# --------------------------------------------------------------------------
# preview - serve a built project so a person can look at it
# --------------------------------------------------------------------------
# deploy_check already builds and serves, but it tears the server down the
# moment the check passes: deploy.json records the URL it used, which then
# answers nothing. `--hold` keeps it up but blocks the call for its whole
# duration and writes the report only afterwards, so the UI could not show a
# link while it mattered. This owns the server instead - start it, keep the
# handle, hand back the URL, stop it on request or at shutdown.
PREVIEWS: dict[str, dict] = {}
PREVIEW_LOCK = threading.Lock()
PREVIEW_TARGETS = ("app", "skeleton")


def preview_state(slug: str) -> dict:
    """What the UI shows: never the Popen handle, and never a dead server."""
    with PREVIEW_LOCK:
        entry = PREVIEWS.get(slug)
        if not entry:
            return {"running": False}
        server = entry.get("server")
        if server is not None and server.poll() is not None:
            PREVIEWS.pop(slug, None)
            return {"running": False,
                    "error": f"the {entry['target']} preview exited on its own "
                             f"(code {server.returncode}) - see its log"}
        return {k: v for k, v in entry.items() if k != "server"}


def start_preview(slug: str, target: str = "app") -> dict:
    slug = core.slugify(slug)
    if target not in PREVIEW_TARGETS:
        raise ValueError(f"preview target is one of {', '.join(PREVIEW_TARGETS)}")
    live = preview_state(slug)
    if live.get("running"):
        if live.get("target") == target:
            return live
        stop_preview(slug)
    root = core.project_path(slug) / target
    if not root.exists():
        raise ValueError(f"{slug} has no {target}/ to preview yet")

    port = test_runner.free_port()
    url = f"http://127.0.0.1:{port}"
    log = core.pipeline_dir(slug) / f"preview-{target}.log"
    with PREVIEW_LOCK:
        PREVIEWS[slug] = {"running": True, "status": "starting", "target": target,
                          "url": "", "port": port, "started": time.time(),
                          "log": str(log), "server": None}

    def work() -> None:
        try:
            # boot() installs if needed, builds, then serves - the same path the
            # test runner uses, so a preview cannot pass where a test could not.
            server = test_runner.boot(root, port, log)
            up = test_runner.wait_for(url, 120)
            with PREVIEW_LOCK:
                entry = PREVIEWS.get(slug)
                if entry is None:                 # stopped while it was building
                    test_runner.stop_server(server)
                    return
                entry["server"] = server
                entry["status"] = "live" if up else "failed"
                entry["url"] = url if up else ""
                if not up:
                    entry["running"] = False
                    entry["error"] = f"built, but nothing answered on {url}"
            core.log_event(slug, f"{target} preview {'live at ' + url if up else 'failed to answer'}",
                           level="ok" if up else "warn", kind="preview", component="preview")
        except Exception as exc:
            with PREVIEW_LOCK:
                PREVIEWS[slug] = {"running": False, "status": "failed",
                                  "target": target, "url": "", "log": str(log),
                                  "error": f"{type(exc).__name__}: {exc}"}
            core.log_event(slug, f"{target} preview failed: {type(exc).__name__}: {exc}",
                           level="error", kind="preview", component="preview")

    threading.Thread(target=work, daemon=True).start()
    return preview_state(slug)


def stop_preview(slug: str) -> dict:
    slug = core.slugify(slug)
    with PREVIEW_LOCK:
        entry = PREVIEWS.pop(slug, None)
    if entry and entry.get("server") is not None:
        test_runner.stop_server(entry["server"])
        core.log_event(slug, f"{entry.get('target', 'app')} preview stopped",
                       level="info", kind="preview", component="preview")
    return {"running": False}


def stop_all_previews() -> None:
    """Nothing may outlive the server that started it."""
    for slug in list(PREVIEWS):
        try:
            stop_preview(slug)
        except Exception:
            pass


# --------------------------------------------------------------------------
# human actions - the gates and the records only a person may write
# --------------------------------------------------------------------------
def human_command(payload: dict) -> tuple[list[str], str | None, str, str]:
    """(args, slug, component, label) for every non-agent, non-script action."""
    action = payload.get("action")
    slug = core.slugify(payload["slug"]) if payload.get("slug") else None
    if action == "stack":
        require(slug, "slug")
        require(payload.get("stack"), "stack")
        return ([
            "stack", slug, "--stack", payload["stack"],
            "--sessions", str(int(payload.get("sessions") or 1)),
            "--minutes", str(int(payload.get("minutes") or 40)),
            "--track", payload.get("track") or "fullstack",
            "--limits", payload.get("limits") or "",
            "--by", payload.get("by") or "",
        ], slug, "stack input", "Stack input (step 0)")
    if action == "pick":
        require(slug, "slug")
        args = ["pick", slug, str(int(payload.get("n") or 1))]
        if payload.get("note"):
            args += ["-m", payload["note"]]
        return args, slug, "gate0", f"Gate 0 - picked idea {int(payload.get('n') or 1)}"
    if action == "gate":
        require(slug, "slug")
        number = int(payload.get("gate", 1))
        decision = payload.get("decision") or "approve"
        if decision not in {"approve", "reject"}:
            raise ValueError("a gate decision is approve or reject")
        args = ["gate", slug, str(number), decision]
        if payload.get("note"):
            args += ["-m", payload["note"]]
        if payload.get("override"):
            args.append("--override")
        return args, slug, f"gate{number}", f"Gate {number} {decision}"
    if action == "dryrun":
        require(slug, "slug")
        require(payload.get("by"), "who taught it")
        args = ["dryrun", slug, "--session", str(int(payload.get("session") or 1)),
                "--minutes", str(int(payload.get("minutes") or 40)),
                "--by", payload["by"]]
        if payload.get("could_not_teach"):
            args.append("--could-not-teach")
        if payload.get("note"):
            args += ["-m", payload["note"]]
        return args, slug, "dry run", "Dry run (step 13)"
    if action == "feedback":
        require(slug, "slug")
        require(payload.get("note"), "note")
        args = ["feedback", slug, "-m", payload["note"]]
        if payload.get("session"):
            args += ["--session", str(int(payload["session"]))]
        if payload.get("by"):
            args += ["--by", payload["by"]]
        return args, slug, "feedback", "Instructor feedback (step 15)"
    if action == "revise":
        require(slug, "slug")
        return ["revise", slug], slug, "revise", "Revise - archive the round, reset Gate 1"
    if action == "lock":
        require(slug, "slug")
        return ["lock", slug, payload.get("tree", "app")], slug, "lock", "Lock"
    if action == "unlock":
        require(slug, "slug")
        return ["unlock", slug], slug, "unlock", "Unlock"
    raise ValueError(f"unsupported action: {action}")


def run_human(payload: dict, *, wait: bool = False) -> dict:
    args, slug, component, label = human_command(payload)
    return run_command(args, slug, component, label, kind="human", wait=wait)


def create_project(payload: dict) -> dict:
    slug = core.slugify(payload.get("slug") or payload.get("name") or "")
    flow = int(payload.get("flow") or 2)
    if flow not in {1, 2}:
        raise ValueError("flow must be 1 or 2")
    if (PROJECTS / slug).exists():
        raise ValueError(f"projects/{slug} already exists - pick another slug")
    proc = subprocess.run([*pipeline_python_args(), "new", slug, "--flow", str(flow)],
                          cwd=str(ROOT), env=pipeline_env(), text=True,
                          encoding="utf-8", errors="replace", capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "project creation failed").strip())
    core.sync_state_events(slug)      # records "Project created" from state.json
    uploads = payload.get("uploads") or []
    if uploads:
        import base64
        upload_dir = PROJECTS / slug / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        for item in uploads:
            name = core.slugify(Path(item.get("name", "upload.bin")).stem) + \
                Path(item.get("name", "upload.bin")).suffix
            data = item.get("data", "")
            if "," in data:
                data = data.split(",", 1)[1]
            (upload_dir / name).write_bytes(base64.b64decode(data))
        core.log_event(slug, f"{len(uploads)} reference file(s) uploaded",
                       level="info", kind="artifact",
                       detail=", ".join(u.get("name", "") for u in uploads))
    result = {"slug": slug, "flow": flow, "stdout": proc.stdout}
    stack = (payload.get("stack") or "").strip()
    if flow == 2 and stack:
        run = run_human({"action": "stack", "slug": slug, "stack": stack,
                         "sessions": payload.get("sessions"),
                         "minutes": payload.get("minutes"),
                         "track": payload.get("track"),
                         "limits": payload.get("limits"),
                         "by": payload.get("by")}, wait=True)
        result["stack_run"] = run.get("id")
        if run.get("status") != "succeeded":
            result["stack_error"] = (run.get("stderr") or run.get("stdout") or "")[-1500:]
    if flow == 1:
        idea = (payload.get("idea") or "").strip()
        if idea:
            (PROJECTS / slug / "idea.md").write_text(idea, encoding="utf-8")
            core.log_event(slug, "idea.md written", level="ok", kind="artifact",
                           detail=f"{len(idea)} characters")
    return result
