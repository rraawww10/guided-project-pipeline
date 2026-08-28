"""Board data, locators and waits for the Sweeper suite.

Every number here is copied from spec.md, "The three boards", which fixes the
three seeded boards and their full `counts` arrays so nobody derives them twice.
Nothing here computes a count or a flood fill: a suite that recomputed the answer
would grade the app against a second implementation instead of against the spec.

Every element these locators read is pinned by spec.md, "Screens": the project
uses CSS Modules, class names are hashed, so the tests read `data-testid` and the
`data-*` attributes and never a class name or a styling detail.

The app is already running; its URL arrives in BASE_URL. The app writes nothing
to disk, so this module holds no path into the app's directory and never reads
APP_DIR - see conftest.py. Every wait below is a retrying Playwright wait, never
a sleep.
"""
from __future__ import annotations

import os

from playwright.sync_api import Locator, Page

# a screen has to load, fetch GET /api/boards/[id] and render before anything
# can be read
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the seeded boards - spec.md, "The three boards"
# --------------------------------------------------------------------------
INTRO_MINES = [9, 11, 18, 23]
FIELD_MINES = [15, 17, 20, 42, 44, 46, 47, 49, 56, 63]
CORNER_MINES = [11, 14, 15]

# intro, 5x5, in index order
INTRO_COUNTS = [
    0, 0, 0, 1, 1,
    1, 1, 1, 1, 0,
    1, 0, 2, 2, 2,
    1, 1, 3, 1, 2,
    0, 0, 2, 1, 2,
]

# corner, 4x4, in index order
CORNER_COUNTS = [
    0, 0, 0, 0,
    0, 0, 1, 1,
    0, 1, 3, 2,
    0, 1, 2, 2,
]

# field, 8x8: only the eight indices c-1-2 names, as index -> count
FIELD_COUNT_PICKS = {0: 0, 7: 1, 8: 1, 15: 0, 54: 3, 56: 1, 57: 2, 63: 0}

# the board index GET /api/boards answers, in seed order
BOARD_IDS = ["intro", "field", "corner"]
MINE_COUNTS = [4, 10, 3]

# --------------------------------------------------------------------------
# what one click opens - spec.md, the acceptance criteria of sessions 2 and 3
# --------------------------------------------------------------------------
FIELD_FROM_0 = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14]
INTRO_FROM_20 = [15, 16, 17, 20, 21, 22]
CORNER_FROM_0 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13]


def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


# --------------------------------------------------------------------------
# the screens
# --------------------------------------------------------------------------
def open_solved(page: Page, board_id: str) -> None:
    """sc-solved at /boards/[id]/solved."""
    page.goto(f"{base_url()}/boards/{board_id}/solved", wait_until="domcontentloaded")


def open_play(page: Page, board_id: str) -> None:
    """sc-play at /boards/[id]."""
    page.goto(f"{base_url()}/boards/{board_id}", wait_until="domcontentloaded")


def grid(page: Page) -> Locator:
    return page.get_by_test_id("board-grid")


def cells(page: Page) -> Locator:
    return page.get_by_test_id("cell")


def cell(page: Page, index: int) -> Locator:
    return page.locator(f'[data-testid="cell"][data-index="{index}"]')


def revealed_cells(page: Page) -> Locator:
    """Every cell on the page currently carrying data-revealed="true"."""
    return page.locator('[data-testid="cell"][data-revealed="true"]')


def flag_mode(page: Page) -> Locator:
    return page.get_by_test_id("flag-mode")


def mines_left(page: Page) -> Locator:
    return page.get_by_test_id("mines-left")


def game_status(page: Page) -> Locator:
    return page.get_by_test_id("game-status")


def board_missing(page: Page) -> Locator:
    return page.get_by_test_id("board-missing")


def attr_by_index(page: Page, name: str) -> dict[int, str]:
    """data-index -> the literal string in `name`, exactly as it is rendered."""
    return {
        int(c.get_attribute("data-index") or -1): (c.get_attribute(name) or "")
        for c in cells(page).all()
    }


def text_by_index(page: Page) -> dict[int, str]:
    """data-index -> the cell's visible text, whitespace-normalized."""
    return {
        int(c.get_attribute("data-index") or -1): normalize(c.text_content())
        for c in cells(page).all()
    }
