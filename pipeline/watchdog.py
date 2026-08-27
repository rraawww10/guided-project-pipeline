"""Nightly watchdog - SCRIPT, step 12.

Replays the committed test script on every shipped project. Runs every night on
every project, so an agent here is a bill that keeps growing.

  python -m pipeline.watchdog [--root .] [--only slug,slug]

Exit 0 if every shipped project still passes, 1 otherwise. Wire to cron.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import test_runner


def shipped(root: Path) -> list[Path]:
    return sorted(p for p in (root / "projects").glob("*")
                  if (p / ".pipeline" / "SHIPPED").exists())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    wanted = {s.strip() for s in a.only.split(",") if s.strip()}
    projects = [p for p in shipped(root) if not wanted or p.name in wanted]

    runs = []
    for p in projects:
        rc = test_runner.main([str(p), "--target", "app", "--out", "watchdog-results.json"])
        res = json.loads((p / "watchdog-results.json").read_text())
        broke = [cid for cid, c in res.get("criteria", {}).items()
                 if c["status"] in ("fail", "missing")]
        runs.append({"slug": p.name, "ok": rc == 0, "broken_criteria": broke,
                     "counts": res.get("counts", {})})

    report = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": all(r["ok"] for r in runs),
        "checked": len(runs),
        "broken": [r for r in runs if not r["ok"]],
        "runs": runs,
    }
    out = root / "projects" / "watchdog-latest.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("at", "ok", "checked")}, indent=2))
    for r in report["broken"]:
        print(f"BROKEN {r['slug']}: {', '.join(r['broken_criteria']) or 'boot or build failed'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
