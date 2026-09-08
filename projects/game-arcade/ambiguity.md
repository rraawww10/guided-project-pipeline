# Ambiguity report - game-arcade

**Verdict:** 4 blocking, 5 worth a look

## Blocking
### A1 - Xorshift32 not fully specified
- **Where:** spec.md, Data model → Notes
- **Owner:** test-runner
- **The line:** "Secret generation is fixed: start from `Game.seed` as a 32‑bit unsigned integer, run xorshift32, and map each successive output to 0..5 by `output % 6`; the first 4 values form the secret."
- **Reading one:** Use Marsaglia's standard xorshift32 with the sequence `x ^= x << 13; x ^= x >> 17; x ^= x << 5`, take the first output after one iteration (not the raw seed), and treat all steps in uint32.
- **Reading two:** Treat the seed itself as the first output (so `output_0 = seed`), or use a different xorshift32 variant/order of shifts, or mix signed/float semantics; each choice yields a different secret for the same seed.
- **Why it matters:** Session 2 criteria c-2-2 and c-2-3 depend on deriving the exact same secret in tests and in the app. A different variant or “seed-as-first-output” choice makes those assertions disagree and sinks the run.
- **Suggested wording:** "Derive the secret by applying Marsaglia xorshift32 to `seed` (uint32) using `x ^= x << 13; x ^= x >> 17; x ^= x << 5` in that order, taking `x` after the first iteration as `output_1`, then `output_2..` from subsequent iterations; map each `output_i & 0xffffffff` to 0..5 with `output_i % 6`; the first 4 mapped values form the secret."

### A2 - "Branch Here" row index vs upto=k is off-by-one ambiguous
- **Where:** spec.md, Screens → sc-play elements; Session 4 c-4-4 and c-4-5
- **Owner:** test-runner
- **The line:** "Branch Here buttons next to each prior row (data-testid=\"branch-here-<n>\")." and "POST /api/games/:id/branch with body { upto: k } … GET that game shows exactly k guesses copied" and "after clicking the Branch Here button for row k, the page renders exactly k guess rows"
- **Reading one:** `<n>` is the 1-based row number shown to the user; clicking `branch-here-1` sends `{ upto: 1 }` and yields 1 row.
- **Reading two:** `<n>` is a 0-based index; clicking `branch-here-0` sends `{ upto: 0 }` (keeping zero guesses), while the phrase "row k" elsewhere refers to a 1-based count; the two usages disagree.
- **Why it matters:** The same click can reasonably be wired to `{ upto: index }` or `{ upto: index + 1 }`. One produces k rows and the other k+1, so c-4-5 fails in one reading.
- **Suggested wording:** "Use 1-based row numbers in testids: `branch-here-1` keeps the first guess, …, `branch-here-k` sends `{ upto: k }` and the branched game renders exactly k rows."

### A3 - "first k guesses" ordering basis is unstated
- **Where:** spec.md, Session 4 c-4-4
- **Owner:** test-runner
- **The line:** "copy the first `upto` guesses into it (including black/white)"
- **Reading one:** "first" means chronological order by `createdAt` ascending (and rows are rendered in that same order).
- **Reading two:** "first" means insertion order as returned by the database default (often unspecified), or by `id` ordering; render order might then differ from copy order.
- **Why it matters:** Branch semantics and UI expectations (which row is "row k") depend on a fixed ordering. Different choices produce different subsets for the same `upto`, making c-4-4 and c-4-5 disagree with the tests.
- **Suggested wording:** "Define guess order as `createdAt` ascending; branching with `{ upto: k }` copies the first k guesses in that order, and the board renders rows in the same order."

### A4 - Hint suggestion display format is not pinned
- **Where:** spec.md, Session 3 c-3-3 and c-3-1
- **Owner:** test-runner
- **The line:** "the page shows … a suggested 4‑number guess (data-testid=\"hint-suggestion\")" and "suggestion = [0,0,0,0]"
- **Reading one:** The UI renders the array literally as "[0,0,0,0]" (including brackets and commas).
- **Reading two:** The UI renders a human string like "0 0 0 0" or "0000" or coloured pegs, with no literal brackets/commas.
- **Why it matters:** Tests that assert an exact string can pass in one rendering and fail in the other. The API shape is clear; the on-screen representation is not.
- **Suggested wording:** "Render `suggestion` text as the literal JSON array, e.g. "[0,0,0,0]", inside the element with data-testid=hint-suggestion."

## Worth a look
### W1 - "reflecting the chosen colours" lacks a stable assertion hook
- **Where:** spec.md, Session 1 c-1-3
- **Owner:** test-runner
- **The line:** "shows 4 peg slots reflecting the chosen colours"
- **Reading one:** Slots display numeric labels 0..5 that tests can read as text.
- **Reading two:** Slots display only coloured swatches via CSS with no text, needing a data attribute or inline style to assert.
- **Why it matters:** Without a pinned attribute or text, the Verifier may have to guess at markup or styles to assert the colours.
- **Suggested wording:** "Each slot element carries `data-color="0..5"` matching the saved code so tests can assert colours without reading styles."

### W2 - Null vs omitted fields for unscored guesses
- **Where:** spec.md, Session 1 c-1-2
- **Owner:** test-runner
- **The line:** "black/white are null (no scoring yet)"
- **Reading one:** Response includes explicit `"black": null` and `"white": null` keys.
- **Reading two:** Response omits those keys entirely until scoring is implemented.
- **Why it matters:** Tests that assert `is None/null` vs `key not present` diverge here.
- **Suggested wording:** "Include `black: null` and `white: null` explicitly in the JSON until scoring populates numbers."

### W3 - Row testids are not unique per row
- **Where:** spec.md, Screens → sc-play elements; Session 2 c-2-5
- **Owner:** test-runner
- **The line:** "per‑row score badges (data-testid=\"score-black\" and \"score-white\")"
- **Reading one:** Multiple rows reuse the same `score-black`/`score-white` testids and tests select them within each row container.
- **Reading two:** Test code queries globally by testid and is sensitive to multiple matches.
- **Why it matters:** The test shape must scope queries by row or pin per-row ids; the spec does not say which.
- **Suggested wording:** "Within each `guess-row-*`, render children with `data-testid="score-black"` and `data-testid="score-white"`, and tests will scope queries within the row."

### W4 - Session 2 "Builds" vs criteria targets
- **Where:** spec.json, Session 2 `builds` and criteria list
- **Owner:** spec-linter
- **The line:** `"builds": ["ep-games-get"]` while criteria include targets on `ep-guesses-create`.
- **Reading one:** "Builds" lists only the newly introduced endpoint; modifying an existing endpoint for scoring is implied and acceptable.
- **Reading two:** "Builds" is meant to enumerate everything a session delivers; omitting `ep-guesses-create` is an oversight.
- **Why it matters:** The session plan can mislead the Pack Writer about what is taught in the session.
- **Suggested wording:** "List both `ep-games-get` and `ep-guesses-create` in Session 2 `builds`, since the POST now enriches its response."

### W5 - sc-games declared in Session 3 but exercised in Session 4
- **Where:** spec.json, Session 3 `builds` and Session 4 criteria
- **Owner:** pack-writer
- **The line:** Session 3 `builds` includes `sc-games`, while its first criteria appear in Session 4.
- **Reading one:** Session 3 scaffolds the screen with no fetch; it becomes functional in Session 4.
- **Reading two:** Session 3 was meant to include list/resume behaviour and the criteria drifted a session later.
- **Why it matters:** The teaching flow and guide timing depend on whether a screen is introduced earlier than it is graded.
- **Suggested wording:** "Either move `sc-games` to Session 4 `builds` or add a Session 3 criterion that the screen scaffolds without data, to match the plan."
