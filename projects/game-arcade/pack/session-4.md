# Session 4 - Replay, list, resume, and branch

Time: 40 minutes
Students start from: hint working on the board; scores render; one or more games exist
Students end with: /games lists saved games with counts; Resume navigates to the board; Branch Here creates a new game with k copied guesses and shows k rows

What they learn
- Index endpoint that returns summaries with counts
- Navigation to resume a game by id
- Server-side branching: copy the first k guesses into a new game

Before you start
- Seed a couple of games and guesses so /games is non-empty
- Open these files:
  - app/app/api/games/route.ts (GET /api/games index)
  - app/app/games/page.tsx (games list UI)
  - app/app/api/games/[id]/branch/route.ts (branching endpoint)
  - app/app/page.tsx (Branch Here button wiring)

The plan
| Minutes | What you do |
|---|---|
| 0-6 | Recap list + resume + branch goals. Clarify row ordering and 1-based k. |
| 6-12 | Live-code cut-ep-games-list: read all games with their guess counts; shape [{ id, seed, guessCount }]. Show JSON. |
| 12-18 | Live-code cut-ui-games-fetch: fetch index → gamesState; /games renders one row per game. |
| 18-24 | Live-code cut-ui-resume-select: Resume navigates to /?game=<id>; show the board with correct rows. |
| 24-31 | Live-code cut-ep-games-branch: create a new Game with the same seed; copy the first k guesses including black/white; return { id, seed } 201. |
| 31-36 | Live-code cut-ui-branch-here: call branch, set currentGameId to new id, navigate; verify exactly k rows appear. |
| 36-38 | Students branch from different rows; you circulate. |
| 38-40 | Wrap-up: replay story and reproducibility, and where to extend. |

Cut points in this session

### cut-ep-games-list - app/api/games/route.ts:18
- What students see: `// TODO(cut-ep-games-list): Read all games with their guess counts and assign an array of { id, seed, guessCount } to \`body\` with status 200`
- What they write: prisma.game.findMany({ include: { _count: { select: { guesses: true } } }, orderBy: { createdAt: 'asc' } }); map to { id, seed, guessCount }.
- Teach it like this: A summary endpoint shapes exactly what the UI needs; include a count to avoid a second query per row.
- Passes when: c-4-1 goes green.

### cut-ui-games-fetch - app/games/page.tsx:16
- What students see: `// TODO(cut-ui-games-fetch): Fetch the games index and write the received array into \`gamesState\` so one row renders per game`
- What they write: setGamesState(responseArray).
- Teach it like this: Keep the UI dumb; it renders whatever array you give it with data-testid="game-row" for each.
- Passes when: c-4-2 goes green.

### cut-ui-resume-select - app/games/page.tsx:27
- What students see: `// TODO(cut-ui-resume-select): On a Resume button click, set \`currentGameId\` to that game's id and navigate to the board so its guesses load`
- What they write: push to `/?game=<id>` using router. The board page reads ?game=... and loads guesses.
- Teach it like this: Single-page app navigation; state lives on the board page keyed by game id.
- Passes when: c-4-3 goes green.

### cut-ep-games-branch - app/api/games/[id]/branch/route.ts:10
- What students see: `// TODO(cut-ep-games-branch): Create a new Game with the same seed as the source, copy the first \`upto\` guesses into it (including black/white), place the new { id, seed } into \`body\` and set \`status\` to 201`
- What they write: create new game with src.seed; slice the first k guesses; copy each with code, black, white; respond with { id, seed } 201.
- Teach it like this: Branching is replay-to-k: do not rescore; copy the stored numbers so replay is faithful.
- Passes when: c-4-4 goes green.

### cut-ui-branch-here - app/page.tsx:103
- What students see: `// TODO(cut-ui-branch-here): After Branch Here is clicked for row k, call the branch endpoint and set \`currentGameId\` to the returned game's id so the board reloads to k rows`
- What they write: fetch POST /api/games/:id/branch { upto:k }, setCurrentGameId(newId), navigate to /?game=newId.
- Teach it like this: The button carries k (1-based). After branching, reload the board for the new id; rows are ordered oldest-first.
- Passes when: c-4-5 goes green.

Where students get stuck
- "Resume shows the wrong number of rows" - You navigated without the ?game param. Push to /?game=<id>; the board reads it on mount.
- "Branch copies k+1 rows" - You treated k as 0-based index; k is a 1-based count including the clicked row. Slice(0, k).
- "Game list is empty" - You never set gamesState; ensure the fetch resolves and you write the parsed array into state.
- "List order is confusing" - We order by createdAt ascending here because row indexes on the board are 1-based oldest-first; keep that consistent when explaining.

Check before moving on
- /games renders one row per saved game. Resume navigates to the board with the correct row count. Branch Here for row k creates a new game whose board shows exactly k rows.
