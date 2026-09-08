# Mastermind Arcade – Seeded, Scored, and Replayed

## Outcome
A visual Mastermind you can show to a friend: pick four coloured pegs, submit a guess, and see black/white feedback instantly. Every game is reproducible from its numeric seed, scoring is deterministic and pure, a simple solver suggests the next guess, and all games persist to SQLite so you can list, resume, and replay any run.

## Out of scope
- Optimal solvers (e.g., Knuth 5‑guess), animations, sounds, online play, authentication.
- Variable code length or colour count; this project fixes 4 slots and 6 colours.
- External services or network calls beyond the app’s own API.

## Data model
- Code: a 4‑tuple of colour ids, each an integer in 0..5. The UI renders six fixed colours.
- Game
  - id: string (uuid)
  - seed: number (non‑negative integer)
  - createdAt: DateTime
  - status: 'in_progress' | 'won'
- Guess
  - id: string (uuid)
  - gameId: string -> Game
  - turn: integer (1..)
  - code: number[4]
  - black: integer (0..4)
  - white: integer (0..4)
  - createdAt: DateTime

Deterministic secret from seed (no RNG calls at run time):
- secretFromSeed(seed: number): Code
- Definition: write seed in base‑6, least‑significant digit first. secret[i] = floor(seed / 6^i) % 6 for i = 0,1,2,3. This fixes the secret as a pure function of the stored seed.

Scoring:
- scoreGuess(secret, guess) produces { black, white } where
  - black is the count of i where secret[i] == guess[i]
  - white is the count of colour‑only matches after removing all exact matches so no peg is counted twice

Lexicographic order over codes:
- Treat codes as 4‑digit base‑6 numbers [d0,d1,d2,d3]. Lexicographic ascending compares d0, then d1, then d2, then d3.

## Endpoints
- POST /api/games (ep-game-create)
  - Request: { seed?: number }
  - Response: { id: string; seed: number }
  - Status: 201
- GET /api/games/[id] (ep-game-detail)
  - Request: none
  - Response: { id: string; seed: number; guesses: { turn: number; code: number[]; black: number; white: number }[] }
  - Status: 200
- POST /api/games/[id]/guesses (ep-guess-create)
  - Request: { code: number[4] }
  - Response: { id: string; turn: number; code: number[]; black: number; white: number }
  - Status: 201
- GET /api/games (ep-games-list)
  - Request: none
  - Response: { id: string; seed: number; guessCount: number; status: string }[]
  - Status: 200
- GET /api/games/[id]/hint (ep-hint)
  - Request: none
  - Response: { remaining: number; suggested: number[] | null }
  - Status: 200

## Screens
- sc-board (route: /game/[id])
  - Elements: peg picker (6 colours × 4 slots), Submit button, previous guesses list (one row per guess), per‑row feedback pegs, "Hint:" text with suggested code, "Remaining N", replay control (Turn slider), Branch button per row.
  - States: empty (no guesses), loaded (guesses present), with‑feedback, hint‑visible, replay‑stepped.
- sc-games (route: /games)
  - Elements: saved games list (id, seed, guessCount), Resume link per game.
  - States: empty (no games), loaded.

## Sessions

### Session 1 - Seeded game + board UI
Goal: Persist games and guesses with Prisma, render the board, and submit guesses (feedback comes in session 2).

Teaches: Prisma models, Next route handlers, seed‑based reproducibility, React controlled state, list rendering.

Builds: ep-game-create, ep-game-detail, ep-guess-create, sc-board

Acceptance criteria:
- c-1-1: POST /api/games returns 201 with a JSON object containing id (string) and seed (number). Target: ep-game-create
- c-1-2: GET /api/games/[id] on a fresh game returns 200 with guesses as an empty array. Target: ep-game-detail
- c-1-3: Screen sc-board lets a player pick four colours and Submit; after submitting once, the page shows one new guess row with four coloured pegs. Target: sc-board; cuts: [cut-ui-build-guess-payload, cut-ep-guess-create-persist]
- c-1-4: POST /api/games/[id]/guesses with a 4‑number code returns 201 with a JSON object whose code matches the body and includes a turn number. Target: ep-guess-create; cuts: [cut-ep-guess-create-persist]

Cut points:
- cut-ui-build-guess-payload (app/game/[id]/page.tsx) writes_into: payload
  - Hint: Write the four currently selected colour ids into `payload` as { code: [d0,d1,d2,d3] } in slot order so the body you POST holds exactly those four numbers.
- cut-ep-guess-create-persist (app/api/games/[id]/guesses/route.ts) writes_into: created
  - Hint: Create the Guess for this game by writing the posted 4‑number code into `created` with the next turn number, then let the handler answer 201 with it.

### Session 2 - Scoring and feedback pegs
Goal: Score guesses deterministically and show black/white pegs per row.

Teaches: Pure functions, exact vs colour‑only matches, avoiding double counting, UI feedback mapping.

Builds: (adds logic only; endpoints and sc-board exist)

Acceptance criteria:
- c-2-1: POSTing the exact secret for a game (computed by secretFromSeed) produces black=4 and white=0 on the last row in GET /api/games/[id]. Target: ep-guess-create; cuts: [cut-lib-score-black]
- c-2-2: After submitting a rotation of the secret (no positions match), GET /api/games/[id] returns 200 and the last guess shows black=0 and white=4. Target: ep-guess-create; cuts: [cut-lib-score-white]
- c-2-3: When the secret has repeats, after submitting a suitable guess, GET /api/games/[id] returns 200 and the last guess shows black+white equal to the count of matching colours after removing exact matches (no white double‑counting). Target: ep-guess-create; cuts: [cut-lib-score-black, cut-lib-score-white]
- c-2-4: On sc-board, each guess row renders the feedback as the exact number of black pegs and white pegs matching its stored black and white. Target: sc-board; cuts: [cut-ui-render-feedback]
- c-2-5: After two submissions, sc-board renders two rows (one per guess). Target: sc-board; cuts: [cut-ui-render-rows]

Cut points:
- cut-lib-score-black (lib/score.ts) writes_into: black
  - Hint: Set `black` to the count of positions i in 0..3 where secret[i] equals guess[i].
- cut-lib-score-white (lib/score.ts) writes_into: white
  - Hint: Set `white` to the count of colour‑only matches after removing all exact matches so no colour is counted twice.
- cut-ui-render-feedback (app/game/[id]/page.tsx) writes_into: feedback
  - Hint: Build `feedback` for the visible row with exactly the stored `black` black pegs and `white` white pegs.
- cut-ui-render-rows (app/game/[id]/page.tsx) writes_into: rows
  - Hint: Map the game’s stored guesses into `rows` with one entry per guess in most‑recent‑first order and keep the four colours for each row.

### Session 3 - Deterministic hint and remaining count
Goal: Filter the 6^4 code space against the history and suggest the next guess deterministically.

Teaches: Finite search space, constraint filtering with a pure function, deterministic ordering (lexicographic), fetching and rendering derived data.

Builds: ep-hint

Acceptance criteria:
- c-3-1: For a game with no guesses, GET /api/games/[id]/hint returns 200 with remaining = 1296. Target: ep-hint; cuts: [cut-lib-candidates-filter]
- c-3-2: For a game with no guesses, GET /api/games/[id]/hint suggests [0,0,0,0]. Target: ep-hint; cuts: [cut-lib-next-candidate]
- c-3-3: After submitting [0,0,0,0] to a game where it scores black=0 and white=0, GET /api/games/[id]/hint returns remaining = 625. Target: ep-hint; cuts: [cut-lib-candidates-filter]
- c-3-4: On sc-board after that zero‑score first guess, the page shows "Hint: 1 1 1 1 • Remaining 625". Target: sc-board; cuts: [cut-ui-show-hint]

Cut points:
- cut-lib-candidates-filter (lib/solver.ts) writes_into: out
  - Hint: Fill `out` with every 4‑long code from 0..5 whose score against each past guess equals that guess’s recorded black and white.
- cut-lib-next-candidate (lib/solver.ts) writes_into: out
  - Hint: Put the first code in lexicographic ascending order from `candidates` into `out`, or null when no candidates remain.
- cut-ui-show-hint (app/game/[id]/page.tsx) writes_into: hintText
  - Hint: Write the next hint code and remaining count into `hintText` as "Hint: d0 d1 d2 d3 • Remaining N".

### Session 4 - Replay, resume, and branch
Goal: List saved games, resume play, scrub through a game’s history, and branch a new line of play from any earlier turn.

Teaches: Index/list pages, navigation, replay scrubbing, branching via seed + prefix of guesses.

Builds: ep-games-list, sc-games

Acceptance criteria:
- c-4-1: GET /api/games returns 200 with a JSON array where each entry has id, seed, guessCount, and status. Target: ep-games-list
- c-4-2: Screen sc-games renders one row per saved game showing id, seed, and guessCount; clicking a row resumes that game at /game/[id]. Target: sc-games; cuts: [cut-ui-games-list-rows]
- c-4-3: On sc-board, moving the Turn control to K shows exactly K guess rows from the start of the game. Target: sc-board; cuts: [cut-ui-replay-apply]
- c-4-4: On sc-board, clicking "Branch from turn K" creates a new game with the same seed and replays the first K guesses into it; after navigation the board shows exactly K rows for the new game. Target: sc-board; cuts: [cut-ui-branch-build]

Cut points:
- cut-ui-replay-apply (app/game/[id]/page.tsx) writes_into: shownGuesses
  - Hint: Set `shownGuesses` to the first `step` guesses from the game’s history in order of play.
- cut-ui-branch-build (app/game/[id]/page.tsx) writes_into: batch
  - Hint: Populate `batch` with the codes of the first `step` guesses so the UI can POST them to the new game in order.
- cut-ui-games-list-rows (app/games/page.tsx) writes_into: rows
  - Hint: Produce one `rows` entry per saved game with its id, seed, and guessCount; newest first.
