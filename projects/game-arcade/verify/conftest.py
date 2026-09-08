# encoding: utf-8
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Iterator, List, Tuple

import pytest
import httpx
from playwright.sync_api import sync_playwright


# Resolve the app directory for any runtime-owned files or seed scripts.
APP_DIR = Path(os.environ.get("APP_DIR", os.getcwd()))


def _run_seed_if_present() -> None:
    """Re-run the project's seed script to restore a known state.

    Where the app has a seed script, running it IS the reset. Skip silently
    when the script is absent so targets that never had one behave as before.
    """
    # Prefer a JS seed script per stack guidance.
    seed_js = APP_DIR / "prisma" / "seed.js"
    if seed_js.exists():
        try:
            # Use node directly; do not fail the test run if the seed exits nonzero
            # in a target that hasn't implemented it yet.
            subprocess.run(
                ["node", str(seed_js)],
                cwd=str(APP_DIR),
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
        except Exception:
            # Never crash collection/execution over resets; tests must remain
            # conclusive even when no reset is available.
            pass
    # No else/return: quietly do nothing when absent.


@pytest.fixture(autouse=True)
def reset_before_each_test() -> None:
    """Autouse fixture to reset mutable state before every test.

    This isolates tests that share a long-lived server and a single database.
    """
    _run_seed_if_present()


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("BASE_URL", "http://localhost:3000")


@pytest.fixture()
def http_client(base_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=base_url, timeout=30.0, follow_redirects=True) as c:
        yield c


@pytest.fixture()
def page(base_url: str):
    # A fresh browser context per test; UI isolation is not DB isolation.
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        p = context.new_page()
        try:
            yield p
        finally:
            context.close()
            browser.close()


# Helpers for deriving the Mastermind secret and scoring, per spec

def xorshift32_stream(seed: int) -> Iterator[int]:
    x = seed & 0xFFFFFFFF
    while True:
        # xorshift32: https://en.wikipedia.org/wiki/Xorshift
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        x &= 0xFFFFFFFF
        yield x


def derive_secret(seed: int) -> List[int]:
    stream = xorshift32_stream(seed)
    return [next(stream) % 6 for _ in range(4)]


def score_guess(secret: List[int], guess: List[int]) -> Tuple[int, int]:
    # black: exact index matches
    black = sum(1 for i in range(4) if secret[i] == guess[i])
    # white: colour-only matches without double counting
    counts_secret = [0] * 6
    counts_guess = [0] * 6
    for v in secret:
        counts_secret[v] += 1
    for v in guess:
        counts_guess[v] += 1
    overlap = sum(min(counts_secret[c], counts_guess[c]) for c in range(6))
    white = overlap - black
    return black, white


def find_seed_with_distinct_secret(start: int = 42, limit: int = 10000) -> Tuple[int, List[int]]:
    """Find a seed whose derived secret has 4 distinct colours.

    Needed for tests that require a derangement with black=0 and white=4.
    """
    for s in range(start, start + limit):
        sec = derive_secret(s)
        if len(set(sec)) == 4:
            return s, sec
    # Fallback: return the start even if not distinct; tests will still fail red-first
    return start, derive_secret(start)
