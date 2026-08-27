"""sc-list at /. One test per list-screen criterion, asserting only it."""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    SEED_RECIPES,
    card_titles,
    cards,
    filter_chip,
    normalize,
    open_list,
    search_box,
    settle_query,
    settle_url,
    wait_for_filter_bar,
)


def loaded_list(page) -> None:
    """Open / and wait for the 8 unfiltered cards.

    Synchronisation, not an extra assertion: the search box and the chips are
    inert until React has hydrated, and a card on screen is the proof that the
    effect which fetches the list has already run in the browser.
    """
    open_list(page)
    expect(cards(page)).to_have_count(8, timeout=LOAD_TIMEOUT)


def test_c_1_3_list_renders_one_card_per_seed_recipe(page):
    """c-1-3: sc-list renders one recipe-card element per recipe, 8 of them for
    the 8 seed recipes."""
    open_list(page)
    expect(cards(page)).to_have_count(8, timeout=LOAD_TIMEOUT)


def test_c_1_4_pasta_card_links_and_reads_its_title_minutes_and_serves(page):
    """c-1-4: the Lemon Garlic Pasta title sits inside a recipe-card linking to
    /recipes/lemon-garlic-pasta whose card-minutes reads 20 min and whose
    card-serves reads Serves 4."""
    open_list(page)
    card = page.locator('a[data-testid="recipe-card"][href="/recipes/lemon-garlic-pasta"]')
    expect(card).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(card).to_contain_text("Lemon Garlic Pasta")
    expect(card.get_by_test_id("card-minutes")).to_have_text("20 min")
    expect(card.get_by_test_id("card-serves")).to_have_text("Serves 4")


def test_c_1_5_every_card_carries_one_card_tag_per_tag(page):
    """c-1-5: one card-tag element per tag of that recipe on every card, 2 on
    the Lemon Garlic Pasta card reading quick and vegetarian."""
    open_list(page)
    expect(cards(page)).to_have_count(8, timeout=LOAD_TIMEOUT)

    for recipe in SEED_RECIPES:
        card = page.locator(
            f'a[data-testid="recipe-card"][href="/recipes/{recipe["id"]}"]'
        )
        expect(card).to_have_count(1, timeout=LOAD_TIMEOUT)
        chips = card.get_by_test_id("card-tag")
        expect(chips).to_have_count(len(recipe["tags"]), timeout=LOAD_TIMEOUT)
        on_card = [normalize(text) for text in chips.all_text_contents()]
        assert on_card == recipe["tags"], f"{recipe['id']} card reads {on_card}"

    pasta = page.locator('a[data-testid="recipe-card"][href="/recipes/lemon-garlic-pasta"]')
    pasta_tags = [normalize(t) for t in pasta.get_by_test_id("card-tag").all_text_contents()]
    assert pasta_tags == ["quick", "vegetarian"], pasta_tags


def test_c_2_4_typing_in_the_search_box_filters_the_list_and_the_url(page):
    """c-2-4: 2 cards and the URL /?q=garlic after garlic is typed, then the
    message No recipes match and 0 cards after the box is changed to zzz."""
    loaded_list(page)

    search_box(page).fill("garlic")
    assert settle_url(page, "/?q=garlic") == "/?q=garlic"
    expect(cards(page)).to_have_count(2, timeout=LOAD_TIMEOUT)

    search_box(page).fill("zzz")
    expect(page.get_by_text("No recipes match")).to_be_visible(timeout=LOAD_TIMEOUT)
    expect(cards(page)).to_have_count(0, timeout=LOAD_TIMEOUT)


def test_c_2_5_the_tag_chip_toggles_the_list_and_the_url(page):
    """c-2-5: 2 cards and the URL /?tag=baking after the baking filter-tag chip
    is clicked, then 8 cards and the URL / after the same chip is clicked again."""
    loaded_list(page)
    wait_for_filter_bar(page)
    chip = filter_chip(page, "baking")
    expect(chip).to_have_count(1, timeout=LOAD_TIMEOUT)

    chip.click()
    assert settle_url(page, "/?tag=baking") == "/?tag=baking"
    expect(cards(page)).to_have_count(2, timeout=LOAD_TIMEOUT)

    chip.click()
    assert settle_url(page, "/") == "/"
    expect(cards(page)).to_have_count(8, timeout=LOAD_TIMEOUT)


def test_c_2_6_the_chip_keeps_the_search_the_box_already_put_in_the_url(page):
    """c-2-6: 1 card reading Garlic Flatbread and a URL holding q=garlic and
    tag=baking, after garlic is typed, the URL reaches /?q=garlic, and the
    baking filter-tag chip is then clicked."""
    loaded_list(page)
    wait_for_filter_bar(page)

    search_box(page).fill("garlic")
    assert settle_url(page, "/?q=garlic") == "/?q=garlic"

    filter_chip(page, "baking").click()

    on_screen = card_titles(page, 1)
    assert on_screen[0].startswith("Garlic Flatbread"), f"the card reads {on_screen}"

    query = settle_query(page, {"q": "garlic", "tag": "baking"})
    assert query.get("q") == "garlic", f"the URL query reads {query!r}"
    assert query.get("tag") == "baking", f"the URL query reads {query!r}"
