Mastermind with Deterministic Scoring and Replay

One page for instructors. You can teach straight from this and the session guides without opening the final code. The spec is frozen; this matches the approved round.

What you build across 4 sessions
- Session 1: Seeded game + board scaffold. Create a game, submit a guess, show one row on the board.
- Session 2: Scoring. Exact (black) and colour-only (white) pegs; show per-row scores.
- Session 3: Deterministic hint. Show remaining candidates and the next suggested guess.
- Session 4: Replay + resume + branch. List games, resume, and branch a new game from any earlier row.

How to run locally
- Requirements: Node 18+, npm, SQLite (bundled), no external services.
- First run
  1) cd projects/game-arcade/app
  2) npm ci
     - postinstall runs prisma generate.
  3) npx prisma db push --skip-generate
  4) node prisma/seed.js
  5) npm run dev (or npm run build && npm start)
  6) Open http://localhost:3000/
- Useful routes
  - /           the board (sc-play)
  - /games      saved games (sc-games)
- Seed data: seed.js creates one game with id "seed-game-1" and seed 13579 to keep GET /api/games/:id testable in isolation.

Project structure you reference while teaching
- app/app/page.tsx            the board UI (sc-play)
- app/app/games/page.tsx      the saved games UI (sc-games)
- app/app/api/games/route.ts  POST /api/games and GET /api/games
- app/app/api/games/[id]/route.ts       GET one game with guesses
- app/app/api/games/[id]/guesses/route.ts  POST a guess (and in S2: scoring)
- app/app/api/games/[id]/hint/route.ts  GET deterministic hint
- app/app/api/games/[id]/branch/route.ts  POST branch
- app/lib/scoring.ts          xorshift secret + scoreGuess
- app/lib/candidates.ts       filterCandidates + nextCandidate
- app/lib/prisma.ts           Prisma client

Data model (Prisma)
- Game { id, seed, createdAt, guesses[] }
- Guess { id, gameId, code: JSON string, black: Int?, white: Int?, createdAt }

What the UI must show (stable hooks)
- sc-play: seed-input, new-game, picker-color-0..5, slot-0..3, submit-guess,
  guess-row-<n>, score-black, score-white, hint-remaining, hint-suggestion,
  branch-here-<n>
- sc-games: game-row, resume-<id>

Timing
- Each session plan totals 40 minutes. Session 1 carries setup cost; keep the pace tight there and use the pre-written fetch/UI scaffolds to stay on time.

When in doubt
- Read the session guide cut sections. Quote the TODO exactly and name the variable the block must write into (writes_into). Avoid live-coding anything outside the markers.
