"""ep-accounts: GET /api/accounts.

One test per criterion, asserting only what that criterion pins. The four names
and the four totals are the literals spec.md prints in "The four accounts, their
totals in paise"; nothing here re-folds the entries.
"""
from __future__ import annotations

from helpers import (
    ACCOUNT_NAMES,
    ACCOUNT_PAISE,
    RENT_TOTAL_PAISE,
    get_accounts,
)


def test_c_2_1_accounts_are_four_totals_sorted_by_name(api):
    """c-2-1: GET /api/accounts returns 200 with a JSON array of 4 objects whose
    account values in order are food, rent, salary and travel, and whose paise
    values in the same order are -542555, -3720000, 6200000 and -455550.

    Both lists are asserted whole and in order, so the count, the ascending sort
    and the four sums are graded together. None of it survives an unwritten
    block: with cut-account-totals empty the array is empty, and with
    cut-amount-paise empty there are no accepted entries to fold at all.
    """
    accounts = get_accounts(api)

    assert [a.get("account") for a in accounts] == ACCOUNT_NAMES, (
        f"accounts are {[a.get('account') for a in accounts]}, "
        f"expected {ACCOUNT_NAMES}"
    )
    assert [a.get("paise") for a in accounts] == ACCOUNT_PAISE, (
        f"paise are {[a.get('paise') for a in accounts]}, expected {ACCOUNT_PAISE}"
    )


def test_c_2_2_a_rejected_line_contributes_no_account_and_no_paise(api):
    """c-2-2: GET /api/accounts returns no object whose account is utilities, no
    object whose account is the empty string, and a rent object whose paise is
    -3720000, which is the sum of lines 5, 11 and 20 with the rejected line 28
    left out.

    utilities is named only by line 25 and the empty account only by line 13,
    and both lines are rejected; line 28 is a rent line rejected for its
    thousands separator, so a parser that lets it through reads rent as
    -3600000 rather than -3720000. The rent object is found by name, not by
    index, because the criterion names it rather than positioning it.
    """
    accounts = get_accounts(api)
    names = [a.get("account") for a in accounts]

    assert "utilities" not in names, (
        f"utilities is named by the rejected line 25 only, but accounts are {names}"
    )
    assert "" not in names, (
        f"the empty account is named by the rejected line 13 only, "
        f"but accounts are {names}"
    )

    rent = [a for a in accounts if a.get("account") == "rent"]
    assert len(rent) == 1, f"expected exactly 1 rent object, found {rent}"
    assert rent[0].get("paise") == RENT_TOTAL_PAISE, (
        f"rent totals {rent[0].get('paise')}, expected {RENT_TOTAL_PAISE} "
        f"- lines 5, 11 and 20 with the rejected line 28 left out"
    )
