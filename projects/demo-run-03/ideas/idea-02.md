# Kanban With Enforced WIP Limits

**One line:** A minimal Kanban board where moving a card is a validated state transition that enforces per-column WIP limits in SQLite via Prisma.

## Theme
A clear state machine over persisted data: cards move between columns if and only if constraints hold. It uses server-side checks and a transaction to keep counts and moves consistent. No drag-and-drop, no external services; just deterministic transitions and queries.

## Sessions
1. Setup and read path — seeded columns and cards render in columns.
   - Prisma schema: Column(id, name, wip_limit), Card(id, title, column_id).
   - Migration + seed: 3 columns (Backlog, In Progress, Done), ~7 cards.
   - GET /api/board returns columns with their cards; React renders a simple three-column view with move buttons.
2. Validated move endpoint.
   - POST /api/cards/:id/move {to_column_id} enforces: target count < wip_limit; returns 200 on success, 409 with a reason on violation.
   - UI disables a move when it would overflow capacity (computed from server data), and shows server error text when attempted.
3. Pull-next and capacity math.
   - POST /api/columns/:id/pull moves the oldest Backlog card into In Progress only if capacity allows; records a Move row for audit.
   - Capacity indicator per column = wip_limit - current_count.
4. Metrics snapshot screen.
   - GET /api/metrics returns per-column counts and total WIP; UI lists counts and remaining capacity; moves log shows the last N transitions.

## What the student types
- The core transition guard: refuse a move when target_count >= wip_limit; return 409 with a stable reason string.
- A transaction that re-checks the limit and updates the card (and inserts a Move log) atomically.
- Capacity computation and serialization shape for the UI (server-calculated numbers, not derived ad hoc in the client).

## What this teaches that the shipped projects do not
- A small but real state machine persisted in a relational store, with server-enforced invariants and explicit error paths.
- Server-validated actions that the UI reflects without guesswork, plus a pull workflow that composes a query and a state change.

## Out of scope
- Drag-and-drop, swimlanes, due dates, timers, and cross-board moves.
- Auth and multi-user concurrency handling beyond a basic transaction.

## Risks
- Overbuilding the metrics pane or a "Done" workflow could crowd session time. Keep the grammar of transitions tiny and the move reasons stable for tests.