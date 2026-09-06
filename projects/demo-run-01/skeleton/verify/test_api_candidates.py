import os
from typing import List, Dict, Any

import httpx
import pytest


BASE_URL = os.environ["BASE_URL"]


def test_c_1_1_candidates_list_has_10_items():
    """
    c-1-1: GET /api/candidates returns 200 with a JSON array of 10 Candidate items
    """
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list), "response must be a JSON array"
    assert len(data) == 10, "seed must contain exactly 10 candidates"
    # spot-check required fields on first item to ensure shape
    first = data[0]
    assert isinstance(first.get("id"), str)
    assert isinstance(first.get("name"), str)
    assert isinstance(first.get("years"), int)
    assert isinstance(first.get("tags"), list)


def test_c_1_4_candidates_list_has_duplicate_years():
    """
    c-1-4: The /api/candidates JSON contains at least one pair of candidates with the same years value
    """
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/candidates")
    assert resp.status_code == 200
    items: List[Dict[str, Any]] = resp.json()
    years_counts: Dict[int, int] = {}
    for it in items:
        y = it["years"]
        years_counts[y] = years_counts.get(y, 0) + 1
    assert any(c >= 2 for c in years_counts.values()), "expected at least one duplicate years value"


def test_c_1_5_candidates_list_has_typescript_tag():
    """
    c-1-5: GET /api/candidates returns 200 with a JSON array that includes at least one item whose tags contain 'typescript'
    """
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/candidates")
    assert resp.status_code == 200
    items: List[Dict[str, Any]] = resp.json()
    assert any(
        isinstance(it.get("tags"), list) and "typescript" in it["tags"] for it in items
    ), "expected at least one candidate with the preferred tag 'typescript'"