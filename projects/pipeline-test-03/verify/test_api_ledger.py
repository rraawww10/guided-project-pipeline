"""ep-ledger: GET /api/ledger.

One test per criterion, asserting only what that criterion pins. Every expected
value is a literal copied from spec.md - the seed block, the broken-lines table
and the criteria themselves - so no test agrees with a broken parser by running
the same rules over the same file.
"""
from __future__ import annotations

from helpers import (
    DIAGNOSTIC_LINE_NOS,
    ENTRY_LINE_NOS,
    FIRST_ENTRY,
    LAST_ENTRY,
    PAISE_BY_LINE,
    REASONS,
    ROLLOVER_DATE,
    ROLLOVER_LINE_NO,
    get_ledger,
    one_by_line_no,
)


def test_c_1_1_ledger_has_21_entries_and_6_diagnostics_in_line_order(api):
    """c-1-1: GET /api/ledger returns 200 with entries holding 21 objects whose
    lineNo values in array order are 4, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18,
    19, 20, 21, 23, 24, 26, 27, 29 and 30, with diagnostics holding 6 objects
    whose lineNo values in array order are 9, 13, 17, 22, 25 and 28, with
    entries[0] equal to lineNo 4, date 2026-01-01, account salary, description
    january pay and paise 4500000, with entries[20] equal to lineNo 30, date
    2026-01-27, account food, description lunch and paise -18000, and with the
    entry whose lineNo is 20 carrying date 2026-02-30.

    The two lineNo lists are asserted as whole ordered lists, so the counts, the
    ordering, and the fact that lines 1 to 3 never arrive are one assertion
    each. Neither list can be produced by an unwritten block: with
    cut-parse-line empty every line is rejected, so entries is empty and
    diagnostics holds 27.

    ambiguity.md W1 records that line 20 does not discriminate a Date-based
    parser the way spec.md's prose claims (V8 accepts 2026-02-30 and rolls it
    over). The criterion still pins the stored string, so that is what this
    asserts: the entry is present and its date is the ten characters the file
    holds, not a rolled-over 2026-03-02.
    """
    body = get_ledger(api)
    entries = body["entries"]
    diagnostics = body["diagnostics"]

    assert [e.get("lineNo") for e in entries] == ENTRY_LINE_NOS, (
        f"entries carry lineNo {[e.get('lineNo') for e in entries]}, "
        f"expected {ENTRY_LINE_NOS}"
    )
    assert [d.get("lineNo") for d in diagnostics] == DIAGNOSTIC_LINE_NOS, (
        f"diagnostics carry lineNo {[d.get('lineNo') for d in diagnostics]}, "
        f"expected {DIAGNOSTIC_LINE_NOS}"
    )

    for key, expected in FIRST_ENTRY.items():
        assert entries[0].get(key) == expected, (
            f"entries[0].{key} is {entries[0].get(key)!r}, expected {expected!r}"
        )
    for key, expected in LAST_ENTRY.items():
        assert entries[20].get(key) == expected, (
            f"entries[20].{key} is {entries[20].get(key)!r}, expected {expected!r}"
        )

    rollover = one_by_line_no(entries, ROLLOVER_LINE_NO, "entry")
    assert rollover.get("date") == ROLLOVER_DATE, (
        f"the entry on line {ROLLOVER_LINE_NO} carries date "
        f"{rollover.get('date')!r}, expected {ROLLOVER_DATE!r}"
    )


def test_c_1_2_each_rejected_line_carries_its_own_first_broken_rule(api):
    """c-1-2: GET /api/ledger returns a diagnostic whose lineNo is 9 and whose
    reason is `date must be YYYY-MM-DD`, a diagnostic whose lineNo is 13 and
    whose reason is `account must not be empty`, a diagnostic whose lineNo is 17
    and whose reason is `expected 4 fields, found 3`, a diagnostic whose lineNo
    is 22 and whose reason is `date must be YYYY-MM-DD`, a diagnostic whose
    lineNo is 25 and whose reason is
    `amount must be a rupee amount like -250.00`, and a diagnostic whose lineNo
    is 28 and whose reason is the same string.

    Each diagnostic is found by its lineNo and never by its position, exactly as
    the criterion is worded - that is what makes this the criterion that tells
    the two session-1 cuts apart (spec.md, c-1-2). Line 17 is the rule-order
    fixture: it has three fields and a valid date, and it must complain about
    the field count. Every reason is compared with `==`, never `in`, so a
    Builder-invented prefix or suffix fails.
    """
    diagnostics = get_ledger(api)["diagnostics"]

    for line_no, reason in REASONS.items():
        diagnostic = one_by_line_no(diagnostics, line_no, "diagnostic")
        assert diagnostic.get("reason") == reason, (
            f"the diagnostic on line {line_no} reads "
            f"{diagnostic.get('reason')!r}, expected {reason!r}"
        )


def test_c_1_3_five_amounts_convert_to_integer_paise(api):
    """c-1-3: GET /api/ledger returns the entry with lineNo 8 with paise -25005,
    the entry with lineNo 6 with paise -245075, the entry with lineNo 19 with
    paise -110550, the entry with lineNo 10 with paise -12050 and the entry with
    lineNo 16 with paise 1200000.

    Five different values, four of them with non-zero paise digits, so no
    constant satisfies all five. Line 8 is the truncating-float fixture:
    250.05 * 100 is 25004.999... in floating point, so a truncating conversion
    lands on -25004 and fails here. ambiguity.md W2 records that a rounding
    float still passes all five - that gap belongs to Gate 1, and this test
    grades the five values the criterion actually pins.

    Each value is asserted as an int identical to the literal, so a float-typed
    -25005.0 is not what is being read: the type is checked before the value.
    """
    entries = get_ledger(api)["entries"]

    for line_no, paise in PAISE_BY_LINE.items():
        entry = one_by_line_no(entries, line_no, "entry")
        value = entry.get("paise")
        assert isinstance(value, int) and not isinstance(value, bool), (
            f"the entry on line {line_no} carries paise {value!r}, "
            f"a {type(value).__name__} - paise is always an integer"
        )
        assert value == paise, (
            f"the entry on line {line_no} carries paise {value}, expected {paise}"
        )
