# Slot-Based Day Planner (No Real Clock)

**One line:** A keyboard-first planner that places tasks into discrete time slots, enforcing non-overlap and showing utilization—all without touching the real clock.

## Theme
Scheduling as a discrete grid problem. Students model a day as N slots, implement non-overlap insertion and movement, and add an auto-pack to close gaps. It is worth a session because it turns a familiar UI into precise rules and invariants.

## Sessions
1. Scaffold + grid: render a vertical slot grid and a form to add a task with `startSlot` and `length`; implement `canPlace` and insert; visualize occupancy.
2. Moves and resizes: add keyboard moves (arrows + Enter) with a pure reducer that snaps and refuses overlaps; keep rendering deterministic.
3. Auto-pack and export: implement `autoPack(tasks)` to left-pack tasks without reordering labels; export/import JSON; show utilization metrics.

## What the student types
- `canPlace(tasks, candidate)`: checks bounds and overlap against existing tasks.
- `applyMove(state, id, delta)`: pure reducer enforcing non-overlap and snapping to the grid.
- `autoPack(tasks)`: stable, gap-closing compaction that preserves a declared order.

## What this teaches that the shipped projects do not
Not a filterable list: it is a grid with constraints, keyboard interactions, and invariants you can test. It emphasizes discrete modeling (indices, not dates) to stay deterministic and reproducible.

## Out of scope
- Drag-and-drop and pointer hit-testing.
- Real times, timezones, or calendars; slots are abstract indices.
- Recurrence and reminders.

## Risks
Keyboard semantics can sprawl. Keep commands minimal (arrow keys and Enter) and constrain the model to a single column of fixed-size slots so tests stay small and reliable.
