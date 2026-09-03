"""ep-scenarios at `GET /api/scenarios` - the seed, over HTTP.

One criterion reads this route: c-1-1, which grades the scaffolding and the seed.
Every expected value is a literal in `helpers.py`, copied from spec.md's seed
table.

This route is also the input every session-2 criterion depends on, and this is
the only test that reads it. Session 2 posts the seed as a literal request body
rather than fetching it here, so a wrong seed cannot cancel out a wrong
simulation: it fails in this row of the report and nowhere else. The reading and
its cost are set out in `helpers.py`'s module docstring.
"""
from __future__ import annotations

from helpers import (
    FLOORS,
    SCENARIO_CALLS,
    SCENARIO_IDS,
    SCENARIO_KEYS,
    SCENARIO_NAMES,
    SCENARIO_STARTS,
    get_scenarios,
    number,
)


def test_c_1_1_scenarios_are_the_five_seeded_lifts_in_seed_order(api):
    """c-1-1: GET /api/scenarios returns 200 with a JSON array of 5 scenarios
    whose id values are above, both-sides, overtake, passing and quiet in that
    order, each carrying id, name, floors, start and calls.

    The 200 and the array-of-objects shape are asserted in `get_scenarios`. The
    id list is compared as one ordered list rather than as a set, because the
    criterion says "in that order" - so a re-ordered seed fails here.

    Each object is then required to carry all five keys, with `name`, `floors`,
    `start` and `calls` equal to spec.md's seed table. The criterion's own
    wording asks only that the keys are carried; their values are asserted
    because they are the inputs every other criterion's expected numbers are
    derived from - the five-click `above` walk starts at `start` 2, and all four
    pinned traces are folds of these `calls` arrays. A suite that never read
    them could not tell a re-typed seed from a simulation bug, and would report
    the second when the first was true.

    **`calls` is compared as an ordered list, and that is a deliberate reading.**
    ambiguity.md W2 (worth a look, owner `nothing`) says the order inside `calls`
    is now load-bearing for grading - `overtake` seeded floor 5 before floor 8 is
    what makes `ahead = live` red on c-2-2 - and that no criterion pins it, so a
    later tidy back into registration order would stay green everywhere. W2 asks
    for c-1-1 to be extended in the spec and I have not done that; what this test
    does is compare `calls` to the seed table spec.md states, which is inside
    c-1-1's "each carrying ... calls" as the strictest honest reading of it. So a
    reordered seed fails here, in this one criterion, rather than nowhere. If the
    person at Gate 1 reads c-1-1 as pinning only the presence of the key, this is
    the assertion to strike, and W2's exposure is then real.

    This criterion declares no cuts. spec.md: c-1-1 is one of the criteria that
    "grade shipped code, and they are the criteria that stay green on the
    all-open skeleton." It is still red before any code exists, which is what
    the red-first check reads: with no route there is no 200.
    """
    scenarios = get_scenarios(api)

    assert len(scenarios) == 5, (
        f"GET /api/scenarios returned {len(scenarios)} scenarios, expected 5"
    )

    ids = [s.get("id") for s in scenarios]
    assert ids == SCENARIO_IDS, (
        f"ids are {ids} in response order, expected {SCENARIO_IDS}"
    )

    for entry in scenarios:
        scenario_id = entry["id"]
        missing = [k for k in SCENARIO_KEYS if k not in entry]
        assert not missing, f"{scenario_id} is missing {missing}: {sorted(entry)}"

        assert entry["name"] == SCENARIO_NAMES[scenario_id], (
            f"{scenario_id} name is {entry['name']!r}, "
            f"expected {SCENARIO_NAMES[scenario_id]!r}"
        )
        assert number(entry["floors"], f"{scenario_id} floors") == FLOORS, (
            f"{scenario_id} floors is {entry['floors']!r}, expected {FLOORS}"
        )
        assert number(entry["start"], f"{scenario_id} start") == SCENARIO_STARTS[
            scenario_id
        ], (
            f"{scenario_id} start is {entry['start']!r}, "
            f"expected {SCENARIO_STARTS[scenario_id]}"
        )
        assert entry["calls"] == SCENARIO_CALLS[scenario_id], (
            f"{scenario_id} calls are {entry['calls']!r}, "
            f"expected {SCENARIO_CALLS[scenario_id]} - spec.md seeds this array "
            f"in this order on purpose, and the order grades cut-calls-ahead"
        )
