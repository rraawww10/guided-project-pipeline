# Fair Rota: Round‑Robin with Rest Windows

**One line:** A small Next/React app that builds a fair weekly shift rota from a staff list and constraints, using a round‑robin generator with rest and max‑load rules.

## Theme
A rota is more than a list: it encodes fairness, rest windows and hard limits. This project turns those ideas into code by generating a weekly schedule from simple inputs (names, shift slots, numeric rules) and explaining the result with a fairness score. Worth it because it blends pure functions with visible outcomes, and every rule is testable without real dates.

## Sessions
1. Seed + capture: a page to add staff and define the week’s shift slots; API writes a JSON file under APP_DIR. Runs with seeded names and shows an empty rota grid populated with slots.
2. Generator v1: implement round‑robin assignment that fills each slot cycling through staff; enforce hard constraints (max shifts per person, no two shifts in the same day). Pressing “Generate” shows a complete grid.
3. Fairness + rest: add a rest‑window rule (no assignment within X slots of a previous one) and a fairness score that reports spread and violations; add “Re‑roll” to rebuild with a different starting offset and persist the accepted rota.

## What the student types
- Round‑robin allocator with a rotating pointer and per‑person counters.
- Constraint checks: same‑day clash rejection and rest‑window (distance‑in‑slots) validator.
- Fairness metric: compute mean/variance of load and a penalty for any violation; pick the best of k starting offsets.

## What this teaches that the shipped projects do not
Existing projects cover list UIs, filtering, small financial maths and simple toggles. This one adds a tiny constraint solver with fairness scoring, including explaining a computed plan. It foregrounds scheduling rules over CRUD and keeps all logic in pure TS functions the tests can call.

## Out of scope
- Real dates or timezones; days are indices (D1…D7).
- Drag/drop reordering; swaps are simple buttons or re‑rolls.
- Optimizing to global optimality; we keep a heuristic (k offsets) not ILP.

## Risks
Packing too many constraints into session 2 or 3 could overrun. Keep inputs small (≤6 staff, ≤14 slots) and ensure the allocator always terminates or reports an unfillable slot deterministically.