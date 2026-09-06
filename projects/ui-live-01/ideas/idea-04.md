# WIP-Limited Kanban (No Drag-and-Drop)

**One line:** A three-column board (Todo, Doing, Done) with enforced WIP limits and deterministic, button-driven moves and reordering.

## Theme
A constrained board highlights state transitions and limits rather than UI flourish. Cards move via explicit buttons; the server enforces WIP (work-in-progress) caps and persists order in a local JSON file. It’s a compact state machine plus a grid and avoids yet another filter/search list.

## Sessions
1. Board and seed: seed `app/data/tasks.seed.json` with status and order. Build an API that returns tasks grouped by status and a page that renders the three columns. End: a static board renders seeded tasks in the right columns.
2. Moves and limits: implement `moveCard(id, toStatus)` server route that refuses when Doing is full (configurable WIP limit). UI buttons enable/disable based on allowed transitions. End: moves succeed/fail visibly and the invariant holds.
3. Reordering and metrics: add up/down reordering within a column, persist stable `order` per status, and show derived metrics (WIP count, lead time placeholder, completion %). End: users can reorder deterministically and see live counts.

## What the student types
- `canMove(task: Task, to: Status, state: BoardState): boolean` – transition rule with WIP check.
- `applyMove(state: BoardState, id: string, to: Status): BoardState` – pure state update that preserves stable ordering.
- `persistBoard(state: BoardState): Promise<void>` – server-side write to JSON with conflict-free semantics.

## What this teaches that the shipped projects do not
- Hard constraints (WIP) enforced both client- and server-side with a pure decision function, rather than open-ended list filtering (recipe-box) or math-only UIs (tip-split).
- Deterministic reordering without a drag-and-drop library, emphasizing data shape and idempotent updates.

## Out of scope
- Drag-and-drop interactions or animations.
- Multi-user sync and websockets; any real-time network.
- Analytics beyond simple derived counts.

## Risks
- Getting reordering wrong (duplicate orders, cross-column collisions). Keep per-column scoped ordering and normalize before persist.
