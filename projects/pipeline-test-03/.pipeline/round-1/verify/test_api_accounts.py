"""ep-accounts - GET /api/accounts, the fold of the accepted entries.

One test per criterion. Every expected value is a literal from spec.md's account
table; nothing here re-derives a total from the app's own answer.
"""
from __future__ import annotations

from helpers import ACCOUNT_TOTALS


def _accounts(api):
    """GET /api/accounts, checked for 200, returned as the parsed array."""
    r = api.get("/api/accounts")
    assert r.status_code == 200, (
        f"GET /api/accounts answered {r.status_code}, expected 200"
    )
    return r.json()


def test_c_2_1_accounts_are_four_totals_in_ascending_account_order(api):
    """c-2-1: GET /api/accounts returns 200 with a JSON array of 4 objects whose
    account values in order are food, rent, salary and travel, and whose paise
    values in the same order are -542555, -3720000, 6200000 and -455550.

    The array is compared whole, so the count, the ascending account order and
    the four sums are graded together. spec.md's Types block gives AccountTotal
    exactly the two fields below. Four different sums, three negative and one
    positive, so no constant object passes; with cut-account-totals unwritten the
    array is empty and the comparison goes red on the first element.
    """
    body = _accounts(api)

    assert isinstance(body, list), f"GET /api/accounts answered {type(body).__name__}"
    assert len(body) == 4, f"the array holds {len(body)} objects, expected 4"
    assert body == ACCOUNT_TOTALS, f"GET /api/accounts answered {body!r}"


def test_c_2_2_a_rejected_line_contributes_no_account_and_no_paise(api):
    """c-2-2: GET /api/accounts returns no object whose account is utilities, no
    object whose account is the empty string, and a rent object whose paise is
    -3720000, which is the sum of lines 5, 11 and 20 with the rejected line 28
    left out.

    utilities is named only by line 25 and the empty account only by line 13, and
    both lines are rejected, so neither may reach the fold. The rent total is the
    other half of the same rule: line 28 is a rent line with a comma in its
    amount, and -3720000 is the sum without it - 1200.00 more would be -3600000.
    The two absence assertions alone would be green on an empty array, which is
    exactly what an unwritten cut-account-totals gives, so the rent total is what
    makes this test red before the code is written.
    """
    body = _accounts(api)

    names = [obj["account"] for obj in body]
    assert "utilities" not in names, (
        f"utilities is named only by the rejected line 25, but accounts are {names!r}"
    )
    assert "" not in names, (
        f"the empty account is named only by the rejected line 13, but accounts "
        f"are {names!r}"
    )

    rent = [obj for obj in body if obj["account"] == "rent"]
    assert len(rent) == 1, f"expected exactly one rent object, got {rent!r}"
    assert rent[0]["paise"] == -3720000, (
        f"rent paise is {rent[0]['paise']}, expected -3720000 - the sum of lines "
        f"5, 11 and 20 with the rejected line 28 left out"
    )
