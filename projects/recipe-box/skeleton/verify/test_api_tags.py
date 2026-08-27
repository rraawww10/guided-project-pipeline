"""ep-tags-list. One test per criterion, asserting only it."""
from __future__ import annotations

from helpers import ALL_TAGS


def test_c_2_3_tags_list_returns_the_five_distinct_tags_in_order(api):
    """c-2-3: GET /api/tags returns 200 with the JSON array baking, one-pot,
    quick, spicy, vegetarian in alphabetical order."""
    response = api.get("/api/tags")
    assert response.status_code == 200, f"got {response.status_code}: {response.text}"
    body = response.json()
    assert isinstance(body, list), f"expected a JSON array, got {body!r}"
    assert body == ALL_TAGS, f"got {body!r}"
