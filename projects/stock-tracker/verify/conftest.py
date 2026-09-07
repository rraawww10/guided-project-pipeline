"""Per-test isolation for the stock-tracker suite.

The suite drives one long-lived server against one SQLite file, and several
tests mutate it (PUT /api/targets, POST /api/apply-plan). Without a reset the
order of the files decides the result: pytest runs test_api_apply.py second, so
the drift it consumed was gone before c-3-3, c-4-3, c-5-3 and c-5-4 read it,
and c-2-2 lost the overweight symbol it asserts on.

prisma/seed.js upserts every seeded row back to a fixed value, so re-running it
restores holdings, targets and the budget:

    AAPL 20 @ 19500   MSFT 8 @ 41000   GOOGL 30 @ 14500   TSLA 5 @ 25000
    targets 0.30 / 0.30 / 0.25 / 0.15   budget 100000c

which leaves GOOGL and AAPL overweight, MSFT and TSLA underweight, an average
absolute drift of 4.78% and GOOGL the unique largest absolute drift. Trades are
not seeded and so accumulate; nothing asserts they start empty.
"""
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

SEED_TIMEOUT = 120


def _seed_script() -> Path | None:
    """prisma/seed.js under the target being tested, or None if there is none.

    APP_DIR is set by pipeline/test_runner.py and points at app/ or skeleton/
    depending on --target. A student running pytest by hand has no APP_DIR, so
    fall back to the CWD, which is the app directory in that run.
    """
    base_dir = Path(os.environ.get("APP_DIR", os.getcwd()))
    seed = base_dir / "prisma" / "seed.js"
    return seed if seed.exists() else None


def _db_path() -> Path | None:
    base_dir = Path(os.environ.get("APP_DIR", os.getcwd()))
    db = base_dir / "prisma" / "dev.db"
    return db if db.exists() else None


@pytest.fixture(autouse=True)
def reseed_database():
    """Restore the seeded portfolio before every test and clear Trades.

    The seed script restores holdings/targets/budget but does not touch trades.
    Clear the Trade table so tests do not see trades created by earlier tests.
    """
    seed = _seed_script()
    if seed is not None:
        r = subprocess.run(
            ["node", str(seed)], cwd=seed.parent.parent,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=SEED_TIMEOUT)
        assert r.returncode == 0, (
            f"reseed failed ({seed}): {(r.stderr or r.stdout or '').strip()[:800]}")
    # Ensure Trades do not accumulate across tests
    db = _db_path()
    if db is not None:
        try:
            conn = sqlite3.connect(str(db))
            with conn:
                conn.execute("DELETE FROM Trade;")
        finally:
            try:
                conn.close()
            except Exception:
                pass
    yield
