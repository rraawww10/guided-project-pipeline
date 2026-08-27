"""ep-bills-list and ep-bill-get. One test per criterion, asserting only it."""
from __future__ import annotations

from helpers import BILL_FIELDS, SEED_BILLS


def test_c_1_1_bills_list_returns_200_with_the_six_seed_bills(api):
    """c-1-1: GET /api/bills returns 200 with a JSON array of the 6 seed bills."""
    response = api.get("/api/bills")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list), f"expected a JSON array, got {type(body).__name__}"
    assert body == SEED_BILLS


def test_c_1_2_bills_list_holds_six_whole_bill_objects(api):
    """c-1-2: 6 bills, each with id, place, date, totalPaise, tipPercent, people."""
    body = api.get("/api/bills").json()
    assert isinstance(body, list), f"expected a JSON array, got {type(body).__name__}"
    assert len(body) == 6, f"expected 6 bills, got {len(body)}"
    for index, bill in enumerate(body):
        assert isinstance(bill, dict), f"bill {index} is not a JSON object"
        for field, kind in BILL_FIELDS.items():
            assert field in bill, f"bill {index} has no {field}"
            value = bill[field]
            if kind is int:
                assert isinstance(value, int) and not isinstance(value, bool), (
                    f"bill {index} {field} is not an integer: {value!r}"
                )
            else:
                assert isinstance(value, str), (
                    f"bill {index} {field} is not a string: {value!r}"
                )


def test_c_2_1_bill_get_returns_200_with_the_stored_bill(api):
    """c-2-1: GET /api/bills/anand-bhavan returns 200 with that bill."""
    response = api.get("/api/bills/anand-bhavan")
    assert response.status_code == 200, response.text
    bill = response.json()
    assert bill["id"] == "anand-bhavan"
    assert bill["totalPaise"] == 124000
    assert bill["tipPercent"] == 10
    assert bill["people"] == 4


def test_c_2_2_bill_get_returns_404_with_an_error_body_for_an_unknown_id(api):
    """c-2-2: GET /api/bills/not-a-bill returns 404 with a JSON body holding error."""
    response = api.get("/api/bills/not-a-bill")
    assert response.status_code == 404, f"got {response.status_code}: {response.text}"
    body = response.json()
    assert isinstance(body, dict), f"expected a JSON object, got {body!r}"
    assert "error" in body, f"no error field in {body!r}"
