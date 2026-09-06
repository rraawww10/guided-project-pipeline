"""Nightly watchdog - SCRIPT, step 12.

Replays the committed test script on every shipped project. Runs every night on
every project, so an agent here is a bill that keeps growing.

  python -m pipeline.watchdog [--root .] [--only slug,slug]

Exit 0 if every shipped project still passes, 1 otherwise. Wire to cron.

Round 1 fixes:

* One project could hide every other one. `test_runner.main` raises when the
  venv cannot be built or the app will not boot, and that exception escaped the
  loop - so a single broken project meant no report at all, for anything. Each
  project is now isolated and a failure is recorded as a failure.
* The report never said what it did NOT check. The one run on record showed
  "checked": 1 with two projects on disk, and nothing flagged that.
* A shipped project whose spec no longer matches what Gate 1 approved is broken
  in a way the tests cannot see, so the drift check runs here too.
"""
from __future__ import annotations

import argparse
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import test_runner
from .state import spec_drift


def shipped(root: Path) -> list[Path]:
    return sorted(p for p in (root / "projects").glob("*")
                  if (p / ".pipeline" / "SHIPPED").exists())


def run_one(p: Path) -> dict:
    """Never raises. A broken project is a result, not the end of the run."""
    entry: dict = {"slug": p.name, "ok": False, "broken_criteria": [], "counts": {}}
    drift = spec_drift(p)
    if drift:
        entry["spec_drift"] = drift
    try:
        rc = test_runner.main([str(p), "--target", "app", "--out", "watchdog-results.json"])
    except Exception as e:
        entry["error"] = f"{type(e).__name__}: {e}"
        entry["traceback"] = traceback.format_exc()[-1500:]
        return entry
    out = p / "watchdog-results.json"
    if not out.exists():
        entry["error"] = "the test runner wrote no watchdog-results.json"
        return entry
    try:
        res = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        entry["error"] = f"watchdog-results.json is unreadable: {e}"
        return entry
    entry["broken_criteria"] = [cid for cid, c in res.get("criteria", {}).items()
                                if c.get("status") in ("fail", "missing")]
    entry["counts"] = res.get("counts", {})
    entry["ok"] = rc == 0 and not drift
    return entry


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    wanted = {s.strip() for s in a.only.split(",") if s.strip()}
    all_shipped = shipped(root)
    projects = [p for p in all_shipped if not wanted or p.name in wanted]
    skipped = [p.name for p in all_shipped if p not in projects]

    runs = [run_one(p) for p in projects]

    report = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": all(r["ok"] for r in runs) and not (wanted - {p.name for p in projects}),
        "shipped_total": len(all_shipped),
        "checked": len(runs),
        "skipped": skipped,
        "unknown_slugs": sorted(wanted - {p.name for p in all_shipped}),
        "broken": [r for r in runs if not r["ok"]],
        "runs": runs,
    }
    out = root / "projects" / "watchdog-latest.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("at", "ok", "shipped_total", "checked", "skipped",
                       "unknown_slugs")}, indent=2))
    for r in report["broken"]:
        why = r.get("error") or r.get("spec_drift") or \
            (", ".join(r["broken_criteria"]) or "boot or build failed")
        print(f"BROKEN {r['slug']}: {why}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
