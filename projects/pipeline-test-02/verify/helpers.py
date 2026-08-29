"""Shared constants, grid builders and screen helpers for the Clue suite.

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**There is no world to reset.** spec.md, Data model: "There is no `data/`
directory and no runtime store: nothing in this project writes a file ... Every
test may run in any order, any number of times, and get the same answer." So no
test touches a file the app owns and nothing here reads APP_DIR - there is
nothing under it to read. A reload starts every board empty again and each test
gets its own browser context, so the tenth run in a working copy answers as the
first, which is what the nightly watchdog replays.

The seed strings and the clue tables below are copied from spec.md (the seed
block and the "Derived, never stored" table). They are this suite's own fixture
data: every request grid and every expected clue string is built from them, and
the suite never asks the app what the answer is.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from playwright.sync_api import Locator, Page

# a screen has to load, fetch and render before anything can be read
LOAD_TIMEOUT = 20_000
# one POST /check has to be sent and answered before a strip repaints
CHECK_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the seed, as spec.md prints it: '#' is a filled cell, '.' is a blank one
# --------------------------------------------------------------------------
SOLUTIONS: dict[str, list[str]] = {
    "boat": [
        "..#..",
        ".###.",
        "#####",
        ".#.#.",
        ".#.#.",
    ],
    "blanks": [
        ".....",
        "#####",
        "#...#",
        ".###.",
        "#.#.#",
    ],
    "house": [
        "...##...",
        "..####..",
        ".######.",
        "########",
        ".#....#.",
        ".#.##.#.",
        ".#.##.#.",
        ".#....#.",
    ],
}

# the ids in seed order, which is the order ep-puzzles-list answers in
SEED_ORDER = ["boat", "blanks", "house"]
TITLES = {"boat": "Boat", "blanks": "Blanks", "house": "House"}
SIZES = {"boat": 5, "blanks": 5, "house": 8}

# The clue tables printed in spec.md, "Derived, never stored". They are the
# derivation evaluated against the seed above, not a second definition - the
# tests pin them as literals because the criteria pin them as literals.
ROW_CLUES: dict[str, list[list[int]]] = {
    "boat": [[1], [3], [5], [1, 1], [1, 1]],
    "blanks": [[0], [5], [1, 1], [3], [1, 1, 1]],
    "house": [[2], [4], [6], [8], [1, 1], [1, 2, 1], [1, 2, 1], [1, 1]],
}
COL_CLUES: dict[str, list[list[int]]] = {
    "boat": [[1], [4], [3], [4], [1]],
    "blanks": [[2, 1], [1, 1], [1, 2], [1, 1], [2, 1]],
    "house": [[1], [6], [3], [4, 2], [4, 2], [3], [6], [1]],
}

# c-2-6 enumerates its own 13 cells: "the 5 cells of row 1, columns 0 and 4 of
# row 2, columns 1, 2 and 3 of row 3, and columns 0, 2 and 4 of row 4, leaving
# row 0 untouched". Row 0 is the top and column 0 the left (spec.md, Screens,
# the cell bullet - ambiguity.md W6 notes spec.json drops that half-sentence).
BLANKS_FILLED: list[tuple[int, int]] = [
    (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    (2, 0), (2, 4),
    (3, 1), (3, 2), (3, 3),
    (4, 0), (4, 2), (4, 4),
]


# --------------------------------------------------------------------------
# grids, as the check endpoint takes them
# --------------------------------------------------------------------------
EMPTY, FILLED, CROSSED = "empty", "filled", "crossed"


def solution_grid(puzzle_id: str) -> list[list[str]]:
    """The seeded solution as Cell[][] - '#' reads filled, '.' reads empty."""
    return [
        [FILLED if ch == "#" else EMPTY for ch in row]
        for row in SOLUTIONS[puzzle_id]
    ]


def empty_grid(size: int) -> list[list[str]]:
    """A size by size grid of `empty` cells."""
    return [[EMPTY] * size for _ in range(size)]


def filled_coords(puzzle_id: str) -> list[tuple[int, int]]:
    """Every (row, column) the seeded solution fills, in reading order."""
    return [
        (r, c)
        for r, row in enumerate(SOLUTIONS[puzzle_id])
        for c, ch in enumerate(row)
        if ch == "#"
    ]


# c-2-6's enumeration IS the filled set of the blanks seed; if the two ever
# disagree the suite says so at import time rather than driving a wrong board.
assert BLANKS_FILLED == filled_coords("blanks"), (
    "the c-2-6 cell list and the blanks seed disagree"
)


def clue_text(clue: list[int]) -> str:
    """A clue as a strip renders it: the numbers joined by one space."""
    return " ".join(str(n) for n in clue)


def check(api, puzzle_id: str, grid):
    """POST /api/puzzles/<id>/check carrying a whole grid."""
    return api.post(f"/api/puzzles/{puzzle_id}/check", json={"grid": grid})


# --------------------------------------------------------------------------
# the screen - every lookup goes through a data-testid the spec pins, because
# CSS Modules hash the class names and nothing here may read styling
# --------------------------------------------------------------------------
def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


def open_puzzle(page: Page, puzzle_id: str) -> None:
    page.goto(f"{base_url()}/puzzles/{puzzle_id}", wait_until="domcontentloaded")


def cell(page: Page, r: int, c: int) -> Locator:
    return page.get_by_test_id(f"cell-{r}-{c}")


def all_cells(page: Page) -> Locator:
    return page.locator('[data-testid^="cell-"]')


def row_clue(page: Page, r: int) -> Locator:
    return page.get_by_test_id(f"row-clue-{r}")


def col_clue(page: Page, c: int) -> Locator:
    return page.get_by_test_id(f"col-clue-{c}")


def all_row_clues(page: Page) -> Locator:
    return page.locator('[data-testid^="row-clue-"]')


def all_col_clues(page: Page) -> Locator:
    return page.locator('[data-testid^="col-clue-"]')


def solved_banner(page: Page) -> Locator:
    return page.get_by_test_id("solved-banner")


def puzzle_title(page: Page) -> Locator:
    return page.get_by_test_id("puzzle-title")


def puzzle_missing(page: Page) -> Locator:
    return page.get_by_test_id("puzzle-missing")


def attr_map(locator: Locator, attribute: str) -> dict[str, str]:
    """data-testid -> the named attribute, for every element the locator finds.

    Comparing the whole map in one assert grades the id set and the attribute
    together, so a missing element fails instead of being quietly skipped.
    """
    return {
        (el.get_attribute("data-testid") or ""): (el.get_attribute(attribute) or "")
        for el in locator.all()
    }


def text_map(locator: Locator) -> dict[str, str]:
    """data-testid -> normalized text, for every element the locator finds."""
    return {
        (el.get_attribute("data-testid") or ""): normalize(el.text_content())
        for el in locator.all()
    }


def text_of(locator: Locator) -> str:
    return normalize(locator.text_content())


def check_path(puzzle_id: str) -> str:
    return f"/api/puzzles/{puzzle_id}/check"


def is_check_response(response, puzzle_id: str) -> bool:
    """True for a response to this puzzle's check endpoint, whatever the query."""
    return urlsplit(response.url).path == check_path(puzzle_id)
