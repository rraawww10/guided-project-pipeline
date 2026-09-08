# Ambiguity report - game-arcade

**Verdict:** 2 blocking, 5 worth a look

## Blocking
### A1 - What is “the last row” in GET /api/games/[id]?
- **Where:** spec.md, Session 2, criteria c-2-1 to c-2-3
- **Owner:** test-runner
- **The line:** "POSTing the exact secret for a game (computed by secretFromSeed) produces black=4 and white=0 on the last row in GET /api/games/[id]."
- **Reading one:** The endpoint returns guesses in order of play (turn ascending), so "last" means the most recent guess (the final element of the array).
- **Reading two:** The endpoint returns guesses newest-first (turn descending) or in an unspecified DB default order, so "last" could mean the oldest row, not the one just submitted.
- **Why it matters:** Tests that read "last" will assert against the wrong element if the array order differs. A builder must pick an order for the API and the UI, and the choice changes what the tests pin.
- **Suggested wording:** "GET /api/games/[id] returns guesses sorted by turn ASC (oldest first). The most recent guess is the final element of the guesses array, and tests assert against that element."

### A2 - ep-guess-create response shape in S1: are black/white present?
- **Where:** spec.md, Session 1, c-1-4; spec.json, endpoints[ep-guess-create].response
- **Owner:** test-runner
- **The line:** spec.md c-1-4: "POST /api/games/[id]/guesses with a 4‑number code returns 201 with a JSON object whose code matches the body and includes a turn number."
- **Reading one:** Follow spec.md literally for Session 1: return only id, turn and code (no black/white until scoring is built in Session 2).
- **Reading two:** Follow spec.json’s contract at all times: return id, turn, code, black and white even in Session 1 (likely zeros before scoring exists).
- **Why it matters:** The API contract differs between the two files. Picking either version changes what ships and which session’s tests fail first; a mismatch will bounce in the Builder/test loop.
- **Suggested wording:** "In Session 1, the ep-guess-create response MUST be { id, turn, code, black: 0, white: 0 }. From Session 2 onward, black/white reflect computed scores. spec.json reflects this shape."

## Worth a look
### W1 - What happens when POST /api/games omits seed?
- **Where:** spec.md, Endpoints, ep-game-create
- **Owner:** test-runner
- **The line:** "Request: { seed?: number }"
- **Reading one:** If seed is absent, the server generates a random seed at runtime and returns it.
- **Reading two:** If seed is absent, the server derives a deterministic default (e.g., 0 or from id) or rejects the request. No RNG is called at runtime.
- **Why it matters:** Reproducibility. Random generation can make manual runs differ between executions; a deterministic default can make every ad-hoc game identical unless the caller supplies a seed.
- **Suggested wording:** "If omitted, the server MUST choose a deterministic default (seed=0). Tests will always provide seed explicitly."

### W2 - UI list order vs replay prefix
- **Where:** spec.md, Session 2, cut-ui-render-rows hint; spec.md, Session 4, c-4-3
- **Owner:** test-runner
- **The line:** "Map the game’s stored guesses into `rows` with one entry per guess in most‑recent‑first order" and "moving the Turn control to K shows exactly K guess rows from the start of the game."
- **Reading one:** The UI always renders newest-first; when replaying to K, it still shows newest-first but only K rows.
- **Reading two:** Replay implies showing the first K guesses in order of play (oldest-first) while normal view is newest-first, so the display order changes between modes.
- **Why it matters:** Tests that assert sequences may fail if they assume the same order in both modes. Builders need a single stated order or an explicit statement that replay changes the ordering.
- **Suggested wording:** "Normal view: newest-first. Replay to K: show the first K guesses but still render newest-first."

### W3 - Games list sorting
- **Where:** spec.json, Session 4, cut-ui-games-list-rows hint
- **Owner:** test-runner
- **The line:** "newest first."
- **Reading one:** Only the UI sorts; the /api/games endpoint can return any order.
- **Reading two:** The endpoint itself is expected to return newest-first.
- **Why it matters:** If tests read the API directly (or rely on UI preserving API order), an unstated expectation about server-side order can flip assertions.
- **Suggested wording:** "The /api/games endpoint returns games sorted by createdAt DESC (newest first), and the UI preserves that order."

### W4 - Branch control label vs element name
- **Where:** spec.md, Screens (sc-board elements) and Session 4, c-4-4
- **Owner:** test-runner
- **The line:** Elements: "Branch button"; criterion: "clicking \"Branch from turn K\" creates a new game…"
- **Reading one:** The button’s visible text is exactly "Branch from turn K" as quoted.
- **Reading two:** The control is a generic branch button per row; the visible label can differ (e.g., an icon), and "Branch from turn K" is descriptive, not literal.
- **Why it matters:** Tests that query by exact text will fail if the label differs. If the intent is a specific string, say so.
- **Suggested wording:** "The per-row button’s text is exactly: Branch from turn K."

### W5 - Replay slider indexing (off-by-one)
- **Where:** spec.md, Session 4, c-4-3
- **Owner:** test-runner
- **The line:** "moving the Turn control to K shows exactly K guess rows from the start of the game."
- **Reading one:** K ranges from 0..N (K=0 shows no rows; K=N shows all rows).
- **Reading two:** K ranges from 1..N (K=1 shows the first row; there is no K=0).
- **Why it matters:** Off-by-one differences change test interactions and visible counts.
- **Suggested wording:** "K is 0..N inclusive. K=0 shows 0 rows; K=N shows all rows."
