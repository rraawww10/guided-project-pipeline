import os
from typing import List, Dict, Any, Tuple, Optional

import httpx


BASE_URL = os.environ["BASE_URL"]


def _get_candidates() -> List[Dict[str, Any]]:
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/candidates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    return data


def _is_ascii_name_asc(names: List[str]) -> bool:
    return names == sorted(names)


def test_c_3_1_no_active_orders_by_name_ascii():
    """
    c-3-1: With no active tokens (?active=), if two items have equal unrounded scores then name ASC by ASCII order decides; GET /api/rank reflects that order.

    Reading taken: all unrounded scores are equal when no signals are active, but we assert only the minimal requirement:
    pick any pair of candidates that also share the same years value (spec guarantees at least one pair), and assert their
    relative order under active="" follows ASCII name order. This avoids over-asserting a global sort the spec does not pin.
    """
    # Find a pair with the same years value (c-1-4 guarantees such a pair exists)
    items = _get_candidates()
    by_years: Dict[int, List[Tuple[str, str]]] = {}
    for it in items:
        by_years.setdefault(it["years"], []).append((it["id"], it["name"]))
    pair: Optional[Tuple[Tuple[str, str], Tuple[str, str]]] = None
    for group in by_years.values():
        if len(group) >= 2:
            # pick first two
            pair = (group[0], group[1])
            break
    assert pair is not None, "seed must contain at least one duplicate years value"
    (id_a, name_a), (id_b, name_b) = pair

    # Fetch ranking with no active tokens
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/rank", params={"active": ""})
    assert resp.status_code == 200
    ranked: List[Dict[str, Any]] = resp.json()
    order = [it["id"] for it in ranked]

    expected_first, expected_second = (id_a, id_b) if name_a <= name_b else (id_b, id_a)
    first_idx = order.index(expected_first)
    second_idx = order.index(expected_second)
    assert first_idx < second_idx, "name ASCII order must decide ties when no signals are active and years are equal"


def test_c_3_2_tag_active_same_years_same_tag_break_ties_by_name():
    """
    c-3-2: With active=tag, when two candidates have equal years and both either have or both lack the preferred tag, the tie is broken by name in ASCII order.
    This test locates such a pair from the seed and asserts their relative order under active=tag.
    """
    # Find a pair in the seed with same years and same tag presence
    items = _get_candidates()
    by_years: Dict[int, List[Tuple[str, str, bool]]] = {}
    for it in items:
        has_tag = isinstance(it.get("tags"), list) and ("typescript" in it["tags"])
        by_years.setdefault(it["years"], []).append((it["id"], it["name"], has_tag))
    pair: Optional[Tuple[Tuple[str, str, bool], Tuple[str, str, bool]]] = None
    for same_years_group in by_years.values():
        if len(same_years_group) < 2:
            continue
        # try to find two with same tag presence
        for i in range(len(same_years_group)):
            for j in range(i + 1, len(same_years_group)):
                a, b = same_years_group[i], same_years_group[j]
                if a[2] == b[2]:
                    pair = (a, b)
                    break
            if pair:
                break
        if pair:
            break
    assert pair is not None, "seed must contain two candidates with the same years and same tag presence"
    (id_a, name_a, _has_tag), (id_b, name_b, _has_tag2) = pair
    # Fetch active=tag ranking
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/rank", params={"active": "tag"})
    assert resp.status_code == 200
    ranked: List[Dict[str, Any]] = resp.json()
    order = [it["id"] for it in ranked]
    # Under equal years and equal tag presence, name ASCII should decide
    expected_first, expected_second = (id_a, id_b) if name_a <= name_b else (id_b, id_a)
    first_idx = order.index(expected_first)
    second_idx = order.index(expected_second)
    assert first_idx < second_idx, "name ASCII order must decide ties when both have (or both lack) the tag"


def test_c_3_3_tag_active_one_tagged_comes_first():
    """
    c-3-3: With active=tag, when two candidates have equal years and exactly one has the preferred tag, the tagged candidate appears first in GET /api/rank.
    """
    items = _get_candidates()
    by_years: Dict[int, List[Tuple[str, bool]]] = {}
    for it in items:
        has_tag = isinstance(it.get("tags"), list) and ("typescript" in it["tags"])
        by_years.setdefault(it["years"], []).append((it["id"], has_tag))
    pair_ids: Optional[Tuple[str, str]] = None
    for group in by_years.values():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                (id_a, tag_a), (id_b, tag_b) = group[i], group[j]
                if tag_a != tag_b:
                    # pick (tagged, untagged)
                    pair_ids = (id_a, id_b) if tag_a else (id_b, id_a)
                    break
            if pair_ids:
                break
        if pair_ids:
            break
    assert pair_ids is not None, "seed must contain two candidates with the same years where exactly one has the preferred tag"
    tagged_id, untagged_id = pair_ids
    # Fetch active=tag ranking
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.get("/api/rank", params={"active": "tag"})
    assert resp.status_code == 200
    ranked: List[Dict[str, Any]] = resp.json()
    order = [it["id"] for it in ranked]
    assert order.index(tagged_id) < order.index(untagged_id), "tagged candidate must come first under active=tag"
