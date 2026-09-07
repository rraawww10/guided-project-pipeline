"""stack_check - SCRIPT. Does the built app use the stack the human gave?

requirements_doc.md names two rules that never change, and the first is "The
human gives the tech stack. The AI does not choose it." Nothing enforced it.

demo-run-01 is what that costs. The stack was next, react, typescript. The
builder hit a failing build and, instead of repairing it, replaced the project
with a 241-line vanilla node http server that reimplemented the app inline -
its own seed data, its own scoring, hand-written HTML strings. It declared no
dependencies at all and set

    "build": "node -e \"console.log('build ok')\""

The suite then passed 13 of 13, because the tests assert HTTP responses and DOM
testids and the replacement answered both. Every .tsx and .ts file - including
all five that hold cut markers - was dead code nothing executed.

Only `mutation` would have caught it: deleting a marker in a file that never
runs turns no test red, so all five would have come back ungraded. That is 30
minutes into step 8, and it reports "tasks grade nothing" rather than "your
stack is gone". This check reads two files and says so in two seconds.

It runs against app/ only, like code_check: a skeleton has its code cut out.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Stack tokens that name a runtime or a language rather than an npm package.
# Requiring a dependency entry for these would fail every honest project.
NOT_PACKAGES = {"node", "nodejs", "npm", "javascript", "js", "html", "css",
                "json", "rest", "http", "browser", "web"}

# Stack token -> the npm package that proves it is really in use.
PACKAGE_ALIASES = {
    "nextjs": "next", "next.js": "next",
    "react.js": "react", "reactjs": "react",
    "ts": "typescript",
    "vuejs": "vue", "vue.js": "vue",
    "tailwind": "tailwindcss",
    "node-express": "express",
}

# Stack token -> build commands that actually invoke it. A stack with any of
# these present must show one of them in its build script; a stack of pure
# libraries (react alone) is not held to it, because there is no CLI to name.
BUILD_COMMANDS = {
    "next": ("next build",),
    "vite": ("vite build",),
    "typescript": ("tsc", "next build", "vite build", "svelte-kit build"),
    "svelte": ("svelte-kit build", "vite build"),
    "nuxt": ("nuxt build", "nuxi build"),
    "astro": ("astro build",),
    "remix": ("remix vite:build", "remix build"),
    "webpack": ("webpack",),
    "parcel": ("parcel build",),
}

# Stack token -> the command that actually RUNS it. Declaring next as a
# dependency and then starting `node server.js` leaves the framework installed
# and never executed, which is how demo-run-01 passed the first version of this
# check: it added the four dependencies and kept the impostor server.
RUN_COMMANDS = {
    "next": ("next start", "next dev"),
    "vite": ("vite preview", "vite dev", "vite"),
    "svelte": ("svelte-kit preview", "vite preview"),
    "nuxt": ("nuxt start", "nuxt preview", "nuxi preview"),
    "astro": ("astro preview",),
    "remix": ("remix-serve", "remix vite:dev"),
}

# `next build || node -e ""` succeeds whichever way the build goes. An || in a
# build or start script means the step can no longer fail, and a step that
# cannot fail is not a check. && is fine - that is sequencing, not a fallback.
SWALLOWS_FAILURE = re.compile(r"\|\||;\s*(?:true|exit\s+0)")

# A build script that cannot be building anything.
INERT_BUILD = re.compile(
    r"^\s*(?:"
    r"true|:|exit\s+0"
    r"|echo\b"
    r"|node\s+-e\b"
    r"|node\s+--eval\b"
    r"|printf\b"
    r")",
    re.IGNORECASE)


# The deploy check already refuses an install that prints a deprecation warning.
# It refuses it at STEP 12, after the code phase, both gates, the skeleton and
# the guide - and each failure sends the Builder back to guess another version.
# demo-run-03 spent five deploy runs and four Builder calls cycling 14.2.12 ->
# 14.2.16 -> 15.5.7 -> 16.0.0, all flagged. The same fact is available from the
# registry in two seconds at step 7, before any of that is built.
REGISTRY = os.environ.get("NPM_REGISTRY", "https://registry.npmjs.org")
REGISTRY_TIMEOUT = float(os.environ.get("STACK_CHECK_TIMEOUT", "10"))


def deprecated_version(package: str, spec: str) -> tuple[str, str] | None:
    """(version, message) when an EXACT pin is deprecated. None otherwise.

    Only exact pins are judged. `^15.5.4` resolves at install time to whatever
    is newest then, which this cannot know and must not guess about.
    """
    version = spec.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        return None
    url = f"{REGISTRY}/{package}/{version}"
    try:
        with urllib.request.urlopen(url, timeout=REGISTRY_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None                      # offline, or the registry is unwell
    message = data.get("deprecated")
    return (version, str(message)[:200]) if message else None


def normalise(token: str) -> str:
    token = token.strip().lower()
    return PACKAGE_ALIASES.get(token, token)


def read_json(path: Path) -> tuple[dict | None, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except FileNotFoundError:
        return None, f"{path.name} does not exist"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"cannot read {path.name}: {exc}"


def check(project: Path, target: str = "app") -> dict:
    """Compare the stack the human gave against what app/ actually declares."""
    stack_data, why = read_json(project / "stack.json")
    if stack_data is None:
        # Flow 1 predates `pipeline stack`, and a project with no recorded stack
        # has nothing to be measured against. Skipping is not passing: the
        # report says which it was, so a green report cannot be read as proof.
        return {"ok": True, "skipped": f"no stack on record ({why})",
                "stack": [], "violations": []}

    raw = [str(s) for s in (stack_data.get("stack") or [])]
    stack = [normalise(s) for s in raw]
    packages = [s for s in stack if s not in NOT_PACKAGES]
    root = project / target
    pkg_path = root / "package.json"

    if not packages:
        return {"ok": True, "skipped": "the stack names no npm package",
                "stack": raw, "violations": []}
    if not pkg_path.exists() and not any(root.glob("**/*.json")):
        return {"ok": True, "skipped": f"{target}/ has not been built yet",
                "stack": raw, "violations": []}

    violations: list[dict] = []
    pkg, why = read_json(pkg_path)
    if pkg is None:
        violations.append({
            "code": "S001",
            "message": f"{target}/package.json is missing, so npm cannot install "
                       f"or build anything ({why}). The stack is {', '.join(raw)}.",
        })
        return {"ok": False, "stack": raw, "declared": {}, "violations": violations}

    declared = {}
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        declared.update(pkg.get(field) or {})
    declared_names = {k.lower() for k in declared}

    for name in packages:
        if name not in declared_names:
            violations.append({
                "code": "S002",
                "message": f"the human gave '{name}' in the stack, but "
                           f"{target}/package.json declares no such dependency. "
                           f"It declares: {', '.join(sorted(declared_names)) or 'nothing'}.",
            })

    scripts = pkg.get("scripts") or {}
    build = str(scripts.get("build") or "")
    if not build:
        violations.append({
            "code": "S003",
            "message": f"{target}/package.json has no build script, so nothing "
                       f"compiles the {', '.join(raw)} sources.",
        })
    else:
        if INERT_BUILD.match(build):
            violations.append({
                "code": "S003",
                "message": f"the build script does not build anything: {build!r}. "
                           f"A build that prints a string passes every check that "
                           f"only asks whether the build succeeded.",
            })
        wanted: list[str] = []
        for name in packages:
            wanted.extend(BUILD_COMMANDS.get(name, ()))
        if wanted and not any(cmd in build.lower() for cmd in wanted):
            violations.append({
                "code": "S004",
                "message": f"the build script {build!r} never invokes the stack. "
                           f"Expected one of: {', '.join(sorted(set(wanted)))}.",
            })

    start = str(scripts.get("start") or "")
    runners: list[str] = []
    for name in packages:
        runners.extend(RUN_COMMANDS.get(name, ()))
    if runners and not any(cmd in start.lower() for cmd in runners):
        violations.append({
            "code": "S005",
            "message": f"the start script {start!r} does not run the stack. The "
                       f"dependency can be installed and never executed. Expected "
                       f"one of: {', '.join(sorted(set(runners)))}.",
        })

    for field, script in (("build", build), ("start", start)):
        if script and SWALLOWS_FAILURE.search(script):
            violations.append({
                "code": "S006",
                "message": f"the {field} script swallows its own failure: "
                           f"{script!r}. With a fallback it succeeds whichever way "
                           f"it goes, so it is no longer a check.",
            })

    # S008: `npm ci` refuses outright when package.json and package-lock.json
    # disagree, and it is the SKELETON that finds out. app/ keeps a populated
    # node_modules from earlier steps, so `boot()` skips the install there and a
    # stale lock never surfaces; skeleton/ is the first genuinely clean tree in
    # the run. 2026-09-07, stock-tracker: the Builder bumped next 14.2.13 ->
    # 16.1.1 to clear an S007 advisory and left the lock on 14.2.13. app/ went
    # 21/21 green, then the skeleton died with EUSAGE, `next build` reported
    # `next: not found`, all 21 criteria came back `missing`, and the cutter was
    # re-run four times over a fault no re-cut can reach.
    # Compared as spec strings, which is what npm reconciles first - no semver
    # needed, and a lock regenerated from the same package.json always matches.
    lock_path = root / "package-lock.json"
    if lock_path.exists():
        lock, lock_why = read_json(lock_path)
        if lock is None:
            violations.append({
                "code": "S008",
                "message": f"{target}/package-lock.json cannot be read "
                           f"({lock_why}), so `npm ci` has nothing to install "
                           f"from. Regenerate it with "
                           f"`npm install --package-lock-only`.",
            })
        else:
            locked_root = (lock.get("packages") or {}).get("", {})
            locked = {}
            for field in ("dependencies", "devDependencies", "peerDependencies"):
                locked.update(locked_root.get(field) or {})
            if locked:
                drift = []
                for name, spec in sorted(declared.items()):
                    if name not in locked:
                        drift.append(f"{name} is declared but absent from the lock")
                    elif str(locked[name]) != str(spec):
                        drift.append(f"{name}: package.json wants {spec}, "
                                     f"the lock records {locked[name]}")
                if drift:
                    violations.append({
                        "code": "S008",
                        "message": f"{target}/package-lock.json is out of sync with "
                                   f"package.json, so `npm ci` refuses to install on "
                                   f"any tree without a populated node_modules - the "
                                   f"skeleton at step 10, and the deploy check's "
                                   f"clean copy at step 12. "
                                   + "; ".join(drift)
                                   + ". Run `npm install --package-lock-only` in "
                                   + f"{target}/ and commit the lock with the "
                                   + "package.json change.",
                    })

    # S007 last: it is the only rule that reaches the network, and a project that
    # already fails S001-S006 does not need it to make the point.
    # A person may decide to ship a known advisory - `pipeline deploy
    # --allow-advisories` is that decision, and it leaves this marker. Without
    # honouring it here, step 7 would block at step 7 what step 12 was told to
    # permit, and there would be no way to take the decision at all.
    if (project / ".pipeline" / "ALLOW_ADVISORIES").exists():
        return {"ok": not violations, "target": target, "stack": raw,
                "declared": sorted(declared_names), "build": build, "start": start,
                "advisories_allowed": True, "violations": violations}
    if not violations:
        for name, spec in sorted(declared.items()):
            hit = deprecated_version(name, str(spec))
            if hit:
                version, message = hit
                violations.append({
                    "code": "S007",
                    "message": f"{name}@{version} is deprecated on the registry: "
                               f"{message} The step 12 deploy check refuses an "
                               f"install that prints this. Pick a version that "
                               f"`npm view {name}@<version> deprecated` reports "
                               f"nothing for.",
                })

    return {"ok": not violations, "target": target, "stack": raw,
            "declared": sorted(declared_names), "build": build, "start": start,
            "violations": violations}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--target", default="app")
    a = ap.parse_args(argv)
    report = check(Path(a.project).resolve(), a.target)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
