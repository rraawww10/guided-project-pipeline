"""ep-habits-list: GET /api/habits. One test per criterion, asserting only it."""
from __future__ import annotations

from helpers import (
    HABIT_IDS,
    STREAKS,
    WEEK,
    WEEK_OF_SEPT_6,
    write_store_with_tracked_day,
)


def test_c_1_1_habits_list_returns_four_habits_with_seven_days_each(api):
    """c-1-1: 200 and a JSON array of 4 habits, each with id, name, streak and
    a days array of exactly 7 entries."""
    response = api.get("/api/habits")
    assert response.status_code == 200, response.text

    habits = response.json()
    assert isinstance(habits, list), f"body is {type(habits).__name__}, not a list"
    assert len(habits) == 4, f"{len(habits)} habits: {habits}"

    for habit in habits:
        assert isinstance(habit, dict), f"entry is {habit!r}"
        for key in ("id", "name", "streak", "days"):
            assert key in habit, f"{habit.get('id')!r} has no {key}: {habit}"
        assert isinstance(habit["id"], str) and habit["id"], habit
        assert isinstance(habit["name"], str) and habit["name"], habit
        assert isinstance(habit["streak"], int), habit
        assert isinstance(habit["days"], list), habit
        assert len(habit["days"]) == 7, (
            f"{habit['id']} has {len(habit['days'])} days: {habit['days']}"
        )


def test_c_1_2_habits_list_days_are_the_tracked_week_monday_first(api):
    """c-1-2: every habit's days[].date is 2026-08-24 through 2026-08-30 in that
    Monday-to-Sunday order."""
    response = api.get("/api/habits")
    assert response.status_code == 200, response.text

    habits = response.json()
    assert len(habits) == 4, f"{len(habits)} habits: {habits}"

    for habit in habits:
        dates = [day["date"] for day in habit["days"]]
        assert dates == WEEK, f"{habit['id']} days are {dates}"


def test_c_1_3_habits_list_streaks_are_five_zero_zero_and_one(api):
    """c-1-3: streak 5 for drink-water, 0 for read-pages, 0 for meditate and 1
    for stretch."""
    response = api.get("/api/habits")
    assert response.status_code == 200, response.text

    by_id = {habit["id"]: habit for habit in response.json()}
    assert sorted(by_id) == sorted(HABIT_IDS), f"ids are {sorted(by_id)}"

    got = {habit_id: by_id[habit_id]["streak"] for habit_id in HABIT_IDS}
    assert got == {habit_id: STREAKS[habit_id] for habit_id in HABIT_IDS}, got


def test_c_1_6_habits_list_week_follows_the_stored_tracked_day(api):
    """c-1-6: trackedDay 2026-08-30, a Sunday, still gives 2026-08-24 through
    2026-08-30; trackedDay 2026-09-06 gives 2026-08-31 through 2026-09-06."""
    for tracked_day, expected in (
        ("2026-08-30", WEEK),
        ("2026-09-06", WEEK_OF_SEPT_6),
    ):
        write_store_with_tracked_day(tracked_day)

        response = api.get("/api/habits")
        assert response.status_code == 200, response.text

        habits = response.json()
        assert len(habits) == 4, f"{len(habits)} habits: {habits}"

        for habit in habits:
            dates = [day["date"] for day in habit["days"]]
            assert dates == expected, (
                f"trackedDay {tracked_day}: {habit['id']} days are {dates}"
            )
