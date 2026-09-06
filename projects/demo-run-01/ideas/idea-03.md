# WIP‑Limited Kanban

**One line:** A three‑column kanban that enforces per‑column WIP limits and guard‑railed moves with clear refusal reasons.

## Theme
Move beyond CRUD by modeling workflow as a finite‑state machine: To‑Do → In‑Progress → Done, with explicit guards (WIP caps, blocked items). It’s useful because many production UIs need to enforce invariants, not just display data, and students practice writing a transition function they can test.

## Sessions
1. Seed 8–10 tasks and render three columns with simple Move Left/Right buttons. Provide GET /api/tasks that serves the seed and a POST /api/preview that echoes a proposed move. End with a working board where tasks can move freely.
2. Implement canMove(task, to, state) and transition(state, event) that enforce: per‑column WIP limits, no skipping columns, and “blocked” tasks cannot enter Done. When a move is refused, show a short reason inline. End with a guarded board whose rules are enforced.
3. Add Start Oldest First: a deterministic batch action that moves the oldest eligible N tasks into In‑Progress within the WIP cap. Record an audit trail of transitions (task id, from → to, why) and render it under the board. End with predictable automation and history.

## What the student types
- canMove and transition: pure functions encoding the state machine and its guard conditions.
- enforceWip: counting per‑column and refusing moves that would breach a limit, with a human‑readable reason.
- pickOldestEligible: select tasks deterministically for batch moves.

## What this teaches that the shipped projects do not
- An explicit, testable transition table with guards and refusal paths, not just optimistic updates to a list.
- Deterministic batch operations under constraints (WIP) and surfacing the reason when rules prevent an action.

## Out of scope
- Drag‑and‑drop; use buttons to keep the surface area small.
- Persistence beyond memory/seed; no external database.
- User accounts or multi‑user sync.

## Risks
- Edge cases around WIP and blocked flags causing confusing UI states; mitigate by keeping transitions pure and showing refusal messages.
- Over‑engineering batch actions; keep them simple and deterministic.