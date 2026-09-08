# Leave Request Conflict Checker

**One line:** Approve or deny leave requests against minimum staffing targets using integer day indexes and clear conflict reasons.

## Theme
A focused validation engine: employees submit leave requests as inclusive integer day ranges (e.g., days 10–12). The system checks them against existing approvals and per-day staffing minima, then approves or denies with a concrete reason. No dates or timezones; just indexed days. State persists to JSON under APP_DIR.

## Sessions
1. Model + overlap: define shapes and build `overlaps(a, b)` and `apply(approvals, request, minima)` that returns approve/deny and reasons. End: API POST validates several seeded requests and returns decisions.
2. State machine + UI: requests move Pending → Approved/Denied with idempotent replays, and decisions are persisted. End: a simple form to submit a request, list of decisions, and file-backed reload.
3. End-to-end guardrail: submit multiple requests that would drop a day below minima and get a Denied with an exact reason; approve a safe one and see counters update. Include Undo Last (revert last approval and recompute). End: full browser flow from input to persisted decision.

## What the student types
- Range arithmetic and overlap detection.
- Staffing count computation against minima with exact, human-readable reasons.
- A small, explicit state machine with safe persistence and undo.

## What this teaches that the shipped projects do not
Emphasizes validation with explicit reasons and range math, not generic CRUD, and avoids the real clock entirely. Different from shift-rota’s scheduling API pitfalls and from stock-tracker’s aggregations.

## Out of scope
Calendars/real dates, recurring rules, and any external auth/service.

## Risks
Off-by-one mistakes on inclusive ranges; ensure tests include boundary cases in both directions. Seeds must not accidentally satisfy the orderings or leave the grid trivially valid.