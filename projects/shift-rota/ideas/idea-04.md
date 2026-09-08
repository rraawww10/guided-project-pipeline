# Availability Matcher: Fill Coverage From Yes/No

**One line:** Build a weekly rota by choosing from a staff×slot availability matrix to meet per‑slot minimums, with clear explanations for any gap.

## Theme
Sometimes the rota is “who can work when?”. This idea models it explicitly: a boolean availability grid and numeric coverage targets. The core is a deterministic chooser that prefers the least‑loaded available person while respecting rest windows.

## Sessions
1. Setup + matrix: seed staff and a small set of slots; UI to tick availability per person/slot and set a required count per slot. Persist to JSON and render the empty assignment/coverage view.
2. Filler: implement a greedy fill that, for each slot, repeatedly selects the available person with the fewest assigned shifts so far (tie‑break by name) who also passes same‑day and rest‑window constraints. Stop when the slot’s minimum is met or no candidate exists. Show the assignment grid and unmet counts.
3. Explanations + what‑if: for any unmet slot, compute and display the reason chain (e.g., “Only Alex available; Alex blocked by rest from Tue‑N”). Add a one‑click what‑if that toggles one availability and re‑runs fill.

## What the student types
- Candidate selection and tie‑break logic over a 2D availability structure.
- Rest‑window and same‑day validators.
- Explanation builder that traces why no candidate qualified for a slot.

## What this teaches that the shipped projects do not
It centers selection over a matrix with explicit witnesses (why this person, why not that one), contrasting with existing projects that emphasize lists, filters or arithmetic. The explanation step makes invisible constraints visible and graded.

## Out of scope
- Optimal global matching; we implement a deterministic greedy pass only.
- Real calendar/time.
- CSV import/export.

## Risks
Explanation text can balloon; keep seeds tiny (≤5 staff, ≤10 slots) and make messages templated so tests can assert exact strings.