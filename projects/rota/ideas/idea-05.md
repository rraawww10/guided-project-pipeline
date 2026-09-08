# Fairness Auditor + Next Assignee Suggester

**One line:** Read past rota history, compute fairness metrics, and suggest the next assignee per slot to minimize streaks and balance totals.

## Theme
When a rota is assigned incrementally, you need a principled next choice. This project computes fairness metrics (total assignments, current streak length, days since last assignment) from history, then applies a weighted, deterministic scorer to suggest the next assignee for a given slot. All data stays in JSON under APP_DIR; the UI is minimal and testable.

## Sessions
1. History reader + metrics: from `history.json`, compute per-person totals, last-assigned distance, and current streaks. End: metrics table renders and recomputes from file.
2. Selector logic: implement `suggestNext(slot, metrics, caps)` that scores candidates (prefer lower totals, longer since last, and avoid exceeding a streak cap), with a fixed, documented tie-breaker. End: API returns a single suggested id for a seeded query.
3. Full flow: click Assign to append the suggestion to history and update metrics; provide Undo Last. End: end-to-end browser flow proving that repeated assigns never exceed the streak cap and that totals balance over several steps.

## What the student types
- Metric calculators over a compact history.
- A deterministic weighted scorer and comparator with a streak cap.
- Append/undo transitions in the file store.

## What this teaches that the shipped projects do not
Focuses on fairness metrics and deterministic selection rather than building an entire schedule at once. Unlike shift-rota (full schedule + route registration pitfalls) or habit-tracker/recipe-box (CRUD), this centers on scoring rules, tie-breaking, and invariant caps.

## Out of scope
Authentication, calendars, multi-team tenancy, and anything beyond text/number inputs.

## Risks
Subjective weights can drift; pin exact weights and tiebreak order in the spec to keep tests stable. Seeds must be chosen so a “do nothing” strategy cannot pass (e.g., history already perfectly balanced).