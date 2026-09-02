"""Shared fixture data and screen helpers for the Tenpin suite.

The app is already running; its URL arrives in `BASE_URL`. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**There is no world to reset, and nothing here reads `APP_DIR`.** spec.md, Out
of scope: "Scoring is a pure read; nothing in this project writes a file, so no
test has to reset one and `data/games.json` ships as a tracked seed." No test in
this suite writes a file the app owns and no test needs to locate one, so there
is no `os.environ["APP_DIR"]` anywhere - which is also the lookup that would
raise `KeyError` for a student running pytest by hand inside their skeleton. The
tenth run in a working copy answers as the first.

Every number and every string below is copied out of spec.json's criteria and
spec.md's Data model - the seed table, the derived frames/cumulative/total
table, the roll-symbol paragraph and the endpoint bodies. They are this suite's
own fixture data: **no test asks the app what the answer is, and no test
re-derives an answer with the logic the app is being graded on.** There is no
frame splitting, no lookahead and no addition anywhere in this file; the frame
lists and the cumulative arrays are literals.

Every lookup on a screen goes through a `data-testid` the spec pins. spec.md,
Screens: "Elements, every one with a `data-testid` because class names are
hashed and a test must have a stable hook." `get_by_test_id` matches the
attribute exactly, never as a prefix, and no class name and no styling is read
anywhere in this suite. The one prefix locator, `family`, is used only with
`frame-`, which is the prefix of no other testid in the spec's element table
(`frame-1..10`, `total-1..10`, `game-total`, `no-game`: `game-total` does not
begin with `total-`, and no score cell begins with `frame-`). What it finds is
compared as one ordered list, so an extra member fails as loudly as a missing
one.
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
# order." c-1-1 is the criterion that grades that order.
GAME_IDS: list[str] = ["g-gutter", "g-perfect", "g-mixed", "g-partial"]

GAME_NAMES: dict[str, str] = {
    "g-gutter": "All Gutters",
    "g-perfect": "Perfect Game",
    "g-mixed": "Spare Heavy",
    "g-partial": "Stopped at Six",
}

GUTTER_ROLLS: list[int] = [0] * 20                     # "twenty 0 rolls"
PERFECT_ROLLS: list[int] = [10] * 12                   # "twelve 10 rolls"
MIXED_ROLLS: list[int] = [1, 4, 4, 5, 6, 4, 5, 5, 10, 0, 1, 7, 3, 6, 4, 10, 2, 8, 6]
PARTIAL_ROLLS: list[int] = [3, 4, 7, 2, 9, 0, 8, 1, 10, 10]

GAME_ROLLS: dict[str, list[int]] = {
    "g-gutter": GUTTER_ROLLS,
    "g-perfect": PERFECT_ROLLS,
    "g-mixed": MIXED_ROLLS,
    "g-partial": PARTIAL_ROLLS,
}

# spec.json ep-games-list: "Array of { id: string, name: string,
# rolls: number[], frames: number[][] }", and c-1-1 words it "each carrying id,
# name, rolls and frames".
GAME_KEYS: tuple[str, ...] = ("id", "name", "rolls", "frames")

# --------------------------------------------------------------------------
# the derived values, from spec.md's table "worked out here so the Test Writer
# and the Builder agree"
# --------------------------------------------------------------------------
# 2 + 2 + 2 + 2 + 1 + 2 + 2 + 2 + 1 + 3 = the 19 rolls of g-mixed.
MIXED_FRAMES: list[list[int]] = [
    [1, 4], [4, 5], [6, 4], [5, 5], [10], [0, 1], [7, 3], [6, 4], [10], [2, 8, 6],
]
# Six frames, not five: g-partial closes on two strikes, each of which is a
# one-roll frame, and its rolls run out before a tenth frame exists. A naive
# pair-chunking scan pairs those two strikes and produces five, which is why
# spec.md calls this the scan's edge-case fixture.
PARTIAL_FRAMES: list[list[int]] = [[3, 4], [7, 2], [9, 0], [8, 1], [10], [10]]

PERFECT_SCORES: list[int] = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
MIXED_SCORES: list[int] = [5, 14, 29, 49, 60, 61, 77, 97, 117, 133]
# JSON null arrives as Python None, which is neither 0 nor "" nor "null" - the
# whole point of the project's FrameScore union.
PARTIAL_SCORES: list[object] = [7, 16, 25, 34, None, None]

PARTIAL_TOTAL = 34
GUTTER_TOTAL = 0
EMPTY_GAME_TOTAL = 0

# --------------------------------------------------------------------------
# the score column on the page, as decimal strings
# --------------------------------------------------------------------------
# spec.md, Screens: a score cell holds "the cumulative score as a decimal
# string, or no text at all when that frame's score is null"; game-total holds
# "gameTotal as a decimal string".
PARTIAL_TOTAL_TEXTS: dict[int, str] = {1: "7", 2: "16", 3: "25", 4: "34"}
PARTIAL_EMPTY_CELLS: list[int] = [5, 6]
PARTIAL_GAME_TOTAL_TEXT = "34"

# --------------------------------------------------------------------------
# roll symbols, from spec.md's lib/symbols.ts paragraph
# --------------------------------------------------------------------------
# "a roll of 10 is X; the second roll of a frame whose first two rolls add to 10
# is /; a roll of 0 is -; anything else is its digit. A frame box holds its
# symbols joined by one space, so [2,8,6] reads 2 / 6, [0,1] reads - 1 and [0,0]
# reads - -. The tenth frame of g-perfect is [10,10,10], whose first two rolls
# add to 20 rather than 10, so it reads X X X."
PERFECT_FRAME_10_TEXT = "X X X"
MIXED_FRAME_TEXTS: dict[int, str] = {
    1: "1 4",       # [1,4]     - two digits, an open frame
    3: "6 /",       # [6,4]     - the second roll of a spare
    5: "X",         # [10]      - a strike frame holds one roll
    6: "- 1",       # [0,1]     - the gutter glyph
    10: "2 / 6",    # [2,8,6]   - a spare and a bonus roll in one box
}

# the ten frame-box suffixes c-1-4 counts, in document order
FRAME_SUFFIXES_TEN: list[str] = [str(n) for n in range(1, 11)]

# --------------------------------------------------------------------------
# the endpoint bodies and the message
# --------------------------------------------------------------------------
# spec.md, ep-games-score: 400 with this exact body for a rolls that is absent
# or is not an array of numbers, and for a body that is absent, empty or
# unparseable alike.
ERROR_BODY: dict[str, str] = {"error": "rolls must be an array of numbers"}

# c-1-6 pins both the id in the URL and the id in the text, so they are one
# constant each and the interpolation is part of the assertion.
NO_GAME_ID = "no-such-game"
NO_GAME_TEXT = "No game with id no-such-game"


# --------------------------------------------------------------------------
# the endpoints
# --------------------------------------------------------------------------
def get_games(api) -> list[dict]:
    """GET /api/games, checked down to the array every session-1 criterion reads.

    The 200 and the array-of-objects shape live here rather than in three tests,
    so each criterion's own test asserts only what that criterion pins.
    """
    response = api.get("/api/games")
    assert response.status_code == 200, (
        f"GET /api/games answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, not a JSON array"
    for item in body:
        assert isinstance(item, dict), f"entry is {item!r}, not an object"
    return body


def one_game(games: list[dict], game_id: str) -> dict:
    """The single game carrying this id, found by id and never by index.

    c-1-2 and c-1-3 each read one named game, so this is the lookup they use: a
    duplicate or a miss fails here rather than silently reading a wrong object.
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


def number(value: object, what: str) -> object:
    """Require a real JSON number, then hand it back for comparison.

    spec.json's ep-games-score response declares `total: number`. Two of the
    totals this suite pins are 0, and in Python `0 == False`, so a JSON `false`
    would satisfy a bare equality. This closes that one hole; every other
    expected value in the suite is a non-zero number, a string or `None`.
    """
    assert isinstance(value, (int, float)) and not isinstance(value, bool), (
        f"{what} is {value!r} ({type(value).__name__}), not a JSON number"
    )
    return value


def score_ok(api, rolls: list[int]) -> dict:
    """POST a roll list, require the declared 200, hand back the parsed body.

    spec.md, ep-games-score: "`rolls` is an array of numbers: 200 with
    `{ "frames": FrameScore[], "total": number }`". The status and the two keys
    are asserted here; what is in them is each criterion's own test.
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

    Applied to a box or a cell that is supposed to hold text, because the markup
    the Builder wraps "joined by one space" in is its own to choose. It is
    deliberately NOT applied to a pending score cell: spec.md requires that
    cell's `textContent` to be the empty string and rules out `&nbsp;`
    explicitly, and a non-breaking space collapses to "" here. Those cells are
    read with `raw_text_of`.
    """
    return " ".join((text or "").split())


def open_game(page: Page, game_id: str):
    """Open `/games/<id>` - sc-game.

    A server component: spec.md says it "reads the seed through `lib/store.ts`
    directly rather than fetching `/api/games`" and that session 2's column
    "calls `scoreGame` and `gameTotal` from `lib/score.ts` in process and never
    fetches `/api/games/score`". So nothing here waits on a client fetch.
    """
    return page.goto(f"{base_url()}/games/{game_id}", wait_until="domcontentloaded")


def by_testid(page: Page, value: str) -> Locator:
    """One exact data-testid match - never a prefix match."""
    return page.get_by_test_id(value)


def family(page: Page, prefix: str) -> Locator:
    """Every element whose data-testid starts with `prefix`.

    Used only with `frame-`, which is the prefix of no other data-testid in
    spec.md's element table. What it finds is compared as one ordered list.
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
    frame whose score is `null` contains **no text**: its `textContent` is the
    empty string. It is not a placeholder character, not `&nbsp;`, not an em
    dash and not the `-` gutter glyph." Collapsing whitespace here would let a
    non-breaking space through, so it is not collapsed.
    """
    return locator.text_content(timeout=LOAD_TIMEOUT) or ""
