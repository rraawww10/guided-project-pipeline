"""Shared fixture data and screen helpers for the Tenpin suite.

The app is already running; its URL arrives in `BASE_URL`. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**There is no world to reset.** spec.md, Out of scope: "Scoring is a pure read;
nothing in this project writes a file, so no test has to reset one and
`data/games.json` ships as a tracked seed." So no test writes a file the app
owns, and nothing here reads `APP_DIR` - there is nothing under it this suite
needs. The tenth run in a working copy answers as the first.

Every number and every string below is copied out of spec.md's Data model - the
seed table, the derived frames/cumulative/total table, the roll-symbol rules and
the endpoint bodies. They are this suite's own fixture data: no test asks the app
what the answer is, and no test re-derives an answer with the logic the app is
being graded on (there is no frame splitting and no scoring in this file).

Every lookup on a screen goes through a `data-testid` the spec pins. spec.md,
Screens: "Elements, every one with a `data-testid` because class names are
hashed and a test must have a stable hook." `get_by_test_id` matches the
attribute exactly, never as a prefix. The one prefix locator, `family`, is used
only with `frame-`, which is the prefix of no other testid in the spec's element
table (`frame-1..10`, `total-1..10`, `game-total`, `no-game` - `game-total` does
not begin with `total-`, and no score cell begins with `frame-`), and what it
finds is compared as one ordered list so an extra member fails too.
"""
from __future__ import annotations

import os

from playwright.sync_api import Locator, Page

# a server component has to render before anything reads it
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the seed, exactly as spec.md's Data model table pins it
# --------------------------------------------------------------------------
# "data/games.json holds exactly these four games, shipped written, in this
# order." c-1-1 is what grades that order.
GAME_IDS: list[str] = ["g-gutter", "g-perfect", "g-mixed", "g-partial"]

GAME_NAMES: dict[str, str] = {
    "g-gutter": "All Gutters",
    "g-perfect": "Perfect Game",
    "g-mixed": "Spare Heavy",
    "g-partial": "Stopped at Six",
}

GUTTER_ROLLS: list[int] = [0] * 20                     # twenty 0 rolls
PERFECT_ROLLS: list[int] = [10] * 12                   # twelve 10 rolls
MIXED_ROLLS: list[int] = [1, 4, 4, 5, 6, 4, 5, 5, 10, 0, 1, 7, 3, 6, 4, 10, 2, 8, 6]
PARTIAL_ROLLS: list[int] = [3, 4, 7, 2, 9, 0, 8, 1, 10, 10]

GAME_ROLLS: dict[str, list[int]] = {
    "g-gutter": GUTTER_ROLLS,
    "g-perfect": PERFECT_ROLLS,
    "g-mixed": MIXED_ROLLS,
    "g-partial": PARTIAL_ROLLS,
}

GAME_KEYS: tuple[str, ...] = ("id", "name", "rolls", "frames")

# --------------------------------------------------------------------------
# the derived values, from spec.md's table "worked out here so the Test Writer
# and the Builder agree"
# --------------------------------------------------------------------------
MIXED_FRAMES: list[list[int]] = [
    [1, 4], [4, 5], [6, 4], [5, 5], [10], [0, 1], [7, 3], [6, 4], [10], [2, 8, 6],
]
# Six frames, not five: g-partial's rolls run out before a tenth frame, and a
# naive pair-chunking scan produces five. This is the scan's edge-case fixture.
PARTIAL_FRAMES: list[list[int]] = [[3, 4], [7, 2], [9, 0], [8, 1], [10], [10]]

PERFECT_SCORES: list[int] = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
MIXED_SCORES: list[int] = [5, 14, 29, 49, 60, 61, 77, 97, 117, 133]
# JSON null arrives as Python None, which is neither 0 nor "" - the whole point
# of the project's FrameScore union.
PARTIAL_SCORES: list[object] = [7, 16, 25, 34, None, None]

PARTIAL_TOTAL = 34
GUTTER_TOTAL = 0
EMPTY_GAME_TOTAL = 0

# --------------------------------------------------------------------------
# the score column on the page, as decimal strings
# --------------------------------------------------------------------------
# spec.md, Screens: a score cell holds "the cumulative score as a decimal
# string, or no text at all when that frame's score is null", and the game total
# holds "gameTotal as a decimal string".
PARTIAL_TOTAL_TEXTS: dict[int, str] = {1: "7", 2: "16", 3: "25", 4: "34"}
PARTIAL_EMPTY_CELLS: list[int] = [5, 6]
PARTIAL_GAME_TOTAL_TEXT = "34"

# --------------------------------------------------------------------------
# roll symbols, from spec.md's lib/symbols.ts paragraph
# --------------------------------------------------------------------------
# "A frame box holds its symbols joined by one space, so [2,8,6] reads 2 / 6,
# [0,1] reads - 1 and [0,0] reads - -. The tenth frame of g-perfect is
# [10,10,10], whose first two rolls add to 20 rather than 10, so it reads X X X."
PERFECT_FRAME_10_TEXT = "X X X"
MIXED_FRAME_TEXTS: dict[int, str] = {
    1: "1 4",
    3: "6 /",
    5: "X",
    6: "- 1",
    10: "2 / 6",
}

# the ten frame-box suffixes c-1-4 counts, in document order
FRAME_SUFFIXES_TEN: list[str] = [str(n) for n in range(1, 11)]

# --------------------------------------------------------------------------
# the endpoint bodies
# --------------------------------------------------------------------------
# spec.md, ep-games-score: 400 with the error body below, for an absent or
# non-numeric-array rolls and for a body that is absent, empty or unparseable
# alike.
ERROR_BODY: dict[str, str] = {"error": "rolls must be an array of numbers"}

NO_GAME_ID = "no-such-game"
NO_GAME_TEXT = "No game with id no-such-game"


# --------------------------------------------------------------------------
# the endpoints
# --------------------------------------------------------------------------
def get_games(api) -> list[object]:
    """GET /api/games, checked down to the array every session-1 criterion reads."""
    response = api.get("/api/games")
    assert response.status_code == 200, (
        f"GET /api/games answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, not a JSON array"
    for item in body:
        assert isinstance(item, dict), f"entry is {item!r}, not an object"
    return body


def one_game(games: list[object], game_id: str) -> dict:
    """The single game carrying this id, found by id and never by index.

    c-1-2 and c-1-3 each read one named game, so this is the lookup they use; a
    duplicate or a miss fails here rather than reading a wrong object.
    """
    found = [g for g in games if g.get("id") == game_id]
    assert len(found) == 1, (
        f"expected exactly 1 game with id {game_id!r}, found {len(found)}: {found}"
    )
    return found[0]


def post_score(api, **kwargs):
    """POST /api/games/score, raw - the caller reads the status the route chose.

    Used directly by c-2-5, which grades a 400. The keyword arguments go
    straight to httpx, so a test may send `json=` or a raw `content=` body.
    """
    return api.post("/api/games/score", **kwargs)


def score_ok(api, rolls: list[int]) -> dict:
    """POST a roll list, require the declared 200, hand back the parsed body.

    spec.md, ep-games-score: rolls is an array of numbers -> 200 with
    {frames: FrameScore[], total: number}.
    """
    response = post_score(api, json={"rolls": rolls})
    assert response.status_code == 200, (
        f"POST /api/games/score answered {response.status_code} for "
        f"{len(rolls)} rolls: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, dict), f"body is {type(body).__name__}, not a JSON object"
    assert "frames" in body, f"body has no frames key: {body}"
    assert isinstance(body["frames"], list), (
        f"frames is {type(body['frames']).__name__}, not a JSON array"
    )
    assert "total" in body, f"body has no total key: {body}"
    return body


# --------------------------------------------------------------------------
# the screens
# --------------------------------------------------------------------------
def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends.

    Applied to a box or cell that is supposed to hold text, because the markup
    around "joined by one space" is the Builder's to choose. It is deliberately
    NOT applied to the pending score cells: spec.md requires their textContent
    to be the empty string and rules out a non-breaking space explicitly, which
    would collapse to "" here. Those cells are read with `raw_text_of`.
    """
    return " ".join((text or "").split())


def open_game(page: Page, game_id: str):
    """Open `/games/<id>` - sc-game, a server component that reads the seed
    through lib/store.ts and never fetches its own routes."""
    return page.goto(f"{base_url()}/games/{game_id}", wait_until="domcontentloaded")


def by_testid(page: Page, value: str) -> Locator:
    """One exact data-testid match - never a prefix match."""
    return page.get_by_test_id(value)


def family(page: Page, prefix: str) -> Locator:
    """Every element whose data-testid starts with `prefix`.

    Used only with `frame-`, which is the prefix of no other data-testid in
    spec.md's element table. What it finds is compared as one ordered list, so
    an extra member fails as loudly as a missing one.
    """
    return page.locator(f'[data-testid^="{prefix}"]')


def suffixes(locator: Locator, prefix: str) -> list[str]:
    """The tail of each data-testid the locator finds, in document order."""
    return [
        (el.get_attribute("data-testid") or "")[len(prefix):]
        for el in locator.all()
    ]


def text_of(locator: Locator) -> str:
    """The element's text, whitespace-collapsed, waited for with LOAD_TIMEOUT.

    `text_content()` retries until the element exists. The timeout is passed
    explicitly so a missing element - which is what an open `cut-frames-scan`
    leaves behind - fails on this suite's own 20s budget rather than on
    Playwright's hidden 30s default.
    """
    return normalize(locator.text_content(timeout=LOAD_TIMEOUT))


def raw_text_of(locator: Locator) -> str:
    """The element's textContent exactly as the DOM holds it, uncollapsed.

    For the pending score cells only. spec.md, Screens: "A score cell for a
    frame whose score is null contains **no text**: its textContent is the empty
    string. It is not a placeholder character, not &nbsp;, not an em dash and not
    the - gutter glyph." Collapsing whitespace here would let a non-breaking
    space through, so it is not collapsed.
    """
    return locator.text_content(timeout=LOAD_TIMEOUT) or ""
