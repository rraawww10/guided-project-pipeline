Troubleshooting - game-arcade

Real errors students hit, their causes, and what to say. Keep this open while circulating.

Setup and environment
- "Prisma error: P1001 cannot reach database" - The SQLite file and schema are not created. From app/: run `npx prisma db push --skip-generate` then `node prisma/seed.js`. postinstall already ran `prisma generate`.
- "TypeError: next is not found / command not found" - node_modules missing. Run `npm ci` in app/.

Session 1
- Symptom: POST /api/games returns 200 not 201. Cause: status left at default. Fix: set `status = 201` inside cut-ep-games-create-save before the return.
- Symptom: The guess row flashes then disappears. Cause: You refetched the game after submit; that overwrote the local append. Fix: In app/app/page.tsx, rely on the `setGuessesState((prev) => [...prev, saved])` append and do not immediately refetch.
- Symptom: The row shows the wrong colours or strings. Cause: You returned strings for `code`. Fix: When shaping the response, parse numbers (see how GET /games/:id maps JSON.parse(...).map(Number)).
- Symptom: 404 on POST /api/games/:id/guesses. Cause: Using a non-existent id. Fix: Create a game first or use the seeded `seed-game-1`.

Session 2
- Symptom: Whites undercount on repeated colours. Cause: Subtracting black per colour while accumulating. Fix: Sum min(freq_secret[c], freq_guess[c]) for all c, then `white = total - black` once at the end.
- Symptom: All rows show black=0 white=0. Cause: Never computed or saved the score. Fix: In cut-ep-score-on-submit, derive secret from seed, call scoreGuess, and persist those numbers.
- Symptom: UI shows empty scores. Cause: Returning nulls in S2. Fix: Ensure POST sets numeric black/white; GET then echoes numbers.

Session 3
- Symptom: Remaining is 1296 even after guesses. Cause: filterCandidates ignored history or compared only one of the fields. Fix: For each candidate, require BOTH s.black === g.black AND s.white === g.white for every g in history.
- Symptom: Suggestion differs between runs or machines. Cause: No deterministic ordering. Fix: Sort candidates lexicographically before picking the first.
- Symptom: UI still shows null suggestion. Cause: hintState never set. Fix: In cut-ui-hint-fetch, `setHintState(body)` after a successful GET.

Session 4
- Symptom: /games stays empty. Cause: State never set. Fix: In cut-ui-games-fetch, assign the parsed array to gamesState.
- Symptom: Resume opens the board but rows are wrong. Cause: Pushed to `/games/:id` or set state on the list page. Fix: Navigate to `/?game=<id>`; the board page owns loading by id.
- Symptom: Branch copies the wrong number of rows. Cause: Off-by-one on k. Fix: k is 1-based and includes the clicked row; copy the first k guesses (slice(0, k)).

Gotchas from earlier rounds
- Waiting for the UI: tests wait for element states; avoid adding arbitrary timeouts. Ensure your UI updates are synchronous with state sets shown in the guide.
- Determinism: the hint must be reproducible. Sort candidates before picking.
- State vs refetch: Do not refetch after submit in S1; let the append own the immediate row. The code comments in app/app/page.tsx explain why this matters for grading.
