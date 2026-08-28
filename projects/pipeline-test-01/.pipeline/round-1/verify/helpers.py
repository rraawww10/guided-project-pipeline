"""Shared constants and readers for the Sweeper suite.

The app is already running; its URL arrives in `BASE_URL`. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**The app owns no file.** spec.md, "Data model": "Nothing is written to disk.
The boards are a `const` in `lib/boards.ts`, every endpoint is a pure function of
that constant plus its request, and both screens hold their own state in React."
So there is no store for a test to reset, the suite gives the same answer on its
first run and its hundredth, and `APP_DIR` is never needed. `app_dir()` below is
kept anyway, with the fallback the contract requires, so that a later change that
does give the app a file has one place to reach for and no test ever indexes
`os.environ["APP_DIR"]`.

Every hook a test reads is a `data-testid` or a `data-*` attribute the spec pins.
Class names are hashed by CSS Modules and nothing here reads one.
"""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import Locator, Page

# a screen has to load, fetch GET /api/boards/[id] and render before a test reads it
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


def app_dir() -> Path:
    """The directory the running app was started from - app/ or skeleton/.

    A student running pytest by hand stands in the app itself and has no
    APP_DIR, so this falls back to the working directory instead of raising.
    Unused today: this app writes nothing.
    """
    return Path(os.environ.get("APP_DIR", os.getcwd()))


# ---------------------------------------------------------------------------
# the three seeded boards - spec.md, "The three boards"
# ---------------------------------------------------------------------------
INTRO_MINES = [9, 11, 18, 23]
FIELD_MINES = [15, 17, 20, 42, 44, 46, 47, 49, 56, 63]
CORNER_MINES = [11, 14, 15]

# counts[i] is how many of the eight cells touching i are mines, including when
# i is itself a mine. Fixed in the spec so nobody derives them twice.
INTRO_COUNTS = [
    0, 0, 0, 1, 1,
    1, 1, 1, 1, 0,
    1, 0, 2, 2, 2,
    1, 1, 3, 1, 2,
    0, 0, 2, 1, 2,
]

CORNER_COUNTS = [
    0, 0, 0, 0,
    0, 0, 1, 1,
    0, 1, 3, 2,
    0, 1, 2, 2,
]

INTRO_CELLS = 25      # 5 x 5
FIELD_CELLS = 64      # 8 x 8
CORNER_CELLS = 16     # 4 x 4


def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


# ---------------------------------------------------------------------------
# the screens
# ---------------------------------------------------------------------------
def open_play(page: Page, board_id: str) -> None:
    """sc-play, route /boards/[id]."""
    page.goto(f"{base_url()}/boards/{board_id}", wait_until="domcontentloaded")


def open_solved(page: Page, board_id: str) -> None:
    """sc-solved, route /boards/[id]/solved."""
    page.goto(f"{base_url()}/boards/{board_id}/solved", wait_until="domcontentloaded")


def cells(page: Page) -> Locator:
    return page.get_by_test_id("cell")


def cell(page: Page, index: int) -> Locator:
    """The one cell carrying this data-index."""
    return page.locator(f'[data-testid="cell"][data-index="{index}"]')


def cells_with(page: Page, attr: str, value: str) -> Locator:
    """Every cell whose `attr` holds exactly `value` - e.g. data-revealed true."""
    return page.locator(f'[data-testid="cell"][{attr}="{value}"]')


def board_missing(page: Page) -> Locator:
    return page.get_by_test_id("board-missing")


def mines_left(page: Page) -> Locator:
    return page.get_by_test_id("mines-left")


def game_status(page: Page) -> Locator:
    return page.get_by_test_id("game-status")


def flag_mode(page: Page) -> Locator:
    return page.get_by_test_id("flag-mode")


# ---------------------------------------------------------------------------
# reading a whole grid in one round trip
#
# A 64-cell board would otherwise cost 128 get_attribute calls. Both readers run
# after a retrying to_have_count wait, so the DOM they read is already settled.
# ---------------------------------------------------------------------------
_ATTR_MAP_JS = """
(els, attr) => Object.fromEntries(
    els.map(e => [e.getAttribute('data-index'), e.getAttribute(attr)]))
"""

_TEXT_MAP_JS = r"""
els => Object.fromEntries(
    els.map(e => [e.getAttribute('data-index'),
                  (e.textContent || '').replace(/\s+/g, ' ').trim()]))
"""


def cell_attr_map(page: Page, attr: str) -> dict[str, str | None]:
    """data-index (as the string it is rendered as) -> that cell's `attr`."""
    return cells(page).evaluate_all(_ATTR_MAP_JS, attr)


def cell_text_map(page: Page) -> dict[str, str]:
    """data-index (as rendered) -> that cell's visible text, whitespace collapsed."""
    return cells(page).evaluate_all(_TEXT_MAP_JS)
