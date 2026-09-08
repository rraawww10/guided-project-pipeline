# Ambiguity report - game-arcade

**Verdict:** 3 blocking, 5 worth a look

## Blocking
### A1 - POST /guesses returns null vs scored fields across sessions
- **Where:** spec.md c-1-2 vs c-2-2/c-2-3; spec.json c-1-2 vs c-2-2/c-2-3
- **Owner:** test-runner
- **The line:** "c-1-2: POST /api/games/:id/guesses with body { code: [0,1,2,3] } returns 201 JSON Guess whose code equals the body and black/white are null (no scoring yet)."
- **Reading one:** The POST always returns a Guess with black/white = null (as per Session 1), and scoring only appears on GET later.
- **Reading two:** The same POST returns a Guess with computed black/white numbers (as per Session 2's c-2-2 and c-2-3) in the final app.
- **Why it matters:** The suite runs all sessions against one final app. Both readings cannot be true simultaneously; one session's criterion will fail no matter how the Builder implements the endpoint, and the loop cannot converge.
- **Suggested wording:** Make the Session 1 criterion avoid pinning nulls and defer scoring semantics to Session 2, e.g. "returns 201 with a JSON Guess echoing the posted code"; Session 2 then states the scored response.

### A2 - Branching index k and row indexing are unstated
- **Where:** spec.md, Session 4, criteria c-4-4 and c-4-5
- **Owner:** test-runner
- **The line:** "POST /api/games/:id/branch with body { upto: k } returns 201 with a new Game; GET that game shows exactly k guesses copied from the source." / "After Branch Here is clicked for row k, the page renders exactly k guess rows"
- **Reading one:** k is a count (1-based): clicking the 1st row branches to 1 guess; clicking the 3rd row branches to 3 guesses, regardless of whether rows are 0- or 1-indexed in their DOM ids.
- **Reading two:** k is a 0-based row index: clicking row 3 (data-testid="guess-row-3") copies 4 guesses, i.e. index + 1, or alternatively copies guesses up to but not including that row.
- **Why it matters:** The UI ids use <n> but the spec never fixes the list's order or whether <n> is 0- or 1-based. Endpoint behavior and UI wiring can both be implemented plausibly yet disagree with the tests' chosen convention.
- **Suggested wording:** State both the list order and the convention explicitly, e.g. "Rows are ordered from the start of the game (oldest first). The k in { upto: k } and in branch-here-<k> is a 1-based count including the clicked row."

### A3 - cut-ui-append-guess can be made toothless by a refetch
- **Where:** spec.md, Session 1, cut-ui-append-guess (and Session 2 sc-play rendering from saved guesses)
- **Owner:** mutation
- **The line:** "Hint: Append the just‑submitted 4‑number code to `guessesState` so a new guess row appears on the board."
- **Reading one:** The board updates by appending client state after POST; no immediate refetch occurs, so removing this cut leaves the row absent and a criterion fails.
- **Reading two:** The page refetches the game (or list) right after submit and re-renders from saved guesses, so removing the append has no observable effect and every criterion still passes.
- **Why it matters:** A cut that can be left empty while all criteria stay green ships broken grading. Mutation would report this as NOT GRADED and no later step can repair it.
- **Suggested wording:** Pin the update path: e.g. "Do not refetch after submit; update the UI by appending to `guessesState` and rely on the next navigation to reload from the server" (or explicitly require the refetch and remove the append task).

## Worth a look
### W1 - xorshift32 variant and seed edge cases are not fully specified
- **Where:** spec.md, Data model → Notes (secret generation)
- **Owner:** test-runner
- **The line:** "Secret generation is fixed: start from `Game.seed` as a 32‑bit unsigned integer, run xorshift32, and map each successive output to 0..5 by `output % 6`; the first 4 values form the secret."
- **Reading one:** Use Marsaglia xorshift32 with shifts (13, 17, 5), treat seed as `seed >>> 0`, and if seed is 0, substitute 1 to avoid the all-zero stream.
- **Reading two:** Any xorshift32 variant is acceptable (different shift triplets or zero allowed), producing a different secret for the same seed.
- **Why it matters:** The tests will compute a specific secret from a seed; a different variant or seed-0 handling will desync every score and hint expectation.
- **Suggested wording:** "Use Marsaglia xorshift32 with shifts (13,17,5). Initialize `state = (seed >>> 0) || 1` and after each step take `state % 6`."

### W2 - UI hint formatting is unspecified
- **Where:** spec.md, Session 3, c-3-3 (sc-play)
- **Owner:** test-runner
- **The line:** "the page shows the remaining count (data-testid=\"hint-remaining\") and a suggested 4‑number guess (data-testid=\"hint-suggestion\")."
- **Reading one:** The suggestion renders as a JSON-like string "[0,0,0,0]".
- **Reading two:** It renders as four tokens (e.g. "0 0 0 0" or coloured pegs) with no brackets or commas.
- **Why it matters:** Without a pinned text format or hook per digit, a test author cannot write a stable assertion.
- **Suggested wording:** "Render the suggestion as the exact string "[a,b,c,d]" (e.g. "[0,0,0,0]") inside hint-suggestion."

### W3 - Guess row ordering is unstated
- **Where:** spec.md, Screens → sc-play (prior guess rows)
- **Owner:** test-runner
- **The line:** "prior guess rows (data-testid=\"guess-row-<n>\")"
- **Reading one:** Rows render oldest-first (from the start of the game).
- **Reading two:** Rows render most-recent-first.
- **Why it matters:** Tests that click "branch-here-<n>" or read row counts alongside indexes must assume one; the spec does not state which. No criterion currently asserts order, but later interactions (branching) depend on it.
- **Suggested wording:** "Render rows in chronological order from the first guess to the most recent (oldest first)."

### W4 - Game list ordering is unstated
- **Where:** spec.md, Session 4, c-4-2 (sc-games)
- **Owner:** test-runner
- **The line:** "the list renders one row per saved game (data-testid=\"game-row\")"
- **Reading one:** Order by createdAt descending (most recent first).
- **Reading two:** Order by createdAt ascending or by id (database default).
- **Why it matters:** If any test reads a specific row by position, the outcome depends on ordering; the spec is silent. If tests assert only counts, this is harmless but worth pinning for consistency.
- **Suggested wording:** "Order the list by createdAt descending (most recent first)."

### W5 - White-peg subtraction could be read per-colour or total
- **Where:** spec.md, Session 2, cut-score-count-white (hint)
- **Owner:** test-runner
- **The line:** "for each colour 0..5, add the minimum of its frequency in secret and in guess, then subtract `black`."
- **Reading one:** Compute total min-frequency across colours and subtract the total black count once at the end.
- **Reading two:** Subtract the black count per-colour while accumulating, which can undercount when multiple blacks exist.
- **Why it matters:** Different readings give different whites on repeated-colour cases; only one matches Mastermind's rules.
- **Suggested wording:** "Let total = Σ_c min(freq_secret[c], freq_guess[c]); set `white = total - black`."