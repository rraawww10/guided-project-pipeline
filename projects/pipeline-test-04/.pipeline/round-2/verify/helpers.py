"""Shared fixture data and screen helpers for the Tenpin suite.

The app is already running when this suite runs; its URL arrives in `BASE_URL`.
Nothing here starts a server, installs anything, picks a port or sleeps - every
wait is a retrying Playwright wait.

**There is no world to reset, and no `APP_DIR` lookup.** spec.md, Out of scope:
"Saving a scored game back to the store. Scoring is a pure read; nothing in this
project writes a file, so no test has to reset one and `data/games.json` ships as
a tracked seed." So no test mutates anything the app owns, nothing under
`APP_DIR` is read, and the tenth run in a working copy answers as the first -
which is what the nightly watchdog replays.

Every number and string below is a literal copied out of spec.md - the seed
table under "Data model", the derived-values table beside it, the roll-symbol
rule and the criteria themselves. No test asks the app what the answer is, and
no test re-derives an answer with the logic the app is being graded on: there is
no frame-splitting and no scoring arithmetic in this file, only the arrays
spec.md already worked out "so the Test Writer and the Builder agree".

Every page lookup goes through a `data-testid` the spec pins. spec.md, Screens:
"Elements, every one with a `data-testid` because class names are hashed and a
test must have a stable hook", and the table pins `frame-1`..`frame-10`,
`total-1`..`total-10`, `game-total` and `no-game`. `get_by_test_id` matches the
attribute exactly. The one prefix locator, `frame-`, is used only to enumerate
that family, and `frame-` is the prefix of no other testid in the spec
(`total-*`, `game-total` and `no-game` all fail it) - what it finds is then
compared as one whole ordered list, so an extra box fails as loudly as a missing
one.
"""
from __future__ import annotations

import os

from playwright.sync_api import Locator, Page

# A server-rendered page has to arrive before anything reads it. Passed
# explicitly everywhere so a missing element - which is what an open skeleton
# renders where a cut is still empty - fails on this suite's own budget rather
# than on Playwright's hidden 30s default.
LOAD_TIMEOUT = 20_000


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the seed, exactly as spec.md's "Data model" table pins it
# --------------------------------------------------------------------------
# spec.md, Endpoints, ep-games-list: "Returns a JSON array of four objects, one
# per seeded game, each { id, name, rolls, frames }, in the seed's order:
# g-gutter, g-perfect, g-mixed, g-partial."
SEED_IDS: list[str] = ["g-gutter", "g-perfect", "g-mixed", "g-partial"]
SEED_NAMES: list[str] = ["All Gutters", "Perfect Game", "Spare Heavy", "Stopped at Six"]

GUTTER_ROLLS: list[int] = [0] * 20
PERFECT_ROLLS: list[int] = [10] * 12
MIXED_ROLLS: list[int] = [1, 4, 4, 5, 6, 4, 5, 5, 10, 0, 1, 7, 3, 6, 4, 10, 2, 8, 6]
PARTIAL_ROLLS: list[int] = [3, 4, 7, 2, 9, 0, 8, 1, 10, 10]

SEED_ROLLS: dict[str, list[int]] = {
    "g-gutter": GUTTER_ROLLS,
    "g-perfect": PERFECT_ROLLS,
    "g-mixed": MIXED_ROLLS,
    "g-partial": PARTIAL_ROLLS,
}

# --------------------------------------------------------------------------
# the derived values, from spec.md's "Derived values" table
# --------------------------------------------------------------------------
# c-1-2 and c-1-3 pin these two arrays verbatim.
MIXED_FRAMES: list[list[int]] = [
    [1, 4], [4, 5], [6, 4], [5, 5], [10], [0, 1], [7, 3], [6, 4], [10], [2, 8, 6],
]
PARTIAL_FRAMES: list[list[int]] = [[3, 4], [7, 2], [9, 0], [8, 1], [10], [10]]

# c-2-1, c-2-2 and c-2-3 pin these three cumulative arrays verbatim. `None` is
# JSON `null` - spec.md's `FrameScore = number | null`, "null = the bonus rolls
# do not exist yet".
PERFECT_SCORES = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
MIXED_SCORES = [5, 14, 29, 49, 60, 61, 77, 97, 117, 133]
PARTIAL_SCORES = [7, 16, 25, 34, None, None]

# c-2-4's two totals, and c-2-5's empty game.
PARTIAL_TOTAL = 34
GUTTER_TOTAL = 0
EMPTY_TOTAL = 0

# --------------------------------------------------------------------------
# the strings the criteria pin on the page
# --------------------------------------------------------------------------
# spec.md, "Roll symbols": 10 is `X`, the second roll of a frame whose first two
# add to 10 is `/`, 0 is `-`, anything else is its digit; "a frame box holds its
# symbols joined by one space".
PERFECT_FRAME_10_TEXT = "X X X"            # [10,10,10] - c-1-4
MIXED_FRAME_TEXTS: dict[int, str] = {      # c-1-5
    1: "1 4",     # [1,4]
    3: "6 /",     # [6,4] - the pair adds to 10, so the second roll is a spare
    5: "X",       # [10]
    10: "2 / 6",  # [2,8,6] - 2+8 is 10, then the bonus roll
}
PERFECT_FRAME_IDS: list[str] = [f"frame-{n}" for n in range(1, 11)]  # c-1-4

UNKNOWN_GAME_ID = "no-such-game"                             # c-1-6
UNKNOWN_GAME_TEXT = f"No game with id {UNKNOWN_GAME_ID}"     # c-1-6

# c-2-6's score column on /games/g-partial. The four numbers are g-partial's
# cumulative scores from spec.md's derived-values table, rendered as decimal
# strings - spec.md, Screens: a score cell holds "the cumulative score as a
# decimal string, or nothing when that frame's score is `null`".
PARTIAL_SCORE_CELL_TEXTS: dict[int, str] = {1: "7", 2: "16", 3: "25", 4: "34"}
PARTIAL_TOTAL_TEXT = "34"                                    # c-2-6, in game-total
PARTIAL_EMPTY_CELLS: list[str] = ["total-5", "total-6"]      # c-2-6

# spec.md, Endpoints, ep-games-score: the one error body in the project.
ROLLS_ERROR = {"error": "rolls must be an array of numbers"}


# --------------------------------------------------------------------------
# ep-games-list
# --------------------------------------------------------------------------
def get_games(api) -> list[dict]:
    """GET /api/games, checked down to the array every session-1 criterion reads."""
    response = api.get("/api/games")
    assert response.status_code == 200, (
        f"GET /api/games answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, not a JSON array"
    for item in body:
        assert isinstance(item, dict), f"game is {item!r}, not a JSON object"
    return body


def one_game(games: list[dict], game_id: str) -> dict:
    """The single game carrying this id - found by id, never by array index."""
    found = [g for g in games if g.get("id") == game_id]
    assert len(found) == 1, (
        f"expected exactly 1 game with id {game_id!r}, found {len(found)}: {found}"
    )
    return found[0]


# --------------------------------------------------------------------------
# ep-games-score
# --------------------------------------------------------------------------
def post_score(api, rolls: list) -> dict:
    """POST /api/games/score with a legal body: 200 and both keys, or fail here."""
    response = api.post("/api/games/score", json={"rolls": rolls})
    assert response.status_code == 200, (
        f"POST /api/games/score with {len(rolls)} rolls answered "
        f"{response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, dict), f"body is {type(body).__name__}, not a JSON object"
    assert "frames" in body, f"body has no frames key: {body}"
    assert "total" in body, f"body has no total key: {body}"
    assert isinstance(body["frames"], list), (
        f"frames is {type(body['frames']).__name__}, not a JSON array"
    )
    return body


def post_raw(api, payload):
    """POST /api/games/score with whatever body a test wants to send."""
    return api.post("/api/games/score", json=payload)


# --------------------------------------------------------------------------
# sc-game
# --------------------------------------------------------------------------
def normalize(text) -> str:
    """Collapse every run of whitespace to one space and strip the ends.

    spec.md pins "the roll symbols of that frame inside the box, joined by one
    space". Which element each symbol sits in is the Builder's to decide, and
    markup between two spans is whitespace, so the comparison is on the
    collapsed text. `2 / 6` still fails against `2/6`, `2 - 6` or `X X`.
    """
    return " ".join((text or "").split())


def open_game(page: Page, game_id: str):
    """Open `/games/<id>` and hand back the main response.

    `sc-game` is a server component (spec.md, Screens), so the route's HTTP
    status is part of what c-1-6 reads - which is why this returns the response
    rather than swallowing it.
    """
    return page.goto(f"{base_url()}/games/{game_id}", wait_until="domcontentloaded")


def by_testid(page: Page, value: str) -> Locator:
    """One exact data-testid match - never a prefix match."""
    return page.get_by_test_id(value)


def frame_boxes(page: Page) -> Locator:
    """Every element whose data-testid starts with `frame-`, in document order."""
    return page.locator('[data-testid^="frame-"]')


def data_testids(locator: Locator) -> list:
    """The data-testid of each element the locator finds, in document order."""
    return [(el.get_attribute("data-testid") or "") for el in locator.all()]


def text_of(locator: Locator) -> str:
    """The element's collapsed text, waited for on this suite's own budget."""
    return normalize(locator.text_content(timeout=LOAD_TIMEOUT))
