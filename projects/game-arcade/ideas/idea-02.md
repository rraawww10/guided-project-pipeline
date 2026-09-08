# Reversi (Othello) with Turn Engine and Replay

**One line:** An 8×8 Reversi you can play end-to-end, with legal-move highlighting, flipping logic, scoring, and a replay built from the move log in SQLite.

## Theme
Reversi is a crisp showcase of a turn engine: each click proposes a move, a rules engine decides if it’s legal, flips discs along lines, and passes when no move exists. The logic is discrete and assertable, the board is instantly visual, and the whole game replays deterministically from its move list.

## Sessions
1. Scaffold + schema + initial position: Next/React/TS UI for an 8×8 board. Prisma models (Game, Move). Seed the starting position (four center discs). Clicks place a disc without flips yet; turns alternate and state persists in SQLite.
2. Legal moves + highlighting: Implement `legalMoves` for the current player by scanning 8 directions for bracketed lines. Only legal cells are clickable; highlight them. Illegal clicks are ignored.
3. Apply move + flipping + scoring: Implement `applyMove` that flips bracketed discs. Detect passes (no legal moves), detect endgame (no legal moves for both), compute black/white counts, and declare a winner.
4. Replay + resume: Persist the move log. Provide a replay viewer that rebuilds any saved game from initial setup + moves. Support resuming an unfinished game from its last state and starting a new branch from an earlier move.

## What the student types
- `findFlips(board, pos, player): Coord[]` – scans rays to collect bracketed discs.
- `legalMoves(board, player): Set<Coord>` – derives clickable cells.
- `applyMove(state, move): State` – flips discs, switches turns, and handles pass/end.

## What this teaches that the shipped projects do not
- A full turn engine with rule-driven legality, multi-directional line scanning, and pass/finish states, not a form workflow.
- Deterministic replay from an initial state + move log, persisted with Prisma/SQLite.

## Out of scope
- AI opponent, network play, animations. Arbitrary board sizes or variants. Auth and profiles.

## Risks
- Edge cases in ray scanning (bounds, multiple lines per move). Ensuring pass logic is correct and testable. Keeping session 1 light while landing a clickable, persisted board.
