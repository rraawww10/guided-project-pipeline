"""Cutter - SCRIPT, step 8.

Builds the student skeleton by removing marked blocks from the final code.
Rule 4: the skeleton is always generated, never written by hand. The same final
code must produce the same skeleton every run, so there is no agent in here.

  python -m pipeline.cutter cut    <project-dir>
  python -m pipeline.cutter verify <project-dir>
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

OPEN = re.compile(r"^(?P<indent>\s*)(?P<lead>\S.*?)>>>\s*CUT\s+(?P<id>cut-[a-z0-9-]+)\s*(?P<trail>.*?)$")
CLOSE = re.compile(r"^\s*\S.*?<<<\s*CUT\s+(?P<id>cut-[a-z0-9-]+)\s*.*?$")

SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".turbo",
             "coverage", "__pycache__", ".venv", ".pipeline"}

# comment style per extension, so the TODO we leave behind actually compiles
LINE_COMMENT = {
    ".ts": "//", ".tsx": "//", ".js": "//", ".jsx": "//", ".mjs": "//", ".cjs": "//",
    ".css": None, ".scss": None, ".html": None, ".md": None, ".json": None,
    ".py": "#", ".sh": "#", ".yml": "#", ".yaml": "#", ".env": "#",
}
BLOCK_COMMENT = {".css": ("/*", "*/"), ".scss": ("/*", "*/"),
                 ".html": ("<!--", "-->"), ".md": ("<!--", "-->")}


class CutError(Exception):
    pass


def todo_line(path: Path, indent: str, cut_id: str, hint: str, in_jsx: bool) -> str:
    text = f"TODO({cut_id}): {hint}"
    ext = path.suffix
    if in_jsx:
        return f"{indent}{{/* {text} */}}"
    line = LINE_COMMENT.get(ext, "//")
    if line:
        return f"{indent}{line} {text}"
    open_c, close_c = BLOCK_COMMENT.get(ext, ("/*", "*/"))
    return f"{indent}{open_c} {text} {close_c}"


def load_hints(spec: dict) -> dict[str, dict]:
    hints = {}
    for s in spec.get("sessions", []):
        for c in s.get("cuts", []):
            hints[c["id"]] = {"hint": c.get("hint", ""), "file": c.get("file", ""),
                              "session": s.get("n")}
    return hints


def walk_source(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def cut_file(path: Path, text: str, hints: dict[str, dict]) -> tuple[str, list[dict]]:
    """Return (skeleton text, list of cuts applied). Raises on malformed markers."""
    out: list[str] = []
    applied: list[dict] = []
    open_id: str | None = None
    open_line = 0
    removed: list[str] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        m_open = OPEN.match(line)
        m_close = CLOSE.match(line)

        if m_open and not m_close:
            if open_id is not None:
                raise CutError(f"{path}:{lineno} cut {m_open['id']} opens inside "
                               f"open cut {open_id} (line {open_line}) - cuts must not nest")
            open_id = m_open["id"]
            open_line = lineno
            if open_id not in hints:
                raise CutError(f"{path}:{lineno} marker {open_id} is not declared in spec.json")
            indent = m_open["indent"]
            in_jsx = "{/*" in m_open["lead"]
            out.append(todo_line(path, indent, open_id, hints[open_id]["hint"], in_jsx))
            removed = []
            continue

        if m_close:
            if open_id is None:
                raise CutError(f"{path}:{lineno} close marker {m_close['id']} with nothing open")
            if m_close["id"] != open_id:
                raise CutError(f"{path}:{lineno} closes {m_close['id']} but "
                               f"{open_id} is open (line {open_line})")
            applied.append({"id": open_id, "file": str(path), "line": open_line,
                            "lines_removed": len(removed)})
            open_id = None
            continue

        if open_id is not None:
            removed.append(line)
        else:
            out.append(line)

    if open_id is not None:
        raise CutError(f"{path}:{open_line} cut {open_id} is never closed")

    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing, applied


def cut(project: Path) -> dict:
    spec = json.loads((project / "spec.json").read_text())
    hints = load_hints(spec)
    app, skel = project / "app", project / "skeleton"
    if not app.exists():
        raise CutError(f"{app} does not exist - nothing to cut")

    if skel.exists():
        shutil.rmtree(skel)
    skel.mkdir(parents=True)

    manifest: list[dict] = []
    for src in walk_source(app):
        rel = src.relative_to(app)
        dst = skel / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = src.read_text()
        except UnicodeDecodeError:
            shutil.copy2(src, dst)
            continue
        if ">>> CUT" not in text and "<<< CUT" not in text:
            shutil.copy2(src, dst)
            continue
        new_text, applied = cut_file(rel, text, hints)
        dst.write_text(new_text)
        manifest.extend(applied)

    found = {m["id"] for m in manifest}
    declared = set(hints)
    missing = sorted(declared - found)
    if missing:
        raise CutError("cut ids declared in spec.json but not found in the code: "
                       + ", ".join(missing))
    seen: dict[str, int] = {}
    for m in manifest:
        seen[m["id"]] = seen.get(m["id"], 0) + 1
    dupes = sorted(i for i, c in seen.items() if c > 1)
    if dupes:
        raise CutError("cut ids appear more than once in the code: " + ", ".join(dupes))

    # the verify tree ships with the skeleton so the student can run the same checks
    verify_src = project / "verify"
    if verify_src.exists():
        shutil.copytree(verify_src, skel / "verify", dirs_exist_ok=True)

    out = {
        "slug": spec["slug"],
        "cuts": sorted(manifest, key=lambda m: (m["file"], m["line"])),
        "count": len(manifest),
        "by_session": {
            str(n): sorted(i for i, h in hints.items() if h["session"] == n)
            for n in sorted({h["session"] for h in hints.values()})
        },
    }
    tc = typecheck(project)
    out["typecheck"] = tc
    out["ok"] = tc["ok"]
    (skel / ".cut-manifest.json").write_text(json.dumps(out, indent=2) + "\n")
    if not tc["ok"]:
        raise CutError(
            f"the skeleton does not compile - {tc['error_count']} typescript errors:\n  "
            + "\n  ".join(tc["errors"][:10])
            + (f"\n\n{tc['hint']}" if tc["hint"] else ""))
    return out


def typecheck(project: Path) -> dict:
    """The skeleton must still compile.

    A cut that removes a typed function's only `return` leaves the skeleton
    unbuildable. The skeleton check would catch it eventually - a project that
    does not build fails every test, including the criteria that must pass - but
    only after the whole Builder phase has run. This catches it in two seconds,
    right where the cut was made.
    """
    skel, app = project / "skeleton", project / "app"
    tsconfig = skel / "tsconfig.json"
    if not tsconfig.exists():
        return {"ran": False, "ok": True, "why": "no tsconfig.json in the skeleton"}

    # the skeleton is generated without node_modules; borrow the app's
    modules = skel / "node_modules"
    borrowed = False
    if not modules.exists() and (app / "node_modules").exists():
        os.symlink(app / "node_modules", modules, target_is_directory=True)
        borrowed = True
    if not modules.exists():
        return {"ran": False, "ok": True,
                "why": "no node_modules to typecheck against - run the test runner once first"}

    tsc = app / "node_modules" / ".bin" / "tsc"
    cmd = [str(tsc)] if tsc.exists() else ["npx", "--no-install", "tsc"]
    try:
        r = subprocess.run([*cmd, "--noEmit", "-p", "tsconfig.json"],
                           cwd=skel, capture_output=True, text=True, timeout=300)
        out = (r.stdout + r.stderr).strip()
        rc = r.returncode
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ran": False, "ok": True, "why": f"could not run tsc: {e}"}
    finally:
        if borrowed:
            modules.unlink(missing_ok=True)

    errors = [ln for ln in out.splitlines() if ": error TS" in ln]
    # TS2355: a function whose declared type is not void must return a value.
    # That is exactly the shape of a cut that removed the only return.
    returns = [ln for ln in errors if "TS2355" in ln or "TS7030" in ln]
    return {
        "ran": True, "ok": rc == 0, "error_count": len(errors),
        "errors": errors[:40],
        "missing_return": returns[:20],
        "hint": ("A cut removed the only return of a typed function. Keep a typed fallback "
                 "return outside the markers, so the skeleton still compiles with the block "
                 "replaced by its hint comment.") if returns else "",
    }


def expected_skeleton_results(spec: dict) -> dict[str, str]:
    """A criterion whose cuts were removed must FAIL on the skeleton.
    A criterion with no cuts is given to the student, so it must PASS."""
    expect = {}
    for s in spec.get("sessions", []):
        for c in s.get("criteria", []):
            expect[c["id"]] = "fail" if c.get("cuts") else "pass"
    return expect


def verify(project: Path) -> dict:
    """Step 8's check: the skeleton fails the right tests, and only those."""
    spec = json.loads((project / "spec.json").read_text())
    results_path = project / "skeleton-results.json"
    if not results_path.exists():
        raise CutError("skeleton-results.json is missing - run the test runner "
                       "against skeleton/ first")
    actual = json.loads(results_path.read_text()).get("criteria", {})
    expect = expected_skeleton_results(spec)

    wrong = []
    for cid, want in expect.items():
        got = actual.get(cid, {}).get("status", "missing")
        if got != want:
            wrong.append({"criterion": cid, "expected": want, "actual": got})

    report = {"ok": not wrong, "checked": len(expect), "mismatches": wrong}
    (project / "skeleton-check.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in {"cut", "verify", "typecheck"}:
        print("usage: python -m pipeline.cutter {cut|verify|typecheck} <project-dir>", file=sys.stderr)
        return 2
    project = Path(argv[2]).resolve()
    ops = {"cut": cut, "verify": verify, "typecheck": typecheck}
    try:
        result = ops[argv[1]](project)
    except CutError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
