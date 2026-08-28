"""sc-board at /. One test per board criterion, asserting only it."""
from __future__ import annotations

from urllib.parse import urlsplit

from playwright.sync_api import expect

from helpers import (
    LOAD_TIMEOUT,
    WEEK,
    cell,
    cell_done,
    cells,
    open_board,
    row,
    rows,
)


def test_c_1_4_board_renders_four_rows_and_drink_waters_streak_reads_five(page):
    """c-1-4: 4 habit-row elements, and the row with data-habit-id drink-water
    holds a habit-streak element whose text is exactly Streak: 5."""
    open_board(page)
    expect(rows(page)).to_have_count(4, timeout=LOAD_TIMEOUT)

    streak = row(page, "drink-water").get_by_test_id("habit-streak")
    expect(streak).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(streak).to_have_text("Streak: 5", timeout=LOAD_TIMEOUT)


def test_c_1_5_drink_waters_row_holds_seven_cells_with_three_done(page):
    """c-1-5: 7 day-cell elements inside the drink-water row, data-done the
    string true on 2026-08-24, 2026-08-25 and 2026-08-26 and the string false on
    the other 4."""
    open_board(page)
    water = row(page, "drink-water")
    expect(water).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(cells(water)).to_have_count(7, timeout=LOAD_TIMEOUT)

    expected = {
        date: ("true" if date in ("2026-08-24", "2026-08-25", "2026-08-26") else "false")
        for date in WEEK
    }
    assert cell_done(water) == expected


def test_c_3_5_clicking_a_cell_updates_only_that_row_without_a_second_list_fetch(page):
    """c-3-5: clicking the 2026-08-26 cell in the meditate row flips that cell's
    data-done to the string true and that row's habit-streak to Streak: 1, leaves
    the drink-water row at Streak: 5, and the browser issues exactly 1 GET whose
    path is /api/habits from opening / to the end of that click."""
    list_gets: list[str] = []

    def record(request) -> None:
        if request.method == "GET" and urlsplit(request.url).path == "/api/habits":
            list_gets.append(request.url)

    page.on("request", record)

    open_board(page)
    expect(rows(page)).to_have_count(4, timeout=LOAD_TIMEOUT)

    meditate = row(page, "meditate")
    target = cell(meditate, "2026-08-26")
    expect(target).to_have_count(1, timeout=LOAD_TIMEOUT)
    expect(target).to_have_attribute("data-done", "false", timeout=LOAD_TIMEOUT)

    target.click()

    expect(target).to_have_attribute("data-done", "true", timeout=LOAD_TIMEOUT)
    expect(meditate.get_by_test_id("habit-streak")).to_have_text(
        "Streak: 1", timeout=LOAD_TIMEOUT
    )
    expect(row(page, "drink-water").get_by_test_id("habit-streak")).to_have_text(
        "Streak: 5", timeout=LOAD_TIMEOUT
    )

    assert len(list_gets) == 1, (
        f"{len(list_gets)} GET /api/habits requests, expected exactly 1: {list_gets}"
    )
