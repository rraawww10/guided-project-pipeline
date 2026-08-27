"""Shared constants and waits for the recipe-box verification suite.

The app is already running; its URL arrives in BASE_URL. Nothing here starts a
server, and every wait is a retrying Playwright wait, never a sleep.

The store is read-only, so no test mutates it and no test depends on data left
behind by another: each one opens the screen or calls the endpoint it needs.
"""
from __future__ import annotations

import os
import re
from urllib.parse import parse_qsl, urlsplit

from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

BASE_URL = os.environ["BASE_URL"].rstrip("/")

# a screen has to load, fetch and render before anything can be read
LOAD_TIMEOUT = 20_000

# data/recipes.json, in the order the file stores it: the fields the criteria name
SEED_RECIPES = [
    {"id": "lemon-garlic-pasta", "title": "Lemon Garlic Pasta",
     "tags": ["quick", "vegetarian"], "minutes": 20, "serves": 4,
     "ingredients": 7, "steps": 4},
    {"id": "chickpea-curry", "title": "Chickpea Curry",
     "tags": ["one-pot", "spicy", "vegetarian"], "minutes": 35, "serves": 4,
     "ingredients": 9, "steps": 5},
    {"id": "banana-bread", "title": "Banana Bread",
     "tags": ["baking", "vegetarian"], "minutes": 60, "serves": 8,
     "ingredients": 8, "steps": 5},
    {"id": "chicken-noodle-soup", "title": "Chicken Noodle Soup",
     "tags": ["one-pot"], "minutes": 40, "serves": 6,
     "ingredients": 7, "steps": 5},
    {"id": "chilli-prawn-rice", "title": "Chilli Prawn Rice",
     "tags": ["one-pot", "quick", "spicy"], "minutes": 25, "serves": 3,
     "ingredients": 7, "steps": 5},
    {"id": "pesto-pasta-salad", "title": "Pesto Pasta Salad",
     "tags": ["quick", "vegetarian"], "minutes": 15, "serves": 6,
     "ingredients": 7, "steps": 4},
    {"id": "beef-stew", "title": "Beef Stew",
     "tags": ["one-pot"], "minutes": 90, "serves": 6,
     "ingredients": 8, "steps": 6},
    {"id": "garlic-flatbread", "title": "Garlic Flatbread",
     "tags": ["baking", "quick"], "minutes": 40, "serves": 4,
     "ingredients": 7, "steps": 5},
]

ALL_TAGS = ["baking", "one-pot", "quick", "spicy", "vegetarian"]

# lemon-garlic-pasta, the recipe most criteria name, exactly as it is stored
PASTA_STEPS = [
    "Boil the spaghetti in salted water until it still has a bite.",
    "Warm the oil in a wide pan with the sliced garlic and the chilli flakes.",
    "Toss the drained spaghetti through the oil with the lemon juice and the parsley.",
    "Taste, add the salt, and serve.",
]

# its 7 ingredients, in the order the store holds them
PASTA_ITEMS = [
    "spaghetti",
    "olive oil",
    "garlic",
    "chilli flakes",
    "lemon",
    "flat-leaf parsley",
    "salt",
]


def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends."""
    return " ".join((text or "").split())


# --------------------------------------------------------------------------
# sc-list
# --------------------------------------------------------------------------

def open_list(page: Page, query: str = "") -> None:
    """Open sc-list. Does not assume which state it settles in, so the empty
    state and the loaded state are both reachable from here."""
    page.goto(f"{BASE_URL}/{query}", wait_until="domcontentloaded")


def cards(page: Page) -> Locator:
    return page.get_by_test_id("recipe-card")


def card_titles(page: Page, expected: int) -> list[str]:
    """Wait for exactly `expected` recipe-card elements, then read their text."""
    found = cards(page)
    expect(found).to_have_count(expected, timeout=LOAD_TIMEOUT)
    return [normalize(text) for text in found.all_text_contents()]


def filter_chip(page: Page, tag: str) -> Locator:
    """The filter bar's chip for `tag` - filter-tag, never a card's card-tag."""
    return page.get_by_test_id("filter-tag").filter(has_text=exact_text(tag))


def exact_text(value: str) -> re.Pattern[str]:
    """A pattern that matches an element whose whole text reads `value`."""
    return re.compile(rf"^\s*{re.escape(value)}\s*$")


def wait_for_filter_bar(page: Page) -> None:
    """Wait until the tag chip bar has been filled by GET /api/tags.

    The bar is empty until that endpoint answers 200, so a test that clicks a
    chip has to wait for it. All five tags, always, whatever the list shows.
    """
    expect(page.get_by_test_id("filter-tag")).to_have_count(
        len(ALL_TAGS), timeout=LOAD_TIMEOUT
    )


def search_box(page: Page) -> Locator:
    return page.get_by_label("Search recipes")


def url_now(page: Page) -> str:
    """The address bar as path plus query, so /?q=x and / are told apart."""
    parts = urlsplit(page.url)
    return parts.path + (f"?{parts.query}" if parts.query else "")


def settle_url(page: Page, wanted: str) -> str:
    """Wait for the address bar to read `wanted`, then report what it reads.

    Returns rather than asserts, so the test's own assertion is the one that
    fails and prints the URL the page actually landed on.
    """
    try:
        page.wait_for_function(
            "(want) => window.location.pathname"
            " + (window.location.search || '') === want",
            arg=wanted,
            timeout=LOAD_TIMEOUT,
        )
    except PlaywrightTimeoutError:
        pass
    return url_now(page)


def settle_query(page: Page, wanted: dict[str, str]) -> dict[str, str]:
    """Wait until every parameter in `wanted` is set to that value in the
    address bar, then report the whole query as a dict.

    The key order depends on which control was used first, so this reads the
    parameters instead of comparing the joined string.
    """
    try:
        page.wait_for_function(
            "(want) => { const p = new URLSearchParams(window.location.search);"
            " return Object.keys(want).every((k) => p.get(k) === want[k]) }",
            arg=wanted,
            timeout=LOAD_TIMEOUT,
        )
    except PlaywrightTimeoutError:
        pass
    return dict(parse_qsl(urlsplit(page.url).query))


# --------------------------------------------------------------------------
# sc-recipe
# --------------------------------------------------------------------------

def open_recipe(page: Page, recipe_id: str) -> None:
    """Open sc-recipe without assuming which state it settles in."""
    page.goto(f"{BASE_URL}/recipes/{recipe_id}", wait_until="domcontentloaded")


def ingredient_rows(page: Page) -> Locator:
    return page.get_by_test_id("ingredient-row")


def row_texts(page: Page, expected: int) -> list[str]:
    """Wait for exactly `expected` ingredient-row elements, then read them."""
    rows = ingredient_rows(page)
    expect(rows).to_have_count(expected, timeout=LOAD_TIMEOUT)
    return [normalize(text) for text in rows.all_text_contents()]


def servings_count(page: Page) -> Locator:
    return page.get_by_test_id("servings-count")


def flush_render(page: Page) -> None:
    """Let the page paint twice, so a click that should change nothing has
    still been through React before the assertion reads the DOM."""
    page.evaluate(
        "() => new Promise((done) =>"
        " requestAnimationFrame(() => requestAnimationFrame(() => done(null))))"
    )


def step_servings(page: Page, label: str, counts: list[int]) -> None:
    """Click the stepper control named `label` once per entry of `counts`,
    waiting for servings-count to read each entry before the next click.

    The wait is synchronisation, not an extra assertion: it stops a later click
    from landing on a render that has not happened yet. A clamped click leaves
    the number where it was, so the caller repeats the value it expects to stay
    on and the double paint below covers the click that changes nothing.
    """
    button = page.get_by_role("button", name=label, exact=True)
    expect(button).to_be_enabled(timeout=LOAD_TIMEOUT)
    for value in counts:
        button.click()
        expect(servings_count(page)).to_have_text(str(value), timeout=LOAD_TIMEOUT)
    flush_render(page)
