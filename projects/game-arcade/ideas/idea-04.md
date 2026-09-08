# Sudoku Trainer with Deterministic Hint Engine

**One line:** A Sudoku you can play in the browser with candidates, a deterministic hint button (singles-only), undo/redo, and saved puzzles/games in SQLite.

## Theme
A solver-shaped project: instead of randomness, the interesting logic is constraint propagation and choosing the next forced move. We seed the app with a few hand-authored puzzles solvable by singles, and make the hint engine pick the same next move every time so tests and replays are stable.

## Sessions
1. Scaffold + seed + input: Prisma models (Puzzle, Game, Move). Seed 3–5 puzzles. Render a 9×9 grid with cell input and simple validity (row/col/box) feedback. Persist moves with undo/redo.
2. Candidates: Implement `computeCandidates(grid)` to derive remaining digits per empty cell; render pencil marks. Block illegal entries.
3. Deterministic hints: Implement `findNextHint(grid)` that returns the next forced move by rule order (e.g., naked single, then hidden single), using a stable scan order. Apply as a discrete action.
4. Replay + solve-to-end: Rebuild a game from (puzzle + moves). Provide a step-through replay and a “solve by hints” function that applies hints until stuck or solved, logging each step.

## What the student types
- `computeCandidates(grid): Set<number>[][]` – row/col/box constraints.
- `findNextHint(grid): { cell: Coord; digit: number; reason: string } | null` – naked/hidden singles with a stable tie-breaker.
- `applyMove(state, move): State` – validates and updates grid, supports undo/redo.

## What this teaches that the shipped projects do not
- A small, deterministic solver with a rule order and a stable search, plus candidate visualization – different from CRUD and filtering.
- Replay from a fixed puzzle and logged moves, persisted via Prisma/SQLite.

## Out of scope
- Advanced techniques (X-Wing, swordfish), generators, or randomness. Timers, leaderboards, online sharing, or auth.

## Risks
- Getting candidate math exactly correct and keeping hint selection stable across runs (define a fixed cell/box scan order). Ensuring session 1 remains light while still landing a clickable, persisted board.
