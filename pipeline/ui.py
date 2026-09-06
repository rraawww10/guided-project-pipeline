"""Local control and monitoring UI for the guided project pipeline.

    python -m pipeline.ui            # then open http://127.0.0.1:8765

This is a window onto the pipeline, not a second copy of it. Every number it
shows is read from `projects/<slug>/`; every action it offers runs the real
thing - `python -m pipeline ...` for a script or a gate, the agent's own prompt
and skill against OpenRouter for an agent step. There is no simulated progress
anywhere in this server or its page.

    ui_core.py       what the pipeline's files mean
    ui_runner.py     running a script or an agent, and recording it
    orchestrator.py  which of those runs next, and where it must stop
    ui.py            this file - HTTP and the page shell
"""
from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from . import orchestrator
from . import ui_core as core
from . import ui_runner as runner
from .ui_core import PROJECTS, ROOT, STATIC


def dispatch_get(path: str, query: dict):
    parts = [p for p in path.split("/") if p]
    if path == "/api/overview":
        return core.overview()
    if path == "/api/agents":
        return core.agents_view(core.all_projects())
    if path == "/api/scripts":
        return core.scripts_view()
    if path == "/api/runs":
        return core.all_runs()
    if len(parts) == 3 and parts[:2] == ["api", "runs"]:
        run = core.get_run(parts[2])
        if not run:
            raise FileNotFoundError(parts[2])
        return run
    if len(parts) >= 3 and parts[:2] == ["api", "projects"]:
        slug = unquote(parts[2])
        tail = parts[3] if len(parts) > 3 else ""
        after = int((query.get("after") or ["0"])[0] or 0)
        if tail == "status":
            return core.project_status_payload(slug, after=after)
        if tail == "events":
            events = core.read_events(slug, after=after)
            return {"slug": slug, "events": events,
                    "event_seq": max([int(e.get("seq") or 0) for e in events] or [after])}
        if tail == "artifact":
            return core.read_artifact(slug, unquote((query.get("path") or [""])[0]))
        if tail == "plan":
            project = core.project_path(slug)
            return core.plan_entries(project, core.read_state(slug))
        if not tail:
            detail = core.project_detail(slug)
            detail["preview"] = runner.preview_state(slug)
            return detail
    raise FileNotFoundError(path)


def dispatch_post(path: str, payload: dict):
    parts = [p for p in path.split("/") if p]
    if path == "/api/projects":
        return 201, runner.create_project(payload)
    if len(parts) == 4 and parts[:2] == ["api", "projects"]:
        slug = unquote(parts[2])
        verb = parts[3]
        if verb == "start":
            return 202, orchestrator.start(slug)
        if verb == "pause":
            return 200, orchestrator.stop(slug)
        if verb == "step":
            return 202, orchestrator.start(slug, single=True)
        if verb == "preview":
            if (payload.get("action") or "start") == "stop":
                return 200, runner.stop_preview(slug)
            return 202, runner.start_preview(slug, payload.get("target") or "app")
    if path == "/api/run":
        action = payload.get("action")
        if action == "agent":
            return 202, runner.run_agent(payload.get("agent", ""),
                                         payload.get("slug", ""),
                                         step=payload.get("step"),
                                         repair_of=payload.get("repair_of", ""))
        if action == "script":
            return 202, runner.run_script(payload.get("script", ""),
                                          payload.get("slug") or None,
                                          step=payload.get("step"))
        return 202, runner.run_human(payload)
    raise FileNotFoundError(path)


class Handler(BaseHTTPRequestHandler):
    server_version = "GuidedPipelineUI/1.0"
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:                                    # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path in {"/", "/index.html"}:
                self.send_bytes(index_html().encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path.startswith("/static/"):
                self.serve_static(parsed.path.removeprefix("/static/"))
                return
            query = parse_qs(parsed.query)
            if parsed.path.endswith("/download"):
                slug = unquote([p for p in parsed.path.split("/") if p][2])
                self.send_download(slug, unquote((query.get("path") or [""])[0]))
                return
            self.send_json(dispatch_get(parsed.path, query))
        except FileNotFoundError as exc:
            self.send_json({"error": f"not found: {exc}"}, status=404)
        except Exception as exc:
            self.send_json({"error": f"{type(exc).__name__}: {exc}"}, status=500)

    def do_POST(self) -> None:                                   # noqa: N802
        parsed = urlparse(self.path)
        try:
            status, body = dispatch_post(parsed.path, self.read_json())
            self.send_json(body, status=status)
        except FileNotFoundError as exc:
            self.send_json({"error": f"not found: {exc}"}, status=404)
        except (ValueError, RuntimeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
        except Exception as exc:
            self.send_json({"error": f"{type(exc).__name__}: {exc}"}, status=500)

    def serve_static(self, name: str) -> None:
        path = (STATIC / name).resolve()
        if not core.is_inside(path, STATIC.resolve()) or not path.is_file():
            self.send_json({"error": "not found"}, status=404)
            return
        ctype = {".css": "text/css; charset=utf-8",
                 ".js": "application/javascript; charset=utf-8"}.get(
                     path.suffix, mimetypes.guess_type(path.name)[0] or "text/plain")
        self.send_bytes(path.read_bytes(), ctype)

    def send_download(self, slug: str, rel_path: str) -> None:
        project = core.project_path(slug).resolve()
        path = (project / rel_path).resolve()
        if not core.is_inside(path, project) or not path.is_file():
            raise FileNotFoundError(rel_path)
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "application/octet-stream")
        self.send_header("content-disposition", f'attachment; filename="{path.name}"')
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b""
        return json.loads(raw.decode("utf-8")) if raw else {}

    def send_json(self, payload, status: int = 200) -> None:
        data = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_bytes(self, data: bytes, ctype: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", ctype)
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:
        message = fmt % args
        if "/api/projects/" in message and "/status" in message:
            return                              # the poll would drown everything else
        print(f"ui: {message}")


def index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Guided Project Pipeline</title>
  <link rel="stylesheet" href="/static/app.css">
</head>
<body>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">GP</div>
      <div>
        <strong>Pipeline</strong>
        <span>Guided projects</span>
      </div>
    </div>
    <nav>
      <button data-view="dashboard" class="active">Dashboard</button>
      <button data-view="create">Create Project</button>
      <button data-view="projects">Projects</button>
      <button data-view="queue">Queue</button>
      <button data-view="running">Running Workflows</button>
      <button data-view="reviews">Human Gates</button>
      <button data-view="agents">Agents</button>
      <button data-view="scripts">Scripts</button>
      <button data-view="artifacts">Artifacts</button>
    </nav>
    <div class="sidebar-foot">
      <div id="provider-line" class="muted"></div>
      <div id="root-line" class="muted"></div>
    </div>
  </aside>
  <main>
    <header class="topbar">
      <div>
        <h1 id="view-title">Dashboard</h1>
        <p id="view-sub" class="muted"></p>
      </div>
      <div class="topbar-actions">
        <span id="live-dot" class="live-dot" title="polling"></span>
        <button id="refresh" class="ghost">Refresh Status</button>
      </div>
    </header>
    <div id="banner"></div>
    <section id="app" class="content"></section>
  </main>
  <div id="drawer" class="drawer" hidden></div>
  <script src="/static/app.js"></script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guided project pipeline UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    PROJECTS.mkdir(parents=True, exist_ok=True)
    core.load_persisted_runs()
    for state_path in core.project_state_paths():
        slug = state_path.parents[1].name
        core.sync_state_events(slug)
        workflow = core.safe_json(state_path.parents[1] / ".pipeline" / "ui-workflow.json", {})
        if isinstance(workflow, dict) and workflow.get("state") == "running":
            core.write_workflow(slug, state="interrupted",
                                reason="the UI server restarted while this run was in flight")

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.daemon_threads = True
    print(f"Guided Project Pipeline UI  http://{args.host}:{args.port}")
    print(f"project root: {ROOT}")
    info = core.openrouter_info()
    print("agent runner: OpenRouter " + (f"({info['model']})" if info["available"]
                                         else "- OPENROUTER_API_KEY not set, "
                                              "agent steps will not start"))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        # A preview is a node server this process started.
        # stop_server kills the whole tree, and nothing may
        # outlive the UI that launched it - an orphan holds
        # its port and, on Windows, the directory it served.
        runner.stop_all_previews()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
