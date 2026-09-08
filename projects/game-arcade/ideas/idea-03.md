# Seeded Match‑3 with Cascades and Scoring

**One line:** A deterministic match‑3 board: swap adjacent tiles, resolve matches in cascades with gravity and refills from a seed, score combos, and save replays in SQLite.

## Theme
A scoring-heavy puzzle in which a single discrete turn may produce a chain of effects: match → remove → score → gravity → refill → possible rematch. We make every refill deterministic from a seed so the same swap always produces the same cascade. It’s visually gratifying and purely turn-based.

## Sessions
1. Scaffold + seed + swap: Prisma schema (Game, Turn). Render a colored grid generated from a numeric seed. Allow swapping two adjacent tiles and disallow non-adjacent picks. Persist state. No matching yet.
2. Match detection + scoring: Implement `findMatches` (runs, columns ≥3). Remove matched tiles, award points, and mark empties. Ensure a swap that yields no match is rolled back.
3. Cascade resolution: Implement `settleGravity` and deterministic `refill` from the PRNG. Loop: while new matches exist, remove/score/settle/refill. Apply a combo multiplier per cascade step.
4. Replay + resume: Persist the move log and the starting seed. Provide a replay viewer that reconstructs the entire cascade sequence deterministically from (seed + swap list). Show saved games and resume in-progress.

## What the student types
- `findMatches(board): Match[]` – identifies horizontal/vertical runs.
- `settleGravity(board): Board` – compacts columns to fill empty cells.
- `refill(board, rng): Board` and `resolveTurn(board, swap, rng): { board, score }` – deterministic cascade loop.

## What this teaches that the shipped projects do not
- A multi-phase, deterministic scoring pass with a cascade loop and rollback of illegal moves, plus a seeded PRNG driving refills.
- Replay from (seed + actions) to prove determinism. Existing shipped work leans on lists/forms; this centers algorithmic state transitions.

## Out of scope
- Animations between cascade steps. Power-ups, special tiles, large boards. Online leaderboards and auth.

## Risks
- Avoiding infinite cascades on refill (seed and refill policy must not produce immediate forced loops). Ensuring every source of randomness is the seeded PRNG so replays and tests are stable.
