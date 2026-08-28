"""Deploy check - SCRIPT, step 10.

Fresh copy, install, build, temporary preview link. Mechanical, so no agent.

  python -m pipeline.deploy_check <project-dir> [--target app|skeleton] [--hold 300]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from fnmatch import fnmatch
from pathlib import Path

from .cutter import gitignore_matcher
from .test_runner import BOOT_TIMEOUT, free_port, run, wait_for

EXCLUDE = {"node_modules", ".next", ".git", "dist", "build", ".turbo",
           "coverage", "__pycache__", ".venv", ".pipeline",
           # generated build artifacts - both shipped skeletons carry a stale
           # tsconfig.tsbuildinfo, which is junk in a student's copy and was
           # only ever excluded because a project happened to gitignore it
           "*.tsbuildinfo", ".DS_Store"}

# tip-split shipped with this in its install output and step 10 recorded ok:true:
#   next@15.1.6: This version has a security vulnerability ... CVE-2025-66478
# Gate 3 trusts a green deploy check, so an advisory npm already printed has to
# fail the step rather than sit in a detail string nobody reads. recipe-box drew
# a clean version of the same package - which way it went was luck.
ADVISORY = re.compile(
    r"security vulnerability"
    r"|\bCVE-\d{4}-\d{3,}\b"
    r"|\bGHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}\b"
    r"|\b\d+\s+(?:critical|high|moderate|low)\s+severity\s+vulnerabilit"
    r"|\bfound\s+\d+\s+vulnerabilit",
    re.IGNORECASE)


def npm() -> str:
    """The npm executable, resolved.

    On Windows npm is npm.CMD, and CreateProcess cannot launch a bare "npm" -
    it raises WinError 2. shutil.which honours PATHEXT and returns the full
    path, which does launch. Same class as the POSIX venv layout above: the
    pipeline ran only on Linux until it did not.
    """
    return shutil.which("npm") or "npm"


def find_advisories(text: str) -> list[str]:
    """The lines npm already printed that name a vulnerability."""
    return sorted({ln.strip()[:300] for ln in text.splitlines() if ADVISORY.search(ln)})


def fresh_copy(src: Path, dst: Path) -> None:
    """A fresh copy means fresh. Anything the project gitignores is runtime
    state, not source - a live file store left mutated by step 6's tests was
    being copied straight into the build the preview link serves."""
    ignored = gitignore_matcher(src)

    def skip(directory, names):
        here = Path(directory)
        # fnmatch, not equality: EXCLUDE is a pattern list, and the original
        # shutil.ignore_patterns() honoured globs. Rewriting this to take the
        # gitignore matcher quietly dropped that.
        out = {n for n in names if any(fnmatch(n, pat) for pat in EXCLUDE)}
        for n in names:
            rel = (here / n).relative_to(src)
            if ignored(rel):
                out.add(n)
        return out

    shutil.copytree(src, dst, ignore=skip)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--target", default="app", choices=["app", "skeleton"])
    ap.add_argument("--hold", type=int, default=0,
                    help="seconds to keep the preview link alive before tearing down")
    ap.add_argument("--allow-advisories", action="store_true",
                    help="record install security advisories without failing the step. "
                         "A deliberate decision to ship a known advisory - it is written "
                         "into deploy.json either way.")
    a = ap.parse_args(argv)

    project = Path(a.project).resolve()
    steps: list[dict] = []
    started = time.time()
    tmp = Path(tempfile.mkdtemp(prefix=f"gp-deploy-{project.name}-"))
    work = tmp / a.target
    preview = None
    server = None
    advisories: list[str] = []

    def step(name: str, ok: bool, detail: str = "") -> bool:
        steps.append({"step": name, "ok": ok, "detail": detail[-2000:]})
        return ok

    try:
        fresh_copy(project / a.target, work)
        step("fresh copy", True, str(work))

        lock = work / "package-lock.json"
        r = run([npm(), "ci" if lock.exists() else "install", "--no-audit", "--no-fund"],
                work, timeout=1200)
        install_out = (r.stdout or "") + "\n" + (r.stderr or "")
        advisories = find_advisories(install_out)
        if not step("install", r.returncode == 0, r.stderr or r.stdout):
            raise RuntimeError("install failed")
        if advisories:
            detail = ("npm reported a security advisory during install:\n  "
                      + "\n  ".join(advisories)
                      + ("\n(allowed by --allow-advisories)" if a.allow_advisories else
                         "\nUpgrade the dependency, or re-run with --allow-advisories to "
                         "ship it deliberately."))
            if not step("install advisories", bool(a.allow_advisories), detail):
                raise RuntimeError("install reported a security advisory")
        else:
            step("install advisories", True, "none")

        r = run([npm(), "run", "build"], work, timeout=1200)
        if not step("build", r.returncode == 0, r.stderr or r.stdout):
            raise RuntimeError("build failed")

        port = free_port()
        preview = f"http://127.0.0.1:{port}"
        log = (project / ".pipeline")
        log.mkdir(parents=True, exist_ok=True)
        handle = (log / "deploy-server.log").open("w")
        server = subprocess.Popen(
            [npm(), "run", "start", "--", "--port", str(port)], cwd=work,
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
        "ok": all(s["ok"] for s in steps) and len(steps) >= 5,
        "target": a.target,
        "preview": preview,
        "advisories": advisories,
        "advisories_allowed": bool(a.allow_advisories),
        "seconds": round(time.time() - started, 1),
        "steps": steps,
    }
    (project / "deploy.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("ok", "target", "preview", "seconds")}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
