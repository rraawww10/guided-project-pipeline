"""sc-recipe at /recipes/[id]: its loaded state and its not-found state.

One test per criterion, asserting only it.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    PASTA_ITEMS,
    PASTA_STEPS,
    normalize,
    open_recipe,
    row_texts,
)


def test_c_3_3_pasta_renders_one_ingredient_row_per_ingredient(page):
    """c-3-3: 7 ingredient-row elements at /recipes/lemon-garlic-pasta, the
    olive oil row reading 2 tbsp olive oil and the lemon row reading 1 lemon."""
    open_recipe(page, "lemon-garlic-pasta")
    rows = row_texts(page, 7)
    for text, item in zip(rows, PASTA_ITEMS):
        assert item in text, f"the row for {item} reads {text!r}; all 7 read {rows}"
    assert "2 tbsp olive oil" in rows, f"no row reading 2 tbsp olive oil in {rows}"
    assert "1 lemon" in rows, f"no row reading 1 lemon in {rows}"


def test_c_3_4_pasta_renders_four_numbered_steps_in_stored_order(page):
    """c-3-4: 4 step elements in stored order at /recipes/lemon-garlic-pasta,
    the text of the first beginning 1. Boil the spaghetti."""
    open_recipe(page, "lemon-garlic-pasta")
    steps = page.get_by_test_id("step")
    expect(steps).to_have_count(4, timeout=LOAD_TIMEOUT)
    on_screen = [normalize(text) for text in steps.all_text_contents()]
    assert on_screen == [
        f"{index + 1}. {step}" for index, step in enumerate(PASTA_STEPS)
    ], f"the steps read {on_screen}"
    assert on_screen[0].startswith("1. Boil the spaghetti"), on_screen[0]


def test_c_3_5_an_unknown_id_shows_the_not_found_message(page):
    """c-3-5: sc-recipe displays the message Recipe not found at the route
    /recipes/not-a-recipe."""
    open_recipe(page, "not-a-recipe")
    expect(page.get_by_text("Recipe not found")).to_be_visible(timeout=LOAD_TIMEOUT)
