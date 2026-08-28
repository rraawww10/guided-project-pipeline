"""sc-habit at /habits/[id]. One test per criterion, loaded and not-found."""
from __future__ import annotations

from playwright.sync_api import expect

from helpers import LOAD_TIMEOUT, WEEK, cell_done, cells, open_habit


def test_c_2_3_read_pages_page_shows_seven_cells_with_two_done(page):
    """c-2-3: /habits/read-pages renders 7 day-cell elements, data-done the
    string true on 2026-08-24 and 2026-08-25 and the string false on the other
    5."""
    open_habit(page, "read-pages")
    expect(cells(page)).to_have_count(7, timeout=LOAD_TIMEOUT)

    expected = {
        date: ("true" if date in ("2026-08-24", "2026-08-25") else "false")
        for date in WEEK
    }
    assert cell_done(page) == expected


def test_c_2_4_stretch_page_shows_its_name_and_streak_one(page):
    """c-2-4: /habits/stretch shows a habit-name element reading exactly Stretch
    and a habit-streak element reading exactly Streak: 1."""
    open_habit(page, "stretch")

    name = page.get_by_test_id("habit-name")
    expect(name).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(name).to_have_text("Stretch", timeout=LOAD_TIMEOUT)

    streak = page.get_by_test_id("habit-streak")
    expect(streak).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(streak).to_have_text("Streak: 1", timeout=LOAD_TIMEOUT)


def test_c_2_5_unknown_id_shows_habit_not_found_and_nothing_else(page):
    """c-2-5: /habits/no-such-habit shows a habit-missing element reading exactly
    Habit not found, 0 day-cell elements, and no habit-name and no habit-streak
    element."""
    open_habit(page, "no-such-habit")

    missing = page.get_by_test_id("habit-missing")
    expect(missing).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(missing).to_have_text("Habit not found", timeout=LOAD_TIMEOUT)

    expect(cells(page)).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(page.get_by_test_id("habit-name")).to_have_count(0, timeout=LOAD_TIMEOUT)
    expect(page.get_by_test_id("habit-streak")).to_have_count(0, timeout=LOAD_TIMEOUT)
