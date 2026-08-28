"""Shared constants, store handling and waits for the habit-tracker suite.

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

The app owns one mutable file, `data/habits.json`, which it re-creates from
`data/habits.seed.json` whenever it is missing. That file lives inside the
directory the running app was started from - `app/` on the real run,
`skeleton/` on the skeleton run - which arrives as APP_DIR. A student running
pytest by hand stands in the app itself and has no APP_DIR, so the lookup falls
back to the working directory and never indexes the variable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Locator, Page

# a screen has to load, fetch and render before anything can be read
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the store the app writes to
# --------------------------------------------------------------------------
def app_dir() -> Path:
    """The directory the running app was started from."""
    return Path(os.environ.get("APP_DIR", os.getcwd()))


def store_path() -> Path:
    """The live store the app reads and writes on every request."""
    return app_dir() / "data" / "habits.json"


def seed_path() -> Path:
    """The immutable seed the app copies over the live store when it is absent."""
    return app_dir() / "data" / "habits.seed.json"


def reset_store() -> None:
    """Drop the live store, so the next request rebuilds it from the seed.

    Every test calls this before and after itself, so no test inherits another
    test's writes and the suite gives the same answer on its tenth run in the
    same working copy as on its first.
    """
    path = store_path()
    if path.exists():
        path.unlink()


def seed_store() -> dict:
    """The seed, parsed."""
    return json.loads(seed_path().read_text(encoding="utf-8"))


def write_store(store: dict) -> None:
    """Put a whole store on disk where the app reads it."""
    store_path().write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")


def write_store_with_tracked_day(tracked_day: str) -> None:
    """The seed's habits, with `trackedDay` moved to another date."""
    store = seed_store()
    store["trackedDay"] = tracked_day
    write_store(store)


# --------------------------------------------------------------------------
# what the seed means: trackedDay 2026-08-26, a Wednesday
# --------------------------------------------------------------------------
WEEK = [
    "2026-08-24",
    "2026-08-25",
    "2026-08-26",
    "2026-08-27",
    "2026-08-28",
    "2026-08-29",
    "2026-08-30",
]

# the week of 2026-09-06, a Sunday: Monday 2026-08-31 through that Sunday
WEEK_OF_SEPT_6 = [
    "2026-08-31",
    "2026-09-01",
    "2026-09-02",
    "2026-09-03",
    "2026-09-04",
    "2026-09-05",
    "2026-09-06",
]

HABIT_IDS = ["drink-water", "read-pages", "meditate", "stretch"]

# id -> name, as the seed stores it
NAMES = {
    "drink-water": "Drink water",
    "read-pages": "Read 10 pages",
    "meditate": "Meditate",
    "stretch": "Stretch",
}

# id -> streak on the seeded week
STREAKS = {"drink-water": 5, "read-pages": 0, "meditate": 0, "stretch": 1}

# id -> the dates of that week which the seed marks done
DONE = {
    "drink-water": ["2026-08-24", "2026-08-25", "2026-08-26"],
    "read-pages": ["2026-08-24", "2026-08-25"],
    "meditate": [],
    "stretch": ["2026-08-26"],
}


def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


def done_map(days: list[dict]) -> dict[str, bool]:
    """A days array as date -> done."""
    return {day["date"]: day["done"] for day in days}


# --------------------------------------------------------------------------
# the screens
# --------------------------------------------------------------------------
def open_board(page: Page) -> None:
    page.goto(f"{base_url()}/", wait_until="domcontentloaded")


def open_habit(page: Page, habit_id: str) -> None:
    page.goto(f"{base_url()}/habits/{habit_id}", wait_until="domcontentloaded")


def rows(page: Page) -> Locator:
    return page.get_by_test_id("habit-row")


def row(page: Page, habit_id: str) -> Locator:
    return page.locator(f'[data-testid="habit-row"][data-habit-id="{habit_id}"]')


def cells(scope: Page | Locator) -> Locator:
    return scope.get_by_test_id("day-cell")


def cell(scope: Page | Locator, date: str) -> Locator:
    return scope.locator(f'[data-testid="day-cell"][data-date="{date}"]')


def cell_dates(scope: Page | Locator) -> list[str]:
    return [c.get_attribute("data-date") or "" for c in cells(scope).all()]


def cell_done(scope: Page | Locator) -> dict[str, str]:
    """date -> the literal string in data-done, exactly as it is rendered."""
    return {
        (c.get_attribute("data-date") or ""): (c.get_attribute("data-done") or "")
        for c in cells(scope).all()
    }
