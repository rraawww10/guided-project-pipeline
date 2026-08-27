"""sc-recipe's servings stepper and the quantities it scales.

One test per session-4 criterion, asserting only it.
"""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    exact_text,
    ingredient_rows,
    open_recipe,
    row_texts,
    servings_count,
    step_servings,
)

MORE = "More servings"
FEWER = "Fewer servings"


def open_pasta(page) -> None:
    """Open /recipes/lemon-garlic-pasta and wait for its loaded state.

    Synchronisation: the stepper is inert until the recipe has arrived and the
    view has mounted, and the count starts on the stored serves of 4.
    """
    open_recipe(page, "lemon-garlic-pasta")
    expect(servings_count(page)).to_have_text("4", timeout=LOAD_TIMEOUT)


def assert_row_reads(page, text: str) -> None:
    """One ingredient-row whose whole text reads `text`, waited for, not slept for."""
    matching = ingredient_rows(page).filter(has_text=exact_text(text))
    try:
        expect(matching).to_have_count(1, timeout=LOAD_TIMEOUT)
    except AssertionError:
        raise AssertionError(
            f"no ingredient-row reading {text!r}; the rows read {row_texts(page, 7)}"
        ) from None


def test_c_4_1_two_plus_clicks_take_the_count_from_four_to_six(page):
    """c-4-1: servings-count reads 6 after the plus control is clicked 2 times
    at /recipes/lemon-garlic-pasta, which is stored as serves 4."""
    open_pasta(page)
    step_servings(page, MORE, [5, 6])
    expect(servings_count(page)).to_have_text("6", timeout=LOAD_TIMEOUT)


def test_c_4_2_whole_quantity_scales_from_four_to_six_servings(page):
    """c-4-2: an ingredient-row reads 3 tbsp olive oil after 2 plus clicks take
    the count from the stored 4 to 6, where the stored quantity is 2 tbsp."""
    open_pasta(page)
    assert_row_reads(page, "2 tbsp olive oil")
    step_servings(page, MORE, [5, 6])
    assert_row_reads(page, "3 tbsp olive oil")


def test_c_4_3_fraction_scales_and_reduces_from_four_to_six_servings(page):
    """c-4-3: an ingredient-row reads 1/2 tsp chilli flakes after 2 plus clicks
    take the count from the stored 4 to 6, where the stored quantity is 1/3 tsp."""
    open_pasta(page)
    assert_row_reads(page, "1/3 tsp chilli flakes")
    step_servings(page, MORE, [5, 6])
    assert_row_reads(page, "1/2 tsp chilli flakes")


def test_c_4_4_up_then_down_lands_back_on_the_stored_quantity(page):
    """c-4-4: an ingredient-row reads 1/2 tsp chilli flakes after 2 plus clicks,
    then 1/3 tsp chilli flakes again after 2 minus clicks."""
    open_pasta(page)
    step_servings(page, MORE, [5, 6])
    assert_row_reads(page, "1/2 tsp chilli flakes")
    step_servings(page, FEWER, [5, 4])
    assert_row_reads(page, "1/3 tsp chilli flakes")


def test_c_4_5_lower_clamp_holds_the_count_at_one(page):
    """c-4-5: servings-count reads 1 after the minus control is clicked 4 times
    at /recipes/lemon-garlic-pasta, which is stored as serves 4."""
    open_pasta(page)
    # 4 -> 3, 2, 1 and then a fourth click that asks for 0
    step_servings(page, FEWER, [3, 2, 1, 1])
    expect(servings_count(page)).to_have_text("1", timeout=LOAD_TIMEOUT)


def test_c_4_6_upper_clamp_holds_the_count_at_twenty_four(page):
    """c-4-6: servings-count reads 24 after the plus control is clicked 21 times
    at /recipes/lemon-garlic-pasta, which is stored as serves 4."""
    open_pasta(page)
    # 4 up to 24 in 20 clicks and then a twenty-first click that asks for 25
    step_servings(page, MORE, [*range(5, 25), 24])
    expect(servings_count(page)).to_have_text("24", timeout=LOAD_TIMEOUT)
