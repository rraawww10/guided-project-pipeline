"""Shared constants, grid builders and screen helpers for the Clue suite.

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**There is no world to reset.** spec.md, Data model: "There is no `data/`
directory and no runtime store: nothing in this project writes a file ... Every
test may run in any order, any number of times, and get the same answer." So
this suite touches no file the app owns and never reads APP_DIR - there is
nothing under it to read. A reload starts every board empty again, and every
test opens its own browser context, so the tenth run in a working copy answers
exactly as the first.

The three solutions below are copied from spec.md's seed block. They are the
test's own fixture data: the suite builds request grids and expected clue
strings from them, and never asks the app what the answer is.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from playwright.sync_api import Locator, Page

# a screen has to load, fetch and render before anything can be read
LOAD_TIMEOUT = 20_000
# one POST /check has to be sent and answered
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

SEED_ORDER = ["boat", "blanks", "house"]

# The clue tables printed in spec.md, "Derived, never stored". They are the
# derivation evaluated against the seed above, not a second definition - the
# tests pin them as literals because the criteria do.
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


# --------------------------------------------------------------------------
# grids, as the check endpoint takes them
# --------------------------------------------------------------------------
def solution_grid(puzzle_id: str) -> list[list[str]]:
    """The seeded solution as Cell[][] - '#' is filled, anything else empty."""
    return [
        ["filled" if ch == "#" else "empty" for ch in row]
        for row in SOLUTIONS[puzzle_id]
    ]


def empty_grid(size: int) -> list[list[str]]:
    """A size by size grid of `empty` cells."""
    return [["empty"] * size for _ in range(size)]


def filled_coords(puzzle_id: str) -> list[tuple[int, int]]:
    """Every (row, col) the seeded solution fills, in reading order."""
    return [
        (r, c)
        for r, row in enumerate(SOLUTIONS[puzzle_id])
        for c, ch in enumerate(row)
        if ch == "#"
    ]


def clue_text(clue: list[int]) -> str:
    """A clue as the strip renders it: the numbers joined by one space."""
    return " ".join(str(n) for n in clue)


def check(api, puzzle_id: str, grid: list[list[str]]):
    """POST /api/puzzles/<id>/check with a whole grid."""
    return api.post(f"/api/puzzles/{puzzle_id}/check", json={"grid": grid})


# --------------------------------------------------------------------------
# the screen
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


def text_of(locator: Locator) -> str:
    return normalize(locator.text_content())


def check_path(puzzle_id: str) -> str:
    return f"/api/puzzles/{puzzle_id}/check"


def is_check_response(response, puzzle_id: str) -> bool:
    return urlsplit(response.url).path == check_path(puzzle_id)
