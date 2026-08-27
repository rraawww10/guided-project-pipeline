"""sc-list at /. One test per session-1 screen criterion."""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import LOAD_TIMEOUT, SEED_BILLS, normalize, open_list


def test_c_1_3_list_renders_one_card_per_seed_bill(page):
    """c-1-3: sc-list renders 6 bill-card elements for the 6 seed bills."""
    open_list(page)
    expect(page.get_by_test_id("bill-card")).to_have_count(6, timeout=LOAD_TIMEOUT)


def test_c_1_4_anand_bhavan_card_links_and_reads_its_fields(page):
    """c-1-4: the anand-bhavan card is a link to /bills/anand-bhavan holding
    card-place Anand Bhavan, card-date 2026-03-14, card-total the rupee total
    and card-people Split 4 ways."""
    open_list(page)
    card = page.locator('a[data-testid="bill-card"][href="/bills/anand-bhavan"]')
    expect(card).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(card.get_by_test_id("card-place")).to_have_text("Anand Bhavan")
    expect(card.get_by_test_id("card-date")).to_have_text("2026-03-14")
    expect(card.get_by_test_id("card-total")).to_have_text("₹1240.00")
    expect(card.get_by_test_id("card-people")).to_have_text("Split 4 ways")


def test_c_1_5_cards_are_in_the_order_the_endpoint_returns(page):
    """c-1-5: the 6 cards sit in store order, first Anand Bhavan, last Kurry Kulture."""
    open_list(page)
    places = page.get_by_test_id("bill-card").get_by_test_id("card-place")
    expect(places).to_have_count(6, timeout=LOAD_TIMEOUT)
    on_screen = [normalize(text) for text in places.all_text_contents()]
    assert on_screen == [bill["place"] for bill in SEED_BILLS]
    assert on_screen[0] == "Anand Bhavan"
    assert on_screen[-1] == "Kurry Kulture"
