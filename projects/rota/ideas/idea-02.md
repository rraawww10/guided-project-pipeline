# Capacity-Based Task Splitter

**One line:** Allocate a list of tasks (with points and skills) to people with weekly capacities, producing a balanced plan written to JSON.

## Theme
A small, practical allocator: given tasks with sizes and required skills, and people with capacities and skills, compute a reasonable plan for the next “cycle” (cycle is an integer, not a real date). It’s an algorithms-and-constraints exercise with a clean UI to preview and accept a plan. State lives in a JSON file under APP_DIR; no databases.

## Sessions
1. Setup data shapes and file store. Build `plan(tasks, people, capacity)` that greedily assigns highest-priority tasks into remaining capacities. End: a POST /api/plan returns a computed assignment for seeded tasks/people.
2. Add constraints: skill matching, per-person min/max tasks, and capacity validation with clear reasons for any unassigned tasks. Persist an accepted plan to `plan.json`. End: UI lets you recompute, preview, and accept to write the plan.
3. Editing and recompute: allow changing capacities/tasks in the UI; recompute updates the preview while preserving any locked assignments. End: end-to-end flow from entering inputs through to saved plan and a summary of remaining capacity and unassigned tasks.

## What the student types
- Greedy allocator with a stable ordering and capacity tracking.
- Constraint checks: skill compatibility, over-capacity prevention, and reasoned rejections.
- Merge logic to keep locked assignments while recomputing the rest.

## What this teaches that the shipped projects do not
A hands-on, constraint-aware allocator with locking and clear rejection reasons. Different from tip-split (pure arithmetic division) and stock-tracker (reporting/aggregation); this plans under capacity and skills, and avoids being a list-with-filter.

## Out of scope
Optimal bin packing, multiple cycles, calendars, or any external API. Inputs are only typed text/numbers.

## Risks
Edge-case ordering can make tests pass on seed order alone. Seeds must be anti-aligned with all requested sortings (e.g., not already priority-then-skill). Keep the algorithm deterministic to make tests stable.