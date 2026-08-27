"""Deploy check - SCRIPT, step 10.

Fresh copy, install, build, temporary preview link. Mechanical, so no agent.

  python -m pipeline.deploy_check <project-dir> [--target app|skeleton] [--hold 300]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .test_runner import BOOT_TIMEOUT, free_port, run, wait_for

EXCLUDE = {"node_modules", ".next", ".git", "dist", "build", ".turbo",
           "coverage", "__pycache__", ".venv", ".pipeline"}


def fresh_copy(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--target", default="app", choices=["app", "skeleton"])
    ap.add_argument("--hold", type=int, default=0,
                    help="seconds to keep the preview link alive before tearing down")
    a = ap.parse_args(argv)

    project = Path(a.project).resolve()
    steps: list[dict] = []
    started = time.time()
    tmp = Path(tempfile.mkdtemp(prefix=f"gp-deploy-{project.name}-"))
    work = tmp / a.target
    preview = None
    server = None

    def step(name: str, ok: bool, detail: str = "") -> bool:
        steps.append({"step": name, "ok": ok, "detail": detail[-2000:]})
        return ok

    try:
        fresh_copy(project / a.target, work)
        step("fresh copy", True, str(work))

        lock = work / "package-lock.json"
        r = run(["npm", "ci" if lock.exists() else "install", "--no-audit", "--no-fund"],
                work, timeout=1200)
        if not step("install", r.returncode == 0, r.stderr or r.stdout):
            raise RuntimeError("install failed")

        r = run(["npm", "run", "build"], work, timeout=1200)
        if not step("build", r.returncode == 0, r.stderr or r.stdout):
            raise RuntimeError("build failed")

        port = free_port()
        preview = f"http://127.0.0.1:{port}"
        log = (project / ".pipeline")
        log.mkdir(parents=True, exist_ok=True)
        handle = (log / "deploy-server.log").open("w")
        server = subprocess.Popen(
            ["npm", "run", "start", "--", "--port", str(port)], cwd=work,
            env={**os.environ, "PORT": str(port), "NODE_ENV": "production"},
            stdout=handle, stderr=subprocess.STDOUT)
        up = wait_for(preview, BOOT_TIMEOUT)
        step("preview", up, preview if up else f"no answer on {preview}")
        if up and a.hold:
            print(f"preview live at {preview} for {a.hold}s")
            time.sleep(a.hold)
    except Exception as e:
        steps.append({"step": "aborted", "ok": False, "detail": str(e)})
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                server.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    report = {
        "ok": all(s["ok"] for s in steps) and len(steps) >= 4,
        "target": a.target,
        "preview": preview,
        "seconds": round(time.time() - started, 1),
        "steps": steps,
    }
    (project / "deploy.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("ok", "target", "preview", "seconds")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
