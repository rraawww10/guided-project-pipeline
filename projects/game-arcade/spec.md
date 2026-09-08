## Outcome
A visual Mastermind game with a seeded secret code, peg-based guesses, exact/colour-only scoring, a deterministic hint, and a replay/resume flow backed by Prisma + SQLite. The board lives on one interactive page: pick colours, submit a 4‑peg guess, see black/white pegs per row, view a hint (remaining candidates + suggested next guess), and branch a new line of play from any earlier turn. Games are durable and reproducible from their seed.

## Out of scope
- Optimal solvers (e.g., Knuth 5‑guess), animations, online play, auth.
- Variable code length or colour count beyond the fixed 4 slots × 6 colours.
- Any network calls to third‑party services; everything is local and seeded.

## Data model
- Game
  - id: string (cuid)
  - seed: number (int)
  - createdAt: datetime
- Guess
  - id: string (cuid)
  - gameId: string (FK → Game)
  - code: number[4] (each 0..5)
  - black: number | null (exact position matches)
  - white: number | null (colour‑only matches without double counting)

Notes
- Secret generation is fixed: start from `Game.seed` as a 32‑bit unsigned integer, run xorshift32, and map each successive output to 0..5 by `output % 6`; the first 4 values form the secret. The secret is NOT stored; it is derived as needed.
- Replaying from `seed + guesses` yields the same secret and scores.
- API responses use these shapes:
  - Game: { id, seed }
  - Guess: { id, gameId, code: number[4], black: number|null, white: number|null }
  - GameWithGuesses: { id, seed, guesses: Guess[] }
  - Hint: { remaining: number, suggestion: number[] | null }
  - GameSummary: { id, seed, guessCount: number }

## Endpoints
- ep-games-create: POST /api/games → 201 JSON Game
- ep-games-get: GET /api/games/:id → 200 JSON GameWithGuesses
- ep-guesses-create: POST /api/games/:id/guesses → 201 JSON Guess
- ep-hint-get: GET /api/games/:id/hint → 200 JSON Hint
- ep-games-list: GET /api/games → 200 JSON GameSummary[]
- ep-games-branch: POST /api/games/:id/branch → 201 JSON Game (new branched game)

## Screens
- sc-play (route "/")
  - Elements: seed input (data-testid="seed-input"), New Game button (data-testid="new-game"), colour picker buttons (data-testid="picker-color-0".."picker-color-5"), four guess slots (data-testid="slot-0".."slot-3"), Submit Guess button (data-testid="submit-guess"), prior guess rows (data-testid="guess-row-<n>"), per‑row score badges (data-testid="score-black" and "score-white"), hint remaining (data-testid="hint-remaining"), hint suggestion (data-testid="hint-suggestion"), Branch Here buttons next to each prior row (data-testid="branch-here-<n>").
- sc-games (route "/games")
  - Elements: saved games list with rows (data-testid="game-row"), each showing id and guessCount, Resume buttons (data-testid="resume-<id>").

## Sessions

### Session 1 - Seeded game + board scaffold
Goal: Create and fetch a game by seed, submit and persist a guess, and render the guess row on the board.

Teaches: prisma models, POST endpoint, state append

Builds: ep-games-create, ep-guesses-create, sc-play

Acceptance criteria
- c-1-1: POST /api/games returns 201 with a JSON Game that echoes the provided numeric seed and a non-empty id. Target: ep-games-create. Cuts: [cut-ep-games-create-save].
- c-1-2: POST /api/games/:id/guesses with body { code: [0,1,2,3] } returns 201 JSON Guess whose code equals the body and black/white are null (no scoring yet). Target: ep-guesses-create. Cuts: [cut-ep-guesses-create-save].
- c-1-3: On sc-play, after creating a game and submitting one guess, the page renders exactly 1 guess row (data-testid^="guess-row-") and shows 4 peg slots reflecting the chosen colours. Target: sc-play. Cuts: [cut-ui-append-guess].

Cuts
- cut-ep-games-create-save (app/api/games/route.ts) writes_into: body
  - Hint: Insert a new Game with the provided numeric `seed`, set `body` to the created { id, seed }, and set `status` to 201.
- cut-ep-guesses-create-save (app/api/games/[id]/guesses/route.ts) writes_into: body
  - Hint: Persist a Guess row for the game id from the path using the request's 4‑number `code`, leaving its black/white null, then place the saved guess into `body` and set `status` to 201.
- cut-ui-append-guess (app/page.tsx) writes_into: guessesState
  - Hint: Append the just‑submitted 4‑number code to `guessesState` so a new guess row appears on the board.

---

### Session 2 - Exact and colour-only scoring
Goal: Implement Mastermind scoring and return per‑row black/white pegs, rendered on the board.

Teaches: pure functions, avoiding double counting, enriching a POST response

Builds: ep-games-get

Acceptance criteria
- c-2-1: GET /api/games/:id returns 200 with JSON { id, seed, guesses: [] } for a new game. Target: ep-games-get. Cuts: [].
- c-2-2: POST /api/games/:id/guesses with a guess equal to the secret returns 201 with black = 4 and white = 0 in JSON Guess. Target: ep-guesses-create. Cuts: [cut-score-count-black, cut-ep-score-on-submit].
- c-2-3: For a guess containing all secret colours but permuted, the same POST returns black = 0 and white = 4. Target: ep-guesses-create. Cuts: [cut-score-count-white, cut-ep-score-on-submit].
- c-2-4: GET /api/games/:id returns 200 with guesses[] items carrying numeric black and white fields for prior submissions. Target: ep-games-get. Cuts: [cut-score-count-black, cut-score-count-white, cut-ep-score-on-submit].
- c-2-5: On sc-play, each rendered guess row shows its black count in data-testid="score-black" and white count in data-testid="score-white" matching the API. Target: sc-play. Cuts: [cut-ui-render-scores].

Cuts
- cut-score-count-black (lib/scoring.ts) writes_into: black
  - Hint: Count exact matches into `black` by comparing secret and guess at the same index for all 4 slots.
- cut-score-count-white (lib/scoring.ts) writes_into: white
  - Hint: Count colour‑only matches into `white` without double counting: for each colour 0..5, add the minimum of its frequency in secret and in guess, then subtract `black`.
- cut-ep-score-on-submit (app/api/games/[id]/guesses/route.ts) writes_into: score
  - Hint: After loading the Game's secret from its seed, compute the guess's black/white using the scoring function, assign the result to `score`, and include those numbers when saving and in the response.
- cut-ui-render-scores (app/page.tsx) writes_into: rows
  - Hint: Build `rows` from the saved guesses so each row renders the 4 pegs and shows the row's black and white counts in their testids.

---

### Session 3 - Deterministic hint and remaining candidates
Goal: Show the count of candidates consistent with the history and a deterministic next guess.

Teaches: constraint filtering over a finite space, deterministic ordering, client fetch for a computed hint

Builds: ep-hint-get, sc-games

Acceptance criteria
- c-3-1: With no guesses, GET /api/games/:id/hint returns 200 with remaining = 1296 and suggestion = [0,0,0,0]. Target: ep-hint-get. Cuts: [cut-filter-candidates, cut-next-candidate, cut-ep-hint-build].
- c-3-2: After recording one guess and its score, GET /api/games/:id/hint returns a remaining count that matches the set consistent with that history. Target: ep-hint-get. Cuts: [cut-filter-candidates, cut-ep-hint-build].
- c-3-3: On sc-play, the page shows the remaining count (data-testid="hint-remaining") and a suggested 4‑number guess (data-testid="hint-suggestion"). Target: sc-play. Cuts: [cut-ui-hint-fetch].
- c-3-4: Two separate games with identical guess histories produce the same suggestion string from GET /api/games/:id/hint. Target: ep-hint-get. Cuts: [cut-next-candidate, cut-ep-hint-build].

Cuts
- cut-filter-candidates (lib/candidates.ts) writes_into: candidates
  - Hint: From the 6^4 search space, keep only those codes in `candidates` whose score against each recorded guess equals that guess's stored black/white.
- cut-next-candidate (lib/candidates.ts) writes_into: suggestion
  - Hint: Choose the deterministic next guess as the lexicographically first code from the candidate set and assign it to `suggestion`, or null when the set is empty.
- cut-ep-hint-build (app/api/games/[id]/hint/route.ts) writes_into: body
  - Hint: Load the game's guesses, compute the remaining candidate set and a deterministic next guess, and place { remaining, suggestion } into `body` with status 200.
- cut-ui-hint-fetch (app/page.tsx) writes_into: hintState
  - Hint: Fetch the hint endpoint for the active game and write its { remaining, suggestion } into `hintState` for display.

---

### Session 4 - Replay, list, resume, and branch
Goal: List saved games, resume any game, step from earlier turns by branching a new game that replays to that point.

Teaches: index endpoint, server branching

Builds: ep-games-list, ep-games-branch

Acceptance criteria
- c-4-1: GET /api/games returns 200 with an array of GameSummary, each carrying id, seed, and guessCount. Target: ep-games-list. Cuts: [cut-ep-games-list].
- c-4-2: On /games, the list renders one row per saved game (data-testid="game-row") showing its id and guessCount. Target: sc-games. Cuts: [cut-ui-games-fetch].
- c-4-3: Clicking Resume on a saved game shows the board with the correct number of guess rows for that game. Target: sc-games. Cuts: [cut-ui-resume-select].
- c-4-4: POST /api/games/:id/branch with body { upto: k } returns 201 with a new Game; GET that game shows exactly k guesses copied from the source. Target: ep-games-branch. Cuts: [cut-ep-games-branch].
- c-4-5: On sc-play, after clicking the Branch Here button for row k, the page renders exactly k guess rows (elements with data-testid^="guess-row-"). Target: sc-play. Cuts: [cut-ui-branch-here].

Cuts
- cut-ep-games-list (app/api/games/route.ts) writes_into: body
  - Hint: Read all games with their guess counts and assign an array of { id, seed, guessCount } to `body` with status 200.
- cut-ui-games-fetch (app/games/page.tsx) writes_into: gamesState
  - Hint: Fetch the games index and write the received array into `gamesState` so one row renders per game.
- cut-ui-resume-select (app/games/page.tsx) writes_into: currentGameId
  - Hint: On a Resume button click, set `currentGameId` to that game's id and navigate to the board so its guesses load.
- cut-ep-games-branch (app/api/games/[id]/branch/route.ts) writes_into: body
  - Hint: Create a new Game with the same seed as the source, copy the first `upto` guesses into it (including black/white), place the new { id, seed } into `body` and set `status` to 201.
- cut-ui-branch-here (app/page.tsx) writes_into: currentGameId
  - Hint: After Branch Here is clicked for row k, call the branch endpoint and set `currentGameId` to the returned game's id so the board reloads to k rows.
