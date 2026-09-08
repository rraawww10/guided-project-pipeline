# Mastermind with Deterministic Scoring and Replay

**One line:** Classic Mastermind: a seeded secret code, peg-based guesses with exact/colour-only feedback, a simple deterministic solver hint, and full replay from SQLite.

## Theme
A compact, discrete deduction game: each turn is a single submission with an immediate, purely algorithmic score. Randomness exists only in the initial secret and is seeded, so every game id reproduces the same code and the same hint suggestions. Great for teaching pure scoring functions and replay logs.

## Sessions
1. Scaffold + seed + UI: Prisma models (Game with `seed`, Guess). Render a peg picker (4 slots × 6 colours), show previous guesses, and persist submissions. Generate the secret from a seeded PRNG; no feedback yet.
2. Scoring: Implement `scoreGuess(secret, guess): { black: number; white: number }` that counts exact matches and colour-only matches without double counting. Display pegs per row.
3. Deterministic hint: Maintain the set of remaining possible codes given the history; implement `nextCandidate(guesses)` that returns a single valid candidate using a fixed ordering (e.g., lexicographic). Show remaining count and the suggested next guess.
4. Replay + resume: Reconstruct any game from (seed + guesses) and step through turns. List saved games, resume in-progress ones, and branch a new line of play from any earlier guess.

## What the student types
- `scoreGuess(secret, guess): { black: number; white: number }` – exact and colour-only scoring with correct accounting.
- `filterCandidates(guesses): Code[]` – reduces the 6^4 space to those consistent with all past scores.
- `nextCandidate(guesses): Code | null` – deterministic choice of the next hint from the candidate set.

## What this teaches that the shipped projects do not
- Pure scoring and constraint filtering over a small finite space, plus a deterministic hint mechanism and full replay – distinct from list-and-form apps.
- Seeded PRNG use and durable logs with Prisma/SQLite.

## Out of scope
- Optimal solvers (Knuth 5-guess), animations, online play, auth. Variable code length/colour count beyond a small fixed set.

## Risks
- Getting scoring right (especially avoiding double-counting whites). Candidate filtering must be efficient and deterministic; stable ordering is key for reproducible hints and tests.
