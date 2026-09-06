import json
from typing import Any, Dict, List, Tuple

import pytest
import httpx

from conftest import (
    compute_balances_from_expenses,
    transfers_apply_to_balances,
)


# Session 1

def test_c_1_1_get_expenses_returns_array_with_integer_amountcents(http_client: httpx.Client):
    resp = http_client.get("/api/expenses")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list), "Response must be a JSON array"
    for idx, item in enumerate(data):
        assert isinstance(item, dict), f"Item {idx} must be an object"
        assert "amountCents" in item, f"Item {idx} missing amountCents"
        # The spec requires integer cents
        amt = item["amountCents"]
        assert isinstance(amt, int), f"amountCents must be integer, got {type(amt)}"
        # Basic shape checks (id/description/paidBy/participants)
        assert isinstance(item.get("id"), str), f"Item {idx} id must be string"
        assert isinstance(item.get("description"), str), f"Item {idx} description must be string"
        assert isinstance(item.get("paidBy"), str), f"Item {idx} paidBy must be string"
        parts = item.get("participants")
        assert isinstance(parts, list), f"Item {idx} participants must be an array"
        for p in parts:
            assert isinstance(p.get("person"), str), "participant.person must be string"
            # weight optional, numeric if present
            if "weight" in p and p["weight"] is not None:
                assert isinstance(p["weight"], (int, float)), "participant.weight must be number when present"


# Session 2

def test_c_2_1_get_settlement_balances_match_expected_from_expenses(http_client: httpx.Client):
    # We compute expected balances client-side using the spec's integer math (see conftest)
    exps = http_client.get("/api/expenses").json()
    expected = compute_balances_from_expenses(exps)

    resp = http_client.get("/api/settlement")
    assert resp.status_code == 200
    payload = resp.json()
    balances = payload.get("balances", {})
    assert isinstance(balances, dict)

    # Every expected person must be present and equal
    for name, cents in expected.items():
        assert name in balances, f"Missing balance for {name}"
        assert int(balances[name]) == int(cents), f"Balance mismatch for {name}"

    # Totals must sum to zero
    assert sum(int(v) for v in balances.values()) == 0, "Balances must sum to zero"


def test_c_2_2_get_settlement_transfers_conserve_balances_and_sum_to_zero(http_client: httpx.Client):
    resp = http_client.get("/api/settlement")
    assert resp.status_code == 200
    payload = resp.json()
    balances = {k: int(v) for k, v in payload.get("balances", {}).items()}
    transfers: List[Dict[str, Any]] = payload.get("transfers", [])
    assert isinstance(transfers, list)

    # Sum to zero globally
    assert sum(balances.values()) == 0, "Balances must sum to zero"

    # Apply transfers and compare to balances
    net = transfers_apply_to_balances(transfers)
    # Ensure the domains are the same (missing nets imply zero)
    all_names = set(balances.keys()) | set(net.keys())
    for name in all_names:
        assert net.get(name, 0) == balances.get(name, 0), f"Net mismatch for {name}"


def test_c_2_3_get_settlement_transfers_sorted_deterministically(http_client: httpx.Client):
    resp = http_client.get("/api/settlement")
    assert resp.status_code == 200
    payload = resp.json()
    transfers: List[Dict[str, Any]] = payload.get("transfers", [])

    def key(t: Dict[str, Any]) -> Tuple[str, str]:
        return (str(t.get("from")), str(t.get("to")))

    assert transfers == sorted(transfers, key=key), "Transfers must be sorted by from, then to, ASC"


# Session 3

def test_c_3_1_get_settlement_minimalish_and_deterministic(http_client: httpx.Client):
    # Ambiguity A3: we assert determinism and a natural upper-bound for minimality without
    # pinning an exact count (seed not declared). Reading one suggests minimal count and
    # lexicographic tie-break; we enforce determinism across calls and sortedness.
    r1 = http_client.get("/api/settlement")
    r2 = http_client.get("/api/settlement")
    assert r1.status_code == 200 and r2.status_code == 200
    t1 = r1.json().get("transfers", [])
    t2 = r2.json().get("transfers", [])
    assert t1 == t2, "Transfers must be deterministic across calls"

    # Upper bound check: no more than non-zero balances minus 1 transfers (common minimal target)
    balances = {k: int(v) for k, v in r1.json().get("balances", {}).items()}
    nonzero = [k for k, v in balances.items() if int(v) != 0]
    if nonzero:
        assert len(t1) <= max(0, len(nonzero) - 1), "Transfers should not exceed n_nonzero - 1"

    # And enforce sortedness (ties by from/to as in c-2-3)
    tkey = lambda t: (str(t.get("from")), str(t.get("to")), int(t.get("amountCents", 0)))
    assert t1 == sorted(t1, key=tkey), "Transfers must be deterministically ordered"


def test_c_3_2_get_settlement_include_filter_excludes_and_balances_zero(http_client: httpx.Client):
    # Ambiguity A1: implement Reading one per ambiguity.md: compute using only included people.
    exps = http_client.get("/api/expenses").json()
    # Derive all names from expenses
    names = set()
    for e in exps:
        names.add(str(e.get("paidBy")))
        for p in e.get("participants", []):
            names.add(str(p.get("person")))
    names = sorted(n for n in names if n)
    assert len(names) >= 1, "Fixture should include at least one person"

    # Pick a subset: drop the last name if 2+ exist, else use empty include (include none)
    if len(names) >= 2:
        excluded = names[-1]
        include = names[:-1]
    else:
        excluded = names[0]
        include = []

    qs = ",".join(include)
    resp = http_client.get(f"/api/settlement?include={httpx.QueryParams({'include': qs})['include']}")
    assert resp.status_code == 200
    payload = resp.json()
    balances = {k: int(v) for k, v in payload.get("balances", {}).items()}
    transfers = payload.get("transfers", [])

    # No transfer mentions the excluded name
    for t in transfers:
        assert t.get("from") != excluded and t.get("to") != excluded, "Excluded person must not appear in transfers"

    # Balances must be defined only over the include set and sum to zero
    assert set(balances.keys()) <= set(include)
    assert sum(balances.values()) == 0, "Included-set balances must sum to zero"

    # Cross-check balances against our local computation under include
    expected = compute_balances_from_expenses(exps, include=include)
    assert balances == expected, "Balances must match computation over the included set"
