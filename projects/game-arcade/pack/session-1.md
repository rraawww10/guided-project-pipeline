# Session 1 - Seeded game + board scaffold

Time: 40 minutes
Students start from: a clean skeleton, Next dev server running, Prisma schema pushed and seed run
Students end with: create a game by seed, submit one guess, and see exactly one guess row on the board

What they learn
- Prisma: create rows for Game and Guess
- POST endpoints in Next route handlers
- Local UI state append to render a new row

Before you start
- Run the app: cd projects/game-arcade/app; npm ci; npx prisma db push --skip-generate; node prisma/seed.js; npm run dev
- Open these files side-by-side:
  - app/app/api/games/route.ts (POST /api/games)
  - app/app/api/games/[id]/guesses/route.ts (POST /api/games/:id/guesses)
  - app/app/page.tsx (the board UI)
- In the browser: open / and keep DevTools Console visible

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Frame the goal. Show the board UI scaffold and the stable testids. Point to the TODOs we will fill. |
| 5-12 | Live-code cut-ep-games-create-save: create a Game from a numeric seed; return { id, seed } with 201. Test with curl or the page. |
| 12-20 | Live-code cut-ep-guesses-create-save: save a Guess with posted code; return it with black/white null. Post once to see JSON. |
| 20-28 | Live-code cut-ui-append-guess: append the saved guess to guessesState so one row appears. Submit once on the page. |
| 28-35 | Wire the New Game flow on the page: type a seed, click New Game, pick 4 colours, Submit Guess. Verify exactly 1 row renders. |
| 35-38 | Students finish their wiring; you circulate and unblock. |
| 38-40 | Recap what runs now and preview scoring next. |

Cut points in this session

### cut-ep-games-create-save - app/api/games/route.ts:6
- What students see: `// TODO(cut-ep-games-create-save): Insert a new Game with the provided numeric \`seed\`, set \`body\` to the created { id, seed }, and set \`status\` to 201`
- What they write: parse JSON body to get seed:number; use prisma.game.create({ data: { seed } }); assign body to { id, seed } and status to 201.
- Teach it like this: Treat the handler as a tiny controller: read input, write the DB, shape the response. Keep the only return outside the markers; set body and status inside.
- Passes when: c-1-1 goes green.

### cut-ep-guesses-create-save - app/api/games/[id]/guesses/route.ts:34
- What students see: `// TODO(cut-ep-guesses-create-save): Persist a Guess row for the game id from the path using the request's 4-number \`code\`, leaving its black/white null, then place the saved guess into \`body\` and set \`status\` to 201`
- What they write: read code:number[4] from JSON; prisma.guess.create({ data: { gameId: id, code: JSON.stringify(code), black: null, white: null } }); set body to a plain object with parsed numbers; status 201.
- Teach it like this: Persist exactly what the client sent; we do not score yet. SQLite stores code as a JSON string, so stringify on write and JSON.parse back to numbers on the way out.
- Passes when: c-1-2 goes green.

### cut-ui-append-guess - app/page.tsx:83
- What students see: `// TODO(cut-ui-append-guess): Append the just-submitted 4-number code to \`guessesState\` so a new guess row appears on the board`
- What they write: setGuessesState((prev) => [...prev, saved]). Do not refetch the game here; rely on this append to show the row.
- Teach it like this: Show the state change causing the render. A refetch would make this block toothless; mutation checks that removing it would break the UI.
- Passes when: c-1-3 goes green.

Where students get stuck
- "It returns 200, not 201" - Wrong status. Set status to 201 inside the block before the return.
- "Prisma error P2025/not found" - The guesses POST uses the path id. Ensure the id exists (create a game first) and you did not hard-code an id.
- "The row flashes then disappears" - You refetched the game after submit, wiping the local append. Remove the refetch; this block owns the immediate UI update.
- "The colours are wrong in the row" - You returned strings for code. Parse numbers when shaping the response.

Check before moving on
- From the UI: type a seed, click New Game, click four picker buttons (e.g. 0,1,2,3), click Submit Guess. Exactly one row appears with four coloured slots matching your clicks.
