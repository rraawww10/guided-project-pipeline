"""ep-habit-toggle: POST /api/habits/[id]/toggle. One test per criterion.

The store is reset around every test by the autouse fixture in conftest, so
each of these starts from the seeded week whatever the test before it wrote.
"""
from __future__ import annotations

from helpers import done_map, store_path


def test_c_3_1_toggling_stretch_on_the_25th_returns_streak_two(api):
    """c-3-1: POST /api/habits/stretch/toggle with {"date": "2026-08-25"} is 200
    with streak 2 and the days entry for 2026-08-25 marked done."""
    response = api.post("/api/habits/stretch/toggle", json={"date": "2026-08-25"})
    assert response.status_code == 200, f"{response.status_code}: {response.text}"

    habit = response.json()
    assert habit["streak"] == 2, habit
    marks = done_map(habit["days"])
    assert marks.get("2026-08-25") is True, habit["days"]


def test_c_3_2_toggling_drink_water_off_breaks_the_streak_and_persists(api):
    """c-3-2: POST /api/habits/drink-water/toggle with {"date": "2026-08-26"} is
    200 with streak 0, and a following GET /api/habits/drink-water persists
    streak 0 and 2 days marked done in the week."""
    response = api.post("/api/habits/drink-water/toggle", json={"date": "2026-08-26"})
    assert response.status_code == 200, f"{response.status_code}: {response.text}"
    assert response.json()["streak"] == 0, response.json()

    after = api.get("/api/habits/drink-water")
    assert after.status_code == 200, after.text

    habit = after.json()
    assert habit["streak"] == 0, habit
    done = [date for date, flag in done_map(habit["days"]).items() if flag]
    assert sorted(done) == ["2026-08-24", "2026-08-25"], habit["days"]


def test_c_3_3_toggling_read_pages_twice_lands_back_on_two_done_days(api):
    """c-3-3: POST /api/habits/read-pages/toggle twice with
    {"date": "2026-08-26"} is 200 both times, streak 3 first and streak 0 with 2
    days marked done second."""
    first = api.post("/api/habits/read-pages/toggle", json={"date": "2026-08-26"})
    assert first.status_code == 200, f"{first.status_code}: {first.text}"
    assert first.json()["streak"] == 3, first.json()

    second = api.post("/api/habits/read-pages/toggle", json={"date": "2026-08-26"})
    assert second.status_code == 200, f"{second.status_code}: {second.text}"

    habit = second.json()
    assert habit["streak"] == 0, habit
    done = [date for date, flag in done_map(habit["days"]).items() if flag]
    assert sorted(done) == ["2026-08-24", "2026-08-25"], habit["days"]


def test_c_3_4_the_error_branches_answer_404_or_400_and_write_nothing(api):
    """c-3-4: an unknown id is 404, a missing date, a non-date and a date outside
    the tracked week are 400, all 4 carry a non-empty error string, and the store
    file is byte-for-byte identical before and after the 4 requests."""
    materialise = api.get("/api/habits")
    assert materialise.status_code == 200, materialise.text
    assert store_path().exists(), f"{store_path()} was not written by GET /api/habits"
    before = store_path().read_bytes()

    attempts = [
        ("/api/habits/no-such-habit/toggle", {"date": "2026-08-26"}, 404),
        ("/api/habits/stretch/toggle", {}, 400),
        ("/api/habits/stretch/toggle", {"date": "not-a-date"}, 400),
        ("/api/habits/stretch/toggle", {"date": "2026-08-31"}, 400),
    ]

    for path, payload, expected in attempts:
        response = api.post(path, json=payload)
        assert response.status_code == expected, (
            f"POST {path} {payload} -> {response.status_code}: {response.text}"
        )
        body = response.json()
        assert isinstance(body, dict), f"POST {path} {payload} -> {body!r}"
        assert isinstance(body.get("error"), str), f"POST {path} {payload} -> {body!r}"
        assert body["error"].strip() != "", f"POST {path} {payload} -> {body!r}"

    after = store_path().read_bytes()
    assert after == before, (
        f"{store_path()} changed across the 4 rejected requests:\n"
        f"before: {before!r}\nafter:  {after!r}"
    )
