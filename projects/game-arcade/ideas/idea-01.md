# Seeded Minesweeper

**One line:** A playable Minesweeper with a deterministic seed, flood-reveal, win/lose, and saved games in SQLite via Prisma.

## Theme
A classic grid puzzle that rewards careful reasoning. We make the board from a fixed seed so every test and replay is identical, then implement the reveal rules and victory checks. It is highly visual and click-driven, yet entirely turn-based and deterministic.

## Sessions
1. Scaffold + seed + render: Next/React/TS app route and Prisma schema (Game, Cell). Deterministically generate a mine layout from a numeric seed and persist it. Render the grid and allow clicking to reveal a single cell. The game loads from the DB on refresh.
2. Counting: Compute adjacent mine counts per cell and display numbers for revealed cells. Disallow revealing a mine from session 1’s naive handler (mark as exploded and end the game state). Persist turns.
3. Flood reveal + flags: Implement breadth-first flood reveal from a zero cell, revealing contiguous safe regions in one discrete transition. Add right-click flagging (or a toggle control) as a separate, persisted action. Win/lose detection based on revealed safe tiles.
4. Replay + resume: Save a move log. Provide a replay viewer that rebuilds the board from seed + actions and steps through turns. Show finished games list (from SQLite) and allow resuming an in-progress board.

## What the student types
- A small seeded PRNG (e.g., mulberry32) to produce a reproducible mine layout from `seed`.
- `countAdjacentMines(board, pos): number` – pure function over coordinates.
- `revealFrom(board, start): Board` – flood-fill that reveals contiguous zeroes and their borders without recursion limits.

## What this teaches that the shipped projects do not
- Deterministic content via a seeded generator and a replay built from (seed + actions), not CRUD.
- A non-trivial grid algorithm (flood-fill and neighbor counts) and a finite game state machine (playing, won, lost) persisted with Prisma/SQLite. Existing shipped projects skew to forms/lists and dashboards; this is a visual, turn-based puzzle.

## Out of scope
- Real-time timers, animations, or leaderboards. No network/APIs, no auth. Board sizes beyond a small fixed set. Touch gestures and mobile polish.

## Risks
- Getting flood-fill correct and testable without stack overflows (use queue not recursion). Ensuring every source of randomness is seeded so tests/replays are stable. Balancing setup load in session 1 so it stays light while still rendering a clickable grid.
