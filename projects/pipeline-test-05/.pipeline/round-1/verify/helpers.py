"""Shared fixture data and screen helpers for the Lift suite.

The app is already running; its URL arrives in `BASE_URL`. Nothing here starts a
server, installs anything or picks a port, and every wait is a retrying
Playwright wait, never a sleep.

**Nothing here reads `APP_DIR` and nothing here resets a file.** spec.md, Out of
scope: "Persistence. Nothing is written at runtime, so there is no live store."
`os.environ["APP_DIR"]` is also the lookup that raises `KeyError` for a student
running pytest by hand inside their skeleton, and this suite never needs it. The
tenth run in a working copy answers as the first.

Every number and every string below is copied out of spec.json's criteria and
spec.md's Data model - the seed table, the four pinned `runUntil` trace tables,
the five-click `above` walk and the endpoint bodies. They are this suite's own
fixture data: **no test asks the app what the answer is, and no test re-derives
an answer with the logic the app is being graded on.** There is no dispatch
rule, no distance comparison, no tie-break and no tick fold anywhere in this
file; every expected floor, mode, direction, `servedAt` and row count is a
literal.

The seed is a literal here rather than a read of `GET /api/scenarios` for the
same reason: session 2's request body is an *input*, and taking it from the
endpoint would let a wrong seed and a right simulation grade as green. c-1-1 is
the criterion that grades the seed, and it is the only test that reads the
endpoint for it.

## Selectors, and the one prefix trap

Every lookup on a screen goes through a `data-testid` the spec pins. spec.md,
Screens: "Every count and every string a criterion reads is pinned to a
`data-testid`, so styling cannot move a test." `get_by_test_id` matches the
attribute exactly, never as a prefix, and no class name and no styling is read
anywhere in this suite.

The one prefix locator, `family`, is used only with `floor-`. The spec's element
table is `floor-1..floor-8`, `car-floor`, `car-mode`, `tick`, `step-button`,
`served-<floor>`, `served-count`, `no-scenario`: of those, only the eight shaft
rows begin with `floor-` (`car-floor` ends with `floor` and does not begin with
`floor-`), so the family is exactly the shaft rows.

`served-` is deliberately **not** used as a prefix: `served-count` begins with
it, so a prefix match there would count the counter as a served line. The two
served elements are always looked up by their exact testid.
"""
from __future__ import annotations

import os

from playwright.sync_api import Locator, Page, expect

# The shaft page is a client component. This is the budget for its first paint
# and for the render that follows a click, passed explicitly so a missing
# element fails on this suite's own 20s budget rather than on Playwright's
# hidden 30s default.
LOAD_TIMEOUT = 20_000
STEP_TIMEOUT = 10_000

# How many times the FIRST press may be re-sent while the tick readout still
# reads 0. See `click_step`.
FIRST_CLICK_ATTEMPTS = 4

FLOORS = 8


def base_url() -> str:
    """The running app's URL. Read on call, so collection needs no environment."""
    return os.environ["BASE_URL"].rstrip("/")


# --------------------------------------------------------------------------
# the seed, exactly as spec.md's "The seed - data/scenarios.json" table pins it
# --------------------------------------------------------------------------
# "All five scenarios use floors: 8, floors numbered 1 to 8." The `calls` arrays
# are in the order the table gives them, which spec.md calls "the order the
# building registered them".
#
# ambiguity.md B1 (blocking, owner `nothing`) argues that this array order is
# what lets `cut-calls-ahead` be written as `ahead = live` and stay green, and
# suggests reordering `overtake` and `both-sides`. That is a spec change for the
# person at Gate 1; this suite tests the seed the spec on disk states. If that
# order changes, the two arrays below change with it and no expected trace value
# in this file moves - the pinned traces are the same either way for a correct
# implementation.
SCENARIO_IDS: list[str] = ["above", "both-sides", "overtake", "passing", "quiet"]

SCENARIO_NAMES: dict[str, str] = {
    "above": "One call above the car",
    "both-sides": "Calls on either side",
    "overtake": "A nearer call behind",
    "passing": "A call at the passing floor",
    "quiet": "No calls at all",
}

SCENARIO_STARTS: dict[str, int] = {
    "above": 2,
    "both-sides": 4,
    "overtake": 4,
    "passing": 1,
    "quiet": 5,
}

SCENARIO_CALLS: dict[str, list[dict]] = {
    "above": [{"floor": 6, "tick": 0}],
    "both-sides": [{"floor": 2, "tick": 0}, {"floor": 6, "tick": 0}],
    "overtake": [{"floor": 8, "tick": 0}, {"floor": 5, "tick": 2}],
    "passing": [{"floor": 5, "tick": 0}, {"floor": 3, "tick": 2}],
    "quiet": [],
}

# spec.json ep-scenarios: "Array of { id: string, name: string, floors: number,
# start: number, calls: Array<{ floor: number, tick: number }> }", and c-1-1
# words it "each carrying id, name, floors, start and calls".
SCENARIO_KEYS: tuple[str, ...] = ("id", "name", "floors", "start", "calls")


def scenario(scenario_id: str) -> dict:
    """The seeded `Scenario` object, built from the table above and nothing else.

    This is the request body session 2's criteria send. A fresh dict every call,
    so a test that mutates one - c-2-5 gives a call an out-of-range floor -
    cannot change what another test sends.
    """
    return {
        "id": scenario_id,
        "name": SCENARIO_NAMES[scenario_id],
        "floors": FLOORS,
        "start": SCENARIO_STARTS[scenario_id],
        "calls": [dict(call) for call in SCENARIO_CALLS[scenario_id]],
    }


# --------------------------------------------------------------------------
# the endpoint bodies and the message
# --------------------------------------------------------------------------
# spec.md, Endpoints: validation "is exactly one predicate with one message" and
# answers 400 with this exact body for all three rejected shapes.
ERROR_BODY: dict[str, str] = {"error": "scenario must carry floors, start and calls"}

# c-1-2 pins both the id in the URL and the id in the text, so they are one
# constant each and the interpolation is part of the assertion.
NO_SCENARIO_ID = "no-such-lift"
NO_SCENARIO_TEXT = "No scenario with id no-such-lift"

# the eight shaft rows c-1-2 counts, as testids
FLOOR_TESTIDS: list[str] = [f"floor-{n}" for n in range(1, FLOORS + 1)]


# --------------------------------------------------------------------------
# the endpoints
# --------------------------------------------------------------------------
def number(value: object, what: str) -> object:
    """Require a real JSON number, then hand it back for comparison.

    Several pinned values are 0 - `tick` 0 in c-2-6, `calledAt` 0 - and in
    Python `0 == False`, so a JSON `false` would satisfy a bare equality. This
    closes that hole wherever a number is compared.
    """
    assert isinstance(value, (int, float)) and not isinstance(value, bool), (
        f"{what} is {value!r} ({type(value).__name__}), not a JSON number"
    )
    return value


def get_scenarios(api) -> list[dict]:
    """GET /api/scenarios, checked down to the array c-1-1 reads."""
    response = api.get("/api/scenarios")
    assert response.status_code == 200, (
        f"GET /api/scenarios answered {response.status_code}: {response.text[:400]}"
    )
    body = response.json()
    assert isinstance(body, list), f"body is {type(body).__name__}, not a JSON array"
    for item in body:
        assert isinstance(item, dict), f"entry is {item!r}, not an object"
    return body


def post_simulate(api, **kwargs):
    """POST /api/scenarios/simulate, raw - the caller reads the status chosen.

    Used directly by c-2-5, which grades a 400. The keyword arguments go
    straight to httpx, so a test may send `json=` or a raw `content=` body.
    """
    return api.post("/api/scenarios/simulate", **kwargs)


def simulate(api, scenario_body: dict, max_ticks: int | None = None) -> dict:
    """POST a scenario, require the declared 200, hand back the parsed `Trace`.

    `maxTicks` is left out of the body entirely when `max_ticks` is None, which
    is what makes the four completing criteria also exercise spec.md's "`maxTicks`
    defaults to 100 when the body omits it". Only c-2-4 sends it.

    The status and the three `Trace` keys are asserted here; what is in them is
    each criterion's own test.
    """
    body: dict = {"scenario": scenario_body}
    if max_ticks is not None:
        body["maxTicks"] = max_ticks
    response = post_simulate(api, json=body)
    assert response.status_code == 200, (
        f"POST /api/scenarios/simulate answered {response.status_code} for "
        f"{scenario_body.get('id')!r} with maxTicks={max_ticks}: "
        f"{response.text[:400]}"
    )
    trace = response.json()
    assert isinstance(trace, dict), f"body is {type(trace).__name__}, not a JSON object"
    for key in ("rows", "served"):
        assert key in trace, f"trace has no {key} key: {trace}"
        assert isinstance(trace[key], list), (
            f"{key} is {type(trace[key]).__name__}, not a JSON array"
        )
    assert "complete" in trace, f"trace has no complete key: {trace}"
    return trace


def served_for(trace: dict, floor: int) -> dict:
    """The single `served` entry naming this floor, found by floor, never index.

    spec.md: "No scenario calls the same floor twice", so exactly one entry per
    floor is the requirement - a duplicate or a miss fails here rather than
    silently reading a wrong object.
    """
    found = [
        entry for entry in trace["served"]
        if isinstance(entry, dict) and entry.get("floor") == floor
    ]
    assert len(found) == 1, (
        f"expected exactly 1 served entry for floor {floor}, found {len(found)} "
        f"in {trace['served']}"
    )
    return found[0]


def row_for(trace: dict, tick: int) -> dict:
    """The single `rows` entry for this tick, found by tick and never by index.

    c-2-2 names "the rows entry for tick 2". Reading `rows[2]` instead would
    grade the same thing only if the rows are one per tick counting from 0 -
    which is a claim, not a given, so the lookup is by the `tick` field.
    """
    found = [
        row for row in trace["rows"]
        if isinstance(row, dict) and row.get("tick") == tick
    ]
    assert len(found) == 1, (
        f"expected exactly 1 row for tick {tick}, found {len(found)} "
        f"in {trace['rows']}"
    )
    return found[0]


# --------------------------------------------------------------------------
# the screen
# --------------------------------------------------------------------------
def normalize(text: str | None) -> str:
    """Collapse every run of whitespace to one space and strip the ends.

    Applied to every readout this suite reads, because the markup the Builder
    wraps a number in is its own to choose. No criterion on this screen pins an
    element to hold no text, so nothing here needs the uncollapsed reading.
    """
    return " ".join((text or "").split())


def open_shaft(page: Page, scenario_id: str) -> None:
    """Open `/scenarios/<id>` - sc-shaft.

    ambiguity.md B3 (blocking, owner `test-runner`) leaves it open whether this
    page resolves its `Scenario` on the server or fetches it in an effect, and
    no `data-testid` is reserved for a loading state, so there is nothing here to
    assert one from. This suite takes neither reading: every element is read
    through a retrying wait, so a first paint that arrives late is waited for,
    and no test asserts what the page shows before it has one.
    """
    page.goto(f"{base_url()}/scenarios/{scenario_id}", wait_until="domcontentloaded")


def by_testid(page: Page, value: str) -> Locator:
    """One exact data-testid match - never a prefix match."""
    return page.get_by_test_id(value)


def family(page: Page, prefix: str) -> Locator:
    """Every element whose data-testid starts with `prefix`.

    Used only with `floor-`, which no other testid in the spec's element table
    begins with.
    """
    return page.locator(f'[data-testid^="{prefix}"]')


def text_of(locator: Locator) -> str:
    """The element's text, whitespace-collapsed, waited for with LOAD_TIMEOUT."""
    return normalize(locator.text_content(timeout=LOAD_TIMEOUT))


def read_testid(page: Page, value: str) -> str:
    """Require exactly one element with this testid, then read its text.

    Existence is asserted before the text, because an element that is absent is
    not an element holding the wrong text, and the failure should say which.
    """
    locator = by_testid(page, value)
    expect(locator).to_have_count(1, timeout=LOAD_TIMEOUT)
    return text_of(locator)


def click_step(page: Page, times: int) -> None:
    """Press `step-button` exactly `times` times, waiting for each press to land.

    Four criteria are worded "after the element with data-testid step-button is
    clicked N times", so a test of one of them has to establish that N presses
    actually took effect. The `tick` readout is the signal used, for three
    reasons:

    * It is the only observable that changes on *every* press. c-1-6 steps an
      idle car in the `quiet` scenario, where the floor, the mode and the served
      count read the same after three presses as before the first - so a test
      that watched only those would be green against a page whose button does
      nothing at all, which is the one thing a test must not be.
    * It is shipped-written and sits outside every cut. spec.md's marker
      placement declares `let next: SimState = { ...state, tick: state.tick + 1 }`
      above the markers in `step`, so the tick advances even with both session-1
      cuts open. The synchronisation therefore does not depend on the code being
      graded.
    * spec.md pins it: `step` is a total function whose "`tick` always advances
      by exactly one", and the `tick` element "holds the tick number".

    This is a wait, not a criterion assertion. ambiguity.md W4 observes that no
    criterion grades the tick readout past c-1-2's 0 and suggests adding "the
    exact text 3 in tick" to c-1-6; that is a spec change for Gate 1 and this
    suite does not make it. What it does is decline to count presses it cannot
    see.

    The first press is the only one that can race hydration on a client
    component, so it is the only one re-sent - and it is re-sent only while the
    readout still reads the seeded 0, that is only while no step has been
    applied. A press that landed slowly cannot therefore be counted twice.
    """
    assert times >= 1, "click_step is for one press or more"

    button = by_testid(page, "step-button")
    expect(button).to_have_count(1, timeout=LOAD_TIMEOUT)
    tick = by_testid(page, "tick")
    # the seeded state, before anything is pressed: spec.md, manualStart - "tick 0"
    expect(tick).to_have_text("0", timeout=LOAD_TIMEOUT)

    landed = False
    for _ in range(FIRST_CLICK_ATTEMPTS):
        button.click()
        try:
            expect(tick).to_have_text("1", timeout=STEP_TIMEOUT)
        except AssertionError:
            if text_of(tick) != "0":
                raise
            continue
        landed = True
        break
    assert landed, (
        "the first press of step-button never advanced the tick readout past "
        f"{text_of(tick)!r} in {FIRST_CLICK_ATTEMPTS} attempts"
    )

    for n in range(2, times + 1):
        button.click()
        expect(tick).to_have_text(str(n), timeout=STEP_TIMEOUT)
