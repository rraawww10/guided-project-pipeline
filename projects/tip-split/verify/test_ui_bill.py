"""sc-bill at /bills/[id]. One test per session-2 screen criterion."""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import LOAD_TIMEOUT, open_bill, open_bill_raw

RUPEE = "₹"


def test_c_2_3_bill_shows_its_stored_fields(page):
    """c-2-3: place, date, total, tip percent and saved split for anand-bhavan."""
    open_bill(page, "anand-bhavan")
    expect(page.get_by_test_id("bill-place")).to_have_text("Anand Bhavan")
    expect(page.get_by_test_id("bill-date")).to_have_text("2026-03-14")
    expect(page.get_by_test_id("bill-total")).to_have_text(f"{RUPEE}1240.00")
    expect(page.get_by_test_id("bill-tip-percent")).to_have_text("10%")
    expect(page.get_by_test_id("bill-saved-people")).to_have_text("Split 4 ways when saved")


def test_c_2_4_bill_shows_the_tip_and_grand_total(page):
    """c-2-4: 124000 paise at 10 percent gives a tip of the rupee 124.00 and a
    grand total of the rupee 1364.00."""
    open_bill(page, "anand-bhavan")
    expect(page.get_by_test_id("bill-tip-amount")).to_have_text(
        f"{RUPEE}124.00", timeout=LOAD_TIMEOUT
    )
    expect(page.get_by_test_id("bill-grand-total")).to_have_text(f"{RUPEE}1364.00")


def test_c_2_5_unknown_bill_shows_not_found_and_the_back_link(page):
    """c-2-5: /bills/not-a-bill shows Bill not found and a link named
    Back to saved bills whose href is /."""
    open_bill_raw(page, "not-a-bill")
    expect(page.get_by_text("Bill not found", exact=True)).to_have_count(
        1, timeout=LOAD_TIMEOUT
    )
    back = page.get_by_role("link", name="Back to saved bills", exact=True)
    expect(back).to_have_count(1)
    assert back.get_attribute("href") == "/"


def test_c_2_6_tip_rounds_half_up(page):
    """c-2-6: 87550 paise at 7 percent is 6128.5 paise and rounds up to 6129,
    so the tip reads the rupee 61.29 and the grand total the rupee 936.79."""
    open_bill(page, "kabab-junction")
    expect(page.get_by_test_id("bill-tip-amount")).to_have_text(
        f"{RUPEE}61.29", timeout=LOAD_TIMEOUT
    )
    expect(page.get_by_test_id("bill-grand-total")).to_have_text(f"{RUPEE}936.79")
