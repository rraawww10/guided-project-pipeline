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
from fnmatch import fnmatch
from pathlib import Path

# Two marker vocabularies, both supported. The first is what the three shipped
# projects use; the second is the form in requirements_doc.md:
#
#   // >>> CUT cut-api-todos-list          ... // <<< CUT cut-api-todos-list
#   # >>> STUDENT S03-T01 START            ... # <<< STUDENT S03-T01 END
#         #     goal: <one line>
#
# The doc's optional `goal:` line sits inside the block and is removed with it;
# the TODO the student reads comes from the task's hint in spec.json, which is
# the wording a person approved at Gate 1.
TASK_ID = r"(?:cut-[a-z0-9][a-z0-9-]*|S\d{1,3}-T\d{1,3})"
OPEN = re.compile(
    r"^(?P<indent>\s*)(?P<lead>\S.*?)>>>\s*(?:CUT|STUDENT)\s+(?P<id>" + TASK_ID +
    r")(?:\s+START)?\s*(?P<trail>.*?)$")
CLOSE = re.compile(
    r"^\s*\S.*?<<<\s*(?:CUT|STUDENT)\s+(?P<id>" + TASK_ID + r")(?:\s+END)?\s*.*?$")
# cheap "is there anything to cut here" test, either vocabulary
MARKER_HINT = re.compile(r">>>\s*(?:CUT|STUDENT)\s")

SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".turbo",
             "coverage", "__pycache__", ".venv", ".pipeline"}
# Generated files that must never reach a student, whatever the project's
# .gitignore happens to say. Both shipped skeletons carry a stale
# tsconfig.tsbuildinfo purely because those projects listed it themselves.
SKIP_FILE_GLOBS = ("*.tsbuildinfo", ".DS_Store")


def gitignore_matcher(root: Path):
    """Honour the project's own `.gitignore` when copying it.

    `data/` is not in SKIP_DIRS and must not be, because a seed file the student
    needs lives there. But a project with a *mutable* file store has a live copy
    that must not ship: step 6's tests leave it mutated, and it was being copied
    straight into the skeleton and into the step-10 fresh copy. A student's first
    `npm run dev` then shows the state some test left behind.

    The project already declares which of the two is which - the live store is
    gitignored and the seed is tracked - so that declaration is what this reads.
    Only the pattern forms a generated project actually uses: a path, a basename
    glob, a trailing-slash directory, and `!` to un-ignore. Last match wins, as
    git does. No `.gitignore`, no exclusions - so this changes nothing for a
    project that does not use one.
    """
    rules: list[tuple[bool, str, bool]] = []
    gi = root / ".gitignore"
    if gi.exists():
        for raw in gi.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            neg = line.startswith("!")
            if neg:
                line = line[1:].strip()
            dir_only = line.endswith("/")
            rules.append((neg, line.strip("/"), dir_only))

    def ignored(rel: Path) -> bool:
        if not rules:
            return False
        posix = rel.as_posix()
        parts = rel.parts
        hit = False
        for neg, pat, dir_only in rules:
            if "/" in pat:
                matched = fnmatch(posix, pat) or posix.startswith(pat + "/")
            elif dir_only:
                matched = pat in parts[:-1]
            else:
                matched = any(fnmatch(part, pat) for part in parts)
            if matched:
                hit = not neg
        return hit

    return ignored

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


def walk_source(root: Path, respect_gitignore: bool = True):
    ignored = gitignore_matcher(root) if respect_gitignore else (lambda rel: False)
    for p in sorted(root.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
            continue
        if any(fnmatch(p.name, g) for g in SKIP_FILE_GLOBS):
            continue
        if ignored(p.relative_to(root)):
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

    # Needs no toolchain, so unlike typecheck() it cannot fail open.
    unsafe = scan_return_safety(app, hints)
    if unsafe:
        raise CutError(
            f"{len(unsafe)} cut(s) remove their function's only return - the skeleton "
            f"would not compile and the student's app would not build at all:\n  "
            + "\n  ".join(f"{u['cut']} at {u['file']}:{u['line']} "
                           f"(function lines {u['function_lines'][0]}-{u['function_lines'][1]}"
                           f"{', typed return' if u['declared_return_type'] else ''})"
                           for u in unsafe)
            + "\n\n" + RETURN_FIX)

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
        if not MARKER_HINT.search(text):
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
    out["return_safety"] = {"ok": True, "checked": len(hints), "violations": []}
    out["partial_state_risks"] = partial_state_risks(spec)
    tc = typecheck(project)
    out["typecheck"] = tc
    # The static scan above already raised on the TS2355 shape, so a typecheck
    # that could not run no longer means the check passed. It is recorded as
    # fail_open so Gate 3 can see the difference between "clean" and "not run".
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
        return {"ran": False, "ok": True, "fail_open": True,
                "why": "no tsconfig.json in the skeleton - the static return-safety "
                       "scan is the only guard that ran"}

    # the skeleton is generated without node_modules; borrow the app's
    modules = skel / "node_modules"
    borrowed = ""
    if not modules.exists() and (app / "node_modules").exists():
        try:
            borrowed = link_dir((app / "node_modules").resolve(), modules)
        except OSError as e:
            return {"ran": False, "ok": True, "fail_open": True,
                    "why": f"could not borrow the app's node_modules: {e} - the "
                           f"static return-safety scan is the only guard that ran"}
    if not modules.exists():
        return {"ran": False, "ok": True, "fail_open": True,
                "why": "no node_modules to typecheck against - run the test runner once "
                       "first. The static return-safety scan is the only guard that ran"}

    # On Windows the extensionless .bin/tsc is a shell script: running it raises
    # WinError 193 and the typecheck fails open for a reason that has nothing to
    # do with the cuts. The .cmd shim next to it is the one Windows can execute.
    bin_dir = app / "node_modules" / ".bin"
    names = ["tsc.cmd", "tsc"] if sys.platform == "win32" else ["tsc"]
    tsc = next((bin_dir / n for n in names if (bin_dir / n).exists()), None)
    cmd = [str(tsc)] if tsc else ["npx", "--no-install", "tsc"]
    try:
        r = subprocess.run([*cmd, "--noEmit", "-p", "tsconfig.json"],
                           cwd=skel, capture_output=True, text=True, timeout=300)
        out = (r.stdout + r.stderr).strip()
        rc = r.returncode
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ran": False, "ok": True, "fail_open": True,
                "why": f"could not run tsc: {e} - the static return-safety scan is "
                       f"the only guard that ran"}
    finally:
        if borrowed:
            unlink_dir(modules, borrowed)
        # an incremental tsconfig makes tsc write a .tsbuildinfo even under
        # --noEmit. SKIP_FILE_GLOBS already swept the skeleton by now, so this
        # guard would otherwise leave its own droppings behind for the student.
        for stale in skel.rglob("*.tsbuildinfo"):
            stale.unlink(missing_ok=True)

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


def link_dir(src: Path, dst: Path) -> str:
    """Point dst at the directory src, as cheaply as this platform allows.

    Returns how it was done: "symlink", "junction" or "copy" - the caller needs
    that to take it back down again.

    os.symlink needs SeCreateSymbolicLinkPrivilege on Windows - without admin or
    Developer Mode it raises WinError 1314 - so `pipeline cut` crashed here,
    wrote no skeleton and no skeleton-check.json, and the phase-2 workflow read
    the missing report as a verdict on the cut markers. A junction needs no
    privilege and behaves the same way for reading node_modules. Copying is the
    last resort: correct, just slow, and node_modules is large.
    """
    try:
        os.symlink(src, dst, target_is_directory=True)
        return "symlink"
    except OSError:
        pass
    if sys.platform == "win32":
        try:
            import _winapi
            _winapi.CreateJunction(str(src), str(dst))
            return "junction"
        except (ImportError, OSError):
            pass
    shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
    return "copy"


def unlink_dir(dst: Path, kind: str) -> None:
    """Undo link_dir. A junction is a directory entry, not a file: Path.unlink
    raises on it, which would turn cleanup into the next crash."""
    try:
        if kind == "symlink":
            dst.unlink(missing_ok=True)
        elif kind == "junction":
            os.rmdir(dst)
        elif kind == "copy":
            shutil.rmtree(dst, ignore_errors=True)
    except OSError:
        pass


# --- static return safety -------------------------------------------------
# The one defect that recurred across consecutive projects. recipe-box round 1
# had six cuts that removed their function's only return; tip-split round 1 then
# did it again in both route handlers with the lesson already written down. The
# skeleton does not compile - not one red test, no build at all, and the
# student's whole app stops working.
#
# typecheck() below catches it with tsc, but it FAILS OPEN: no tsconfig, no
# node_modules or no tsc and it returns ok=True. On a fresh clone that is every
# project. This check needs no toolchain, so it is the one that always runs.

FUNC_HEADER = re.compile(
    r"(?:^|\s)(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+\w*\s*\("
    r"|(?:const|let|var)\s+\w+\s*(?::[^=]+)?=\s*(?:async\s*)?\("
    r"|(?:const|let|var)\s+\w+\s*(?::[^=]+)?=\s*(?:async\s*)?\w+\s*=>"
)
RETURN_STMT = re.compile(r"(?:^|[{};]|\)\s*)\s*return\b")
RETURN_TYPE = re.compile(r"\)\s*:\s*[^{;=]+\s*(?:\{|=>)")
CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


def _strip_noise(line: str) -> str:
    """Good enough for brace counting: drop line comments and string bodies."""
    line = re.sub(r"//.*$", "", line)
    line = re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`", '""', line)
    return line


def _cut_spans(text: str) -> list[tuple[str, int, int]]:
    """(cut id, open line index, close line index) - 0-based, inclusive."""
    spans, open_id, open_at = [], None, 0
    for i, line in enumerate(text.splitlines()):
        mo, mc = OPEN.match(line), CLOSE.match(line)
        if mo and not mc:
            open_id, open_at = mo["id"], i
        elif mc and open_id is not None:
            spans.append((open_id, open_at, i))
            open_id = None
    return spans


def _enclosing_function(lines: list[str], at: int) -> tuple[int, int, bool] | None:
    """Innermost function body containing line `at`. (start, end, typed)."""
    best = None
    for i in range(at, -1, -1):
        if not FUNC_HEADER.search(_strip_noise(lines[i])):
            continue
        # find the body's opening brace, then its match
        depth, start, j = 0, None, i
        while j < len(lines):
            for ch in _strip_noise(lines[j]):
                if ch == "{":
                    depth += 1
                    if start is None:
                        start = j
                elif ch == "}":
                    depth -= 1
                    if start is not None and depth == 0:
                        if start <= at <= j:
                            typed = bool(RETURN_TYPE.search(
                                " ".join(_strip_noise(x) for x in lines[i:start + 1])))
                            return (start, j, typed)
                        best = best or None
                        j = len(lines)
                        break
            else:
                j += 1
                continue
            break
    return best


def scan_return_safety(root: Path, hints: dict[str, dict]) -> list[dict]:
    """Every cut whose block holds its function's only return statement."""
    found: list[dict] = []
    for src_path in walk_source(root, respect_gitignore=False):
        if src_path.suffix not in CODE_EXT:
            continue
        try:
            text = src_path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        if not MARKER_HINT.search(text):
            continue
        lines = text.splitlines()
        for cut_id, a, b in _cut_spans(text):
            inside = [i for i in range(a + 1, b)
                      if RETURN_STMT.search(_strip_noise(lines[i]))]
            if not inside:
                continue
            fn = _enclosing_function(lines, a)
            if fn is None:
                continue                      # cannot tell - stay quiet
            start, end, typed = fn
            outside = [i for i in range(start, end + 1)
                       if (i < a or i > b) and RETURN_STMT.search(_strip_noise(lines[i]))]
            if outside:
                continue
            found.append({
                "cut": cut_id,
                "file": str(src_path),
                "line": a + 1,
                "function_lines": [start + 1, end + 1],
                "declared_return_type": typed,
                "returns_inside_cut": [i + 1 for i in inside],
            })
    return found


RETURN_FIX = (
    "Keep the return OUTSIDE the markers and cut the assignment that feeds it:\n\n"
    "  export async function GET(): Promise<Response> {\n"
    "    let body: { ok: boolean } = { ok: false }\n"
    "    let status = 501\n"
    "    // >>> CUT cut-api-health\n"
    "    body = { ok: true }\n"
    "    status = 200\n"
    "    // <<< CUT cut-api-health\n"
    "    return Response.json(body, { status })\n"
    "  }\n\n"
    "The fallback must not accidentally pass the test - a 501 and ok:false fail the\n"
    "criterion, which is what the skeleton needs. Proven both ways in\n"
    "fixtures/runner-check."
)


def partial_state_risks(spec: dict) -> list[dict]:
    """Where a proper subset of a criterion's cuts may satisfy it.

    The skeleton check proves two things only: a criterion with all its cuts
    open must fail, and a criterion with no cuts must pass. It says nothing
    about the states a student actually moves through. Two cuts graded by
    exactly the same criteria are precisely that blind spot - recipe-box c-3-2
    goes green with cut-store-find-one still empty.

    The spec linter now rejects this shape at step 2 (E110), so this is the
    belt-and-braces report for a spec that predates the rule.
    """
    sig: dict[str, set[str]] = {}
    for s in spec.get("sessions", []):
        for c in s.get("criteria", []):
            for cut in c.get("cuts", []):
                sig.setdefault(cut, set()).add(c["id"])
    groups: dict[frozenset, list[str]] = {}
    for cut, crits in sig.items():
        groups.setdefault(frozenset(crits), []).append(cut)
    return [{"cuts": sorted(v), "graded_only_by": sorted(k)}
            for k, v in sorted(groups.items(), key=lambda kv: sorted(kv[1]))
            if len(v) > 1]


def sweep_generated(project: Path) -> list[str]:
    """Delete build artifacts the pipeline's own checks wrote into skeleton/.

    Excluding these from the copy is not enough: step 8 typechecks the skeleton
    with `tsc` and boots it with `npm run build`, and both write into it after
    the copy is made. habit-tracker's Gate 1 round 4 B4 flagged the shipped
    artifact; I answered that unconditional exclusion made it moot, and it did
    not - tip-split's tsconfig.tsbuildinfo is git-tracked to this day. The
    skeleton is the student's starting point, so it is swept once the checks
    that needed it are done.
    """
    skel = project / "skeleton"
    removed = []
    if not skel.exists():
        return removed
    for path in sorted(skel.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(skel).parts):
            continue          # inside node_modules/.next - not ours to touch
        if any(fnmatch(path.name, g) for g in SKIP_FILE_GLOBS):
            path.unlink()
            removed.append(path.relative_to(skel).as_posix())
    return removed


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

    risks = partial_state_risks(spec)
    manifest = project / "skeleton" / ".cut-manifest.json"
    fail_open = False
    if manifest.exists():
        tc = json.loads(manifest.read_text()).get("typecheck") or {}
        fail_open = bool(tc.get("fail_open"))

    report = {
        "ok": not wrong,
        "checked": len(expect),
        "mismatches": wrong,
        # Known blind spot, made visible instead of left in a lesson file: the
        # check above only ever sees the fully-open skeleton.
        "partial_state_risks": risks,
        "blind_spot": (
            "this check proves only that a criterion fails with ALL its cuts open and "
            "passes with none. Cuts listed in partial_state_risks share a grading "
            "signature, so a proper subset of them satisfies their criteria - check "
            "those by hand, or fix the spec (linter E110)." if risks else ""),
        "typecheck_fail_open": fail_open,
    }
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
