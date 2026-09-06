import os
from typing import List, Dict, Any

import httpx


BASE_URL = os.environ["BASE_URL"]


def test_c_2_1_rank_years_returns_10_items_with_shape():
    """
    c-2-1: GET /api/rank?active=years returns 200 with a JSON array of 10 RankItem having id, name, score (number), and reasons (string[])

    Strengthened to ensure the 'active=years' token is actually applied: at least one item must
    have a positive numeric score and at least one reasons[] entry that mentions 'years'. This
    ensures the query parser is exercised and prevents a fallback implementation from passing.
    """
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/rank", params={"active": "years"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 10
    first = data[0]
    assert isinstance(first.get("id"), str)
    assert isinstance(first.get("name"), str)
    # score must be a JSON number, not a string
    assert isinstance(first.get("score"), (int, float)), "score must be a number in JSON"
    # reasons must be an array of strings
    reasons = first.get("reasons")
    assert isinstance(reasons, list)
    assert all(isinstance(r, str) for r in reasons)

    # Additionally, with active=years at least one item should show a non-zero score coming from years
    scores: List[float] = [it.get("score") for it in data if isinstance(it.get("score"), (int, float))]
    assert any(s > 0 for s in scores), "with active=years, at least one score must be > 0"
    # And at least one reasons[] should mention 'years'
    joined_reasons = [", ".join(it.get("reasons", [])).lower() for it in data]
    assert any("years" in txt for txt in joined_reasons), "expected at least one reasons entry to mention 'years' when active=years"


def test_c_2_2_rank_years_orders_by_unrounded_score_desc():
    """
    c-2-2: With active=years only, GET /api/rank returns items ordered by unrounded score in descending order (non-increasing)
    """
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/rank", params={"active": "years"})
    assert resp.status_code == 200
    data: List[Dict[str, Any]] = resp.json()
    # Assert scores are non-increasing across the list
    scores = [item["score"] for item in data]
    assert all(isinstance(s, (int, float)) for s in scores)
    assert scores == sorted(scores, reverse=True), "scores must be in non-increasing order"


def test_c_3_4_rank_years_min_100_returns_empty_array():
    """
    c-3-4: GET /api/rank?active=years&min=100 returns 200 with an empty JSON array
    """
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/rank", params={"active": "years", "min": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data == [], "expected empty array when min threshold is too high"