"""ep-ledger - GET /api/ledger, the parse of the 30-line seed file.

One test per criterion, asserting only that criterion. Every expected value is a
literal from spec.md; nothing here asks the app what the answer is.
"""
from __future__ import annotations

from helpers import (
    DIAGNOSTICS,
    ENTRY_FIRST,
    ENTRY_LAST,
    PAISE_FIXTURES,
)


def _ledger(api):
    """GET /api/ledger, checked for 200, returned as the parsed Ledger."""
    r = api.get("/api/ledger")
    assert r.status_code == 200, (
        f"GET /api/ledger answered {r.status_code}, expected 200"
    )
    return r.json()


def test_c_1_1_ledger_splits_the_seed_into_21_entries_and_6_diagnostics(api):
    """c-1-1: GET /api/ledger returns 200 with entries holding 21 objects and
    diagnostics holding 6 objects, with entries[0] equal to lineNo 4, date
    2026-01-01, account salary, description january pay and paise 4500000, and
    entries[20] equal to lineNo 30, date 2026-01-27, account food, description
    lunch and paise -18000.

    The two entries are compared whole: spec.md's Types block gives Entry
    exactly the five fields below, so an object carrying more or fewer is not
    the Entry this criterion pins. With cut-parse-line unwritten every data line
    is rejected, so entries is empty and the count assertion is the first to go
    red - 21 is not a number the fallback can produce.
    """
    body = _ledger(api)
    entries, diagnostics = body["entries"], body["diagnostics"]

    assert len(entries) == 21, f"entries holds {len(entries)} objects, expected 21"
    assert len(diagnostics) == 6, (
        f"diagnostics holds {len(diagnostics)} objects, expected 6"
    )
    assert entries[0] == ENTRY_FIRST, f"entries[0] is {entries[0]!r}"
    assert entries[20] == ENTRY_LAST, f"entries[20] is {entries[20]!r}"


def test_c_1_2_diagnostics_are_the_six_broken_lines_with_their_one_reason(api):
    """c-1-2: GET /api/ledger returns diagnostics whose lineNo values in order
    are 9, 13, 17, 22, 25 and 28, whose reason values in the same order are
    date must be YYYY-MM-DD, account must not be empty,
    expected 4 fields, found 3, date must be YYYY-MM-DD,
    amount must be a rupee amount like -250.00 and
    amount must be a rupee amount like -250.00, and returns an entry whose
    lineNo is 20 and whose date is 2026-02-30.

    The whole list is compared in one assertion, which grades the ascending
    lineNo order, the rule order (line 17 complains about its field count, not
    its date) and the skip rule (lines 1 to 3 produce nothing, so the list is
    six long and does not open at line 2) together. The line-20 entry is the
    shape-not-Date half: 2026-02-30 is accepted here while 2026-13-02, line 22,
    is rejected above.
    """
    body = _ledger(api)

    assert body["diagnostics"] == DIAGNOSTICS, (
        f"diagnostics is {body['diagnostics']!r}"
    )

    by_line = {e["lineNo"]: e for e in body["entries"]}
    assert 20 in by_line, (
        "no entry has lineNo 20 - the calendar-invalid date 2026-02-30 must be "
        "accepted, because the date is validated by shape and not by Date"
    )
    assert by_line[20]["date"] == "2026-02-30", (
        f"the entry at lineNo 20 carries date {by_line[20]['date']!r}"
    )


def test_c_1_3_amounts_become_whole_paise_without_a_float(api):
    """c-1-3: GET /api/ledger returns the entry with lineNo 8 with paise -25005,
    the entry with lineNo 6 with paise -245075, the entry with lineNo 19 with
    paise -110550, the entry with lineNo 10 with paise -12050 and the entry with
    lineNo 16 with paise 1200000.

    Five different values, four of them with non-zero paise digits, so no single
    constant passes; line 8 is -250.05, where 250.05 * 100 in floating point is
    25004.999... and a float multiply lands on -25004.
    """
    body = _ledger(api)
    by_line = {e["lineNo"]: e for e in body["entries"]}

    missing = [n for n in PAISE_FIXTURES if n not in by_line]
    assert not missing, f"no entry for lineNo {missing} - expected all five accepted"

    got = {n: by_line[n]["paise"] for n in PAISE_FIXTURES}
    assert got == PAISE_FIXTURES, f"paise by lineNo is {got!r}"
