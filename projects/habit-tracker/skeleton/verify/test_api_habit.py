"""ep-habit-get: GET /api/habits/[id]. One test per criterion."""
from __future__ import annotations


def test_c_2_1_habit_get_returns_drink_waters_week_and_streak(api):
    """c-2-1: GET /api/habits/drink-water is 200 with name Drink water, a days
    array of exactly 7 entries and streak 5."""
    response = api.get("/api/habits/drink-water")
    assert response.status_code == 200, response.text

    habit = response.json()
    assert habit["name"] == "Drink water", habit
    assert isinstance(habit["days"], list), habit
    assert len(habit["days"]) == 7, habit["days"]
    assert habit["streak"] == 5, habit


def test_c_2_2_habit_get_returns_404_with_an_error_for_an_unknown_id(api):
    """c-2-2: GET /api/habits/no-such-habit is 404 with a JSON body whose error
    key holds a non-empty string."""
    response = api.get("/api/habits/no-such-habit")
    assert response.status_code == 404, f"{response.status_code}: {response.text}"

    body = response.json()
    assert isinstance(body, dict), body
    assert isinstance(body.get("error"), str), body
    assert body["error"].strip() != "", body
