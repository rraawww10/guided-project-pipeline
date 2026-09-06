"""Test runner - SCRIPT, step 6's checker and step 8's check.

Boots the app, runs the committed test script, reports pass or fail per
acceptance criterion. Pass or fail is not an opinion, so there is no agent here.

  python -m pipeline.test_runner <project-dir> [--target app|skeleton] [--out results.json]

The Verifier writes verify/. This runner never edits it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from . import code_check, stack_check

BOOT_TIMEOUT = 180        # seconds to wait for the dev server to answer
TEST_TIMEOUT = 900        # seconds for the whole pytest run
PYTEST_DEPS = ["pytest", "playwright", "httpx"]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run(cmd: list[str], cwd: Path, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


GET_PIP = "https://bootstrap.pypa.io/get-pip.py"


def _bootstrap_pip(py: Path) -> bool:
    """Some boxes ship python3 without ensurepip (Debian splits it into
    python3-venv). Fetch get-pip and run it inside the venv instead of failing."""
    import tempfile
    try:
        with urllib.request.urlopen(GET_PIP, timeout=120) as r:
            data = r.read()
    except Exception:
        return False
    tmp = tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False)
    try:
        tmp.write(data)
        tmp.close()
        return subprocess.run([str(py), tmp.name, "-q"],
                              capture_output=True, timeout=600).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        os.unlink(tmp.name)


def venv_bin(venv: Path, name: str) -> Path:
    """The path to an executable inside a venv, on this platform.

    Windows puts them in Scripts/ with an .exe suffix; POSIX puts them in bin/.
    Hardcoding the POSIX layout made `pipeline test` raise WinError 2 out of
    ensure_venv BEFORE it could log a step, so no retry was burned, no ticket
    was raised, and the phase-2 workflow looped on the Verifier for two hours
    with retries showing code=0/15.
    """
    if sys.platform == "win32":
        return venv / "Scripts" / (name + ".exe")
    return venv / "bin" / name


def _make_venv(venv: Path) -> Path:
    """uv if it is here, then the stdlib, then the stdlib without pip."""
    venv.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("uv"):
        r = subprocess.run(["uv", "venv", str(venv)], capture_output=True, text=True)
        if r.returncode == 0:
            return venv_bin(venv, "python")
    r = subprocess.run([sys.executable, "-m", "venv", str(venv)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.rmtree(venv, ignore_errors=True)
        r = subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(
                "could not create a virtualenv for the test runner.\n"
                f"{r.stderr.strip()}\n"
                "Fix it once with:  sudo apt install python3-venv")
    return venv_bin(venv, "python")


def ensure_venv(project: Path) -> Path:
    """One venv per project, reused. Keeps the nightly watchdog free of installs."""
    venv = project / ".pipeline" / "venv"
    py = venv_bin(venv, "python")
    stamp = venv / ".deps-ok"
    if stamp.exists() and py.exists():
        return py

    if not py.exists():
        py = _make_venv(venv)

    has_pip = subprocess.run([str(py), "-m", "pip", "--version"],
                             capture_output=True).returncode == 0
    if not has_pip and not _bootstrap_pip(py):
        raise RuntimeError(
            "the test runner venv has no pip and get-pip could not be fetched.\n"
            "Fix it once with:  sudo apt install python3-venv")

    r = subprocess.run([str(py), "-m", "pip", "install", "-q", *PYTEST_DEPS],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(f"could not install {PYTEST_DEPS}:\n{r.stderr[-1500:]}")

    # chromium is ~150MB and only needed once per machine
    subprocess.run([str(venv_bin(venv, "playwright")), "install", "chromium"],
                   capture_output=True, timeout=1800)
    stamp.write_text("ok\n", encoding="utf-8")
    return py


def wait_for(url: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status < 500:
                    return True
        except (urllib.error.HTTPError,) as e:
            if e.code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def target_slug(target: str) -> str:
    """A filename-safe name for a --target, which may be a PATH.

    The mutation check passes targets like ".pipeline/mutants/cut-game-status",
    and these names were interpolated straight into "server-{target}.log". The
    separator made a directory that does not exist, so every mutant run died in
    boot() with Errno 2, reported all criteria "missing", and mutation.py counts
    "missing" as red - so every task looked graded and the check passed
    vacuously. It reports on rule 3; a false green here is the worst kind.
    """
    return re.sub(r"[^A-Za-z0-9._-]+", "-", target).strip("-") or "target"


def npm() -> str:
    """The npm executable, resolved.

    On Windows npm is npm.CMD, and CreateProcess cannot launch a bare "npm" -
    it raises WinError 2. shutil.which honours PATHEXT and returns the full
    path, which does launch. Same class as the POSIX venv layout above: the
    pipeline ran only on Linux until it did not.
    """
    return shutil.which("npm") or "npm"


# Not one of pytest's exit codes. boot() raising means npm install or npm run
# build failed and the app never started, so the suite was never asked anything
# - a different outcome from pytest running and collecting nothing.
BOOT_FAILED_RC = 99


def boot(target: Path, port: int, log: Path) -> subprocess.Popen:
    env = {**os.environ, "PORT": str(port), "NODE_ENV": "production", "CI": "1"}
    # An EMPTY node_modules is not an installed one. demo-run-01 had the
    # directory - left behind by an `npm ci` that failed against a stub lockfile
    # - so the install was skipped, and `next build` then died with "'next' is
    # not recognized". Ask whether anything is in it, not whether it exists.
    mods = target / "node_modules"
    # Dotted entries do not count. A failed install still leaves `.bin` and
    # `.package-lock.json` behind, so "is there anything in it" was true for a
    # node_modules holding no packages at all.
    installed = mods.is_dir() and any(
        not child.name.startswith(".") for child in mods.iterdir())
    if not installed:
        lock = target / "package-lock.json"
        run([npm(), "ci" if lock.exists() else "install", "--no-audit", "--no-fund"],
            target, timeout=900)
    build = run([npm(), "run", "build"], target, timeout=900)
    log.write_text(f"$ npm run build\n{build.stdout}\n{build.stderr}\n", encoding="utf-8")
    if build.returncode != 0:
        raise RuntimeError(f"npm run build failed - see {log}")
    handle = log.open("a")
    # POSIX: give the server its own process group so stop_server can signal the
    # group. Windows has no process groups in that sense; taskkill /T walks the
    # parent-child tree instead, so nothing extra is needed at spawn time.
    extra = {} if os.name == "nt" else {"start_new_session": True}
    return subprocess.Popen([npm(), "run", "start", "--", "--port", str(port)],
                            cwd=target, env=env, stdout=handle,
                            stderr=subprocess.STDOUT, **extra)


def stop_server(server: subprocess.Popen | None) -> None:
    """Kill the server's whole process tree, not just the handle we hold.

    What Popen returns here is `npm run start`; npm spawns `next start` as a
    child. terminate() reached npm and left `next` running, so every mutation
    run leaked two processes per mutant. On Windows the orphan keeps a handle on
    the mutant directory and the NEXT run dies in mutate_one with

        PermissionError: [WinError 32] ... used by another process

    one whole run away from the cause, because mutation.py's rmtree passes
    ignore_errors=True and said nothing the first time. pipeline-test-03 found
    it with 12 orphans alive from a run that had already reported success.

    The leak itself is not Windows-specific - on POSIX an orphan holding an open
    file does not block unlink, so it shows up as drifting node processes and a
    port that is still bound rather than as a crash.
    """
    if server is None or server.poll() is not None:
        return
    if os.name == "nt":
        # /T takes the tree, /F forces it. Fall through to terminate() if
        # taskkill is unavailable, so this is never worse than it was.
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(server.pid)],
                           capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            server.terminate()
    else:
        try:
            os.killpg(os.getpgid(server.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            server.terminate()
    try:
        server.wait(timeout=20)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(os.getpgid(server.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        server.kill()


def parse_junit(xml_path: Path) -> dict[str, dict]:
    """node id -> {status, message}"""
    out: dict[str, dict] = {}
    if not xml_path.exists():
        return out
    root = ET.parse(xml_path).getroot()
    for case in root.iter("testcase"):
        cls, name = case.get("classname", ""), case.get("name", "")
        file_part = cls.replace(".", "/") + ".py" if cls else ""
        node = f"{file_part}::{name}"
        status, message = "pass", ""
        for tag, s in (("failure", "fail"), ("error", "fail"), ("skipped", "skip")):
            el = case.find(tag)
            if el is not None:
                status = s
                message = (el.get("message") or el.text or "").strip()[:800]
                break
        out[node] = {"status": status, "message": message}
        out[name] = {"status": status, "message": message}   # loose match fallback
    return out


def map_to_criteria(spec: dict, coverage: dict, by_node: dict) -> dict[str, dict]:
    criteria: dict[str, dict] = {}
    for s in spec.get("sessions", []):
        for c in s.get("criteria", []):
            cid = c["id"]
            entry = coverage.get(cid)
            if not entry:
                criteria[cid] = {"status": "missing", "check": c["check"],
                                 "session": s["n"], "test": None,
                                 "message": "no test in coverage.json for this criterion"}
                continue
            node = entry["test"]
            hit = by_node.get(node) or by_node.get(node.split("::")[-1])
            criteria[cid] = {
                "status": hit["status"] if hit else "missing",
                "check": c["check"], "session": s["n"], "test": node,
                "message": hit["message"] if hit else "test did not run",
            }
    return criteria


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    # app | skeleton | any path under the project (the mutation check points
    # this at .pipeline/mutants/<task-id>). Kept permissive rather than a
    # choices= list so a new target needs no change here.
    ap.add_argument("--target", default="app")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    # resolve first: several subprocesses run with cwd=project, and a relative
    # interpreter or test path would then resolve against the wrong directory
    project = Path(a.project).resolve()
    target = project / a.target
    default_out = {"app": "results.json", "skeleton": "skeleton-results.json"}.get(
        a.target, f"results-{Path(a.target).name}.json")
    out_path = project / (a.out or default_out)
    spec = json.loads((project / "spec.json").read_text(encoding="utf-8"))

    verify_dir = target / "verify" if (target / "verify").exists() else project / "verify"
    coverage_path = verify_dir / "coverage.json"
    if not coverage_path.exists():
        out_path.write_text(json.dumps(
            {"ok": False, "error": f"{coverage_path} is missing - the Verifier has not run"},
            indent=2) + "\n", encoding="utf-8")
        print(f"coverage.json missing at {coverage_path}", file=sys.stderr)
        return 1
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))

    py = ensure_venv(project)
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    logs = project / ".pipeline"
    logs.mkdir(parents=True, exist_ok=True)
    slug = target_slug(a.target)
    xml = logs / f"junit-{slug}.xml"
    # Delete last run's report before this one. If the build fails, pytest never
    # runs and never writes a new file - and parse_junit would then read the
    # PREVIOUS run's results as if they were this one's. demo-run-01 reported
    # "13 pass, 0 fail" for a run whose build died in 0.8s and whose suite was
    # never invoked. `ok` was still false because rc said so, but mutation.py
    # reads the counts, and a mutant that fails to build would look green.
    xml.unlink(missing_ok=True)
    server = None
    started = time.time()

    try:
        server = boot(target, port, logs / f"server-{slug}.log")
        if not wait_for(base, BOOT_TIMEOUT):
            raise RuntimeError(f"app did not answer on {base} within {BOOT_TIMEOUT}s")
        proc = subprocess.run(
            [str(py), "-m", "pytest", str(verify_dir), "-q", f"--junit-xml={xml}"],
            cwd=project, capture_output=True, text=True, timeout=TEST_TIMEOUT,
            # APP_DIR is the target actually under test - app/ or skeleton/.
            # Without it a test cannot find the running app's own files: the
            # suite runs with cwd=project from project/verify for app/, with
            # cwd=project from skeleton/verify for skeleton/, and with cwd=
            # skeleton for a student running it by hand. No relative path works
            # for all three, so a project with a file store had no way to reset
            # it - which is what habit-tracker's Gate 1 round 3 found.
            env={**os.environ, "BASE_URL": base, "APP_DIR": str(target),
                 "PYTHONDONTWRITEBYTECODE": "1"})
        stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except Exception as e:
        stdout, stderr, rc = "", str(e), BOOT_FAILED_RC
    finally:
        stop_server(server)

    by_node = parse_junit(xml)
    criteria = map_to_criteria(spec, coverage, by_node)
    counts = {k: sum(1 for v in criteria.values() if v["status"] == k)
              for k in ("pass", "fail", "skip", "missing")}

    # Named static checks the spec declares. They run against app/ only: a
    # skeleton has the code cut out of it, so it would pass them trivially.
    # A failure here fails the step, so it lands in the Builder/test-runner loop
    # instead of in the "nothing catches it" column at Gate 1.
    code = code_check.run(project, a.target) if a.target == "app" else {"ok": True,
                                                                        "checks": {}}

    # The stack the human gave, against what app/ actually declares. Unlike
    # code_check this is not opt-in: a spec that declares no code_checks still
    # cannot be allowed to ship something built on a stack nobody asked for,
    # and demo-run-01 declared none.
    stack = (stack_check.check(project, a.target) if a.target == "app"
             else {"ok": True, "violations": []})

    report = {
        "ok": (rc == 0 and counts["fail"] == 0 and counts["missing"] == 0
               and code.get("ok", True) and stack.get("ok", True)),
        "target": a.target,
        "code_checks": code,
        "stack_check": stack,
        "seconds": round(time.time() - started, 1),
        "counts": counts,
        "criteria": criteria,
        "pytest_returncode": rc,
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-3000:],
    }
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("ok", "target", "counts", "seconds")}, indent=2))
    for bad in (stack.get("violations") or []):
        print(f"\nstack check {bad['code']}: {bad['message']}", file=sys.stderr)
    for name, res in (code.get("checks") or {}).items():
        if not res["ok"]:
            print(f"\ncode check '{name}' failed - {res['count']} violation(s):",
                  file=sys.stderr)
            for v in res["violations"][:10]:
                print(f"  {v['file']}:{v['line']}  {v['found']}  -> {v['fix']}",
                      file=sys.stderr)
    for name in (code.get("unknown") or []):
        print(f"\nspec declares an unknown code check: {name!r}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
