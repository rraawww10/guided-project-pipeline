"""sc-bill's split, at /bills/anand-bhavan: 124000 paise, a 10 percent tip,
136400 paise with tip, stored as a split 4 ways. One test per session-3
criterion."""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import LOAD_TIMEOUT, open_bill, people_count, row_texts, step_people

FEWER = "Fewer people"
MORE = "More people"

FOUR_WAYS = [
    "Person 1 ₹341.00",
    "Person 2 ₹341.00",
    "Person 3 ₹341.00",
    "Person 4 ₹341.00",
]


def test_c_3_1_stored_split_renders_one_row_per_person(page):
    """c-3-1: 4 share-row elements reading Person 1..4 at the rupee 341.00."""
    open_bill(page, "anand-bhavan")
    assert row_texts(page, 4) == FOUR_WAYS


def test_c_3_2_one_fewer_click_shows_three_people_and_three_rows(page):
    """c-3-2: people-count reads 3 and 3 share-row elements render after one
    click of Fewer people."""
    open_bill(page, "anand-bhavan")
    step_people(page, FEWER, [3])
    expect(people_count(page)).to_have_text("3", timeout=LOAD_TIMEOUT)
    expect(page.get_by_test_id("share-row")).to_have_count(3, timeout=LOAD_TIMEOUT)


def test_c_3_3_three_way_split_hands_the_leftover_paise_to_the_first_people(page):
    """c-3-3: 136400 paise across 3 leaves 2 paise over, so the rows read
    454.67, 454.67 and 454.66."""
    open_bill(page, "anand-bhavan")
    step_people(page, FEWER, [3])
    assert row_texts(page, 3) == [
        "Person 1 ₹454.67",
        "Person 2 ₹454.67",
        "Person 3 ₹454.66",
    ]


def test_c_3_4_down_then_up_lands_back_on_the_stored_split(page):
    """c-3-4: 4 to 3 to 4, asserting the intermediate 3 as well as the four
    341.00 rows the return to 4 rebuilds."""
    open_bill(page, "anand-bhavan")
    step_people(page, FEWER, [3])
    expect(people_count(page)).to_have_text("3", timeout=LOAD_TIMEOUT)
    step_people(page, MORE, [4])
    expect(people_count(page)).to_have_text("4", timeout=LOAD_TIMEOUT)
    assert row_texts(page, 4) == FOUR_WAYS


def test_c_3_5_lower_clamp_holds_the_count_at_one(page):
    """c-3-5: four clicks of Fewer people from 4 walk 3, 2, 1 and then clamp at
    1, leaving one row for the whole 136400 paise."""
    open_bill(page, "anand-bhavan")
    step_people(page, FEWER, [3, 2, 1, 1])
    expect(people_count(page)).to_have_text("1", timeout=LOAD_TIMEOUT)
    assert row_texts(page, 1) == ["Person 1 ₹1364.00"]


def test_c_3_6_upper_clamp_holds_the_count_at_twenty(page):
    """c-3-6: seventeen clicks of More people from 4 reach 20 in sixteen and the
    seventeenth is answered by the clamp."""
    open_bill(page, "anand-bhavan")
    step_people(page, MORE, list(range(5, 21)) + [20])
    expect(people_count(page)).to_have_text("20", timeout=LOAD_TIMEOUT)
