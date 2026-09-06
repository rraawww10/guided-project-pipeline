# Shortlist Scorer

## Outcome
A small full‑stack Next+React+TypeScript app that ranks a fixed seed of 10 candidates by simple weighted rules with transparent reasons. It exposes two endpoints: a plain list of candidates and a rank endpoint that maps each candidate through a pure scorer, sorts deterministically, and returns score plus human‑readable reasons. The UI shows one card per candidate, the current score, and a short “reasons” summary. Toggles switch signals on/off; a minimum score filter hides low‑scoring items in session 3. The final order is stable and explainable.

## Out of scope
- CSV import/export, external data sources, or large datasets
- Persistence of weights; all weights are kept in memory only
- Any real‑time or date‑based criteria

## Data model
- Candidate
  - id: string (stable key)
  - name: string
  - years: number (whole years of experience)
  - tags: string[]
- RankItem (API response item)
  - id: string (same as Candidate)
  - name: string
  - score: number (numeric JSON value). RankItem.score MUST be a number in JSON. The response returns a numeric score rounded to two decimals (e.g., 1, 1.3, 1.75). Never return it as a string. The UI formats the displayed score with two decimals.
  - reasons: string[] (short human‑readable fragments that line up with the math, e.g., "years +0.60", "preferred tag +1")
- Weights and signals
  - Active tokens: "years", "tag"
  - Preferred tag token: the exact string "typescript". A candidate "hasPreferredTag" when tags includes "typescript" (case‑sensitive).
  - Session 2 scoring rule (pure function):
    - Base from years (active "years"): normalize years to a 0..1 band by dividing by the maximum years in the current dataset, then scale by 1.0. Example: with maxYears 10, a 6‑year candidate contributes 0.6.
    - Tag bonus (active "tag"): if hasPreferredTag, add +1.0; else add +0.
    - Sum to get an unrounded numeric score. This unrounded score is used for ordering. The response includes a numeric score rounded to two decimals; the UI displays toFixed(2).
    - reasons[] includes one entry per active signal, naming the signal and its signed contribution (e.g., "years +0.60", "preferred tag +1").
- Stable comparator (Session 3):
  - Primary key: unrounded score DESC
  - Tie‑break 1: when "tag" is active, prefer hasPreferredTag over not
  - Tie‑break 2: years DESC
  - Tie‑break 3: name ASC by ASCII codepoint order (pure codepoint compare; tests assume ASCII order)
  - Session use: In Session 2 you may sort by unrounded score only; in the final app (post‑Session 3) always sort using the stable comparator from lib/sort.ts (cmp).
- Seed
  - Exactly 10 candidates in a tracked seed file. At least one pair shares the same years value (to exercise name ordering on ties). At least one candidate has the preferred tag "typescript".

## Endpoints
- ep-candidates-list
  - GET /api/candidates
  - Request: none
  - Response: Candidate[]
  - Status: 200
- ep-rank
  - GET /api/rank
  - Query parameters
    - active: optional string. Comma‑separated tokens drawn from {years, tag}. Unknown token yields 400. Empty tokens are ignored. If multiple 'active' keys are present (e.g., ?active=years&active=tag), join their values with commas in arrival order before parsing.
    - min: optional number. Apply the filter to the ROUNDED score (the two‑decimal value returned in RankItem). Keep rows with rounded_score >= min; drop rows with rounded_score < min.
  - Response: RankItem[]
  - Status: 200 on success; 400 on unknown token in active
  - Sorting: In Session 2, sorting by unrounded score in descending order is acceptable. In the final app, always sort using the stable comparator from lib/sort.ts (cmp).

## Screens
- sc-main (route "/")
  - Elements:
    - One repeated card per candidate (data-testid="card")
    - Toggle panel with two checkboxes: years (data-testid="toggle-years"), tag (data-testid="toggle-tag")
    - Each card shows a visible score text (data-testid="score") and a short reasons summary (data-testid="reasons")
    - A numeric input for minimum score (data-testid="input-min") appears starting in Session 3 only; it is absent in Sessions 1–2
  - States: empty (while loading), loaded, error (fetch failure)

## Sessions

### Session 1 - Seed, list, and toggles
- Goal: Boot the app, expose /api/candidates, render the list on "/", and show a toggle panel that updates local state (no scoring yet).
- Teaches: Next API route basics, fetch+useEffect, useState
- Builds: ep-candidates-list, sc-main
- Acceptance criteria
  - c-1-1: GET /api/candidates returns 200 with a JSON array of 10 Candidate items
  - c-1-2: sc-main renders 10 elements with data-testid="card" on "/"
  - c-1-3: sc-main renders two checkboxes with data-testids "toggle-years" and "toggle-tag"
  - c-1-4: GET /api/candidates returns 200 with a JSON array that contains at least one pair of candidates sharing the same years value
  - c-1-5: GET /api/candidates returns 200 with a JSON array that includes at least one item whose tags contain "typescript"
- Cut points (student blocks)
  - cut-api-candidates-list (app/api/candidates/route.ts)
    - writes_into: body
    - Hint: Put every candidate from the seed into `body` and set `status` to 200
  - cut-ui-load-candidates (app/page.tsx)
    - writes_into: items
    - Hint: After fetching "/api/candidates", parse the JSON array and write it into the `items` state
  - cut-ui-toggle-init (app/page.tsx)
    - writes_into: active
    - Hint: Initialize the `active` state to an empty Set of tokens (no signals active yet)

### Session 2 - Pure scorer and rank endpoint
- Goal: Implement a pure scorer that yields a numeric score and reasons, add /api/rank that maps candidates through it, and render ranked cards with score and reasons when toggles change.
- Teaches: Pure functions, mapping server DTOs, parsing query strings, descending sort by a key
- Builds: ep-rank
- Acceptance criteria
  - c-2-1: GET /api/rank?active=years returns 200 with a JSON array of 10 RankItem, each having id (string), name (string), score (number), and reasons (string[])
  - c-2-2: With active=years only, GET /api/rank returns items ordered by unrounded score in descending order (non‑increasing numeric sequence)
  - c-2-3: On "/", when the years toggle is on, each card renders a score text with data-testid="score" that matches two‑decimal formatting (e.g., 0.60)
  - c-2-4: On "/", when the years toggle is on, at least one card’s reasons (data-testid="reasons") includes the word "years"
- Cut points (student blocks)
  - cut-score-apply (lib/score.ts)
    - writes_into: out
    - Hint: Set fields on `out`: compute `out.score` from the rules (years normalization plus optional preferred‑tag bonus) and fill `out.reasons` with one entry per active signal
  - cut-api-rank-parse-query (app/api/rank/route.ts)
    - writes_into: activeTokens
    - Hint: Parse the 'active' query by splitting on commas after merging repeated keys, drop empty tokens, validate each token against {years, tag}, and write the valid set into `activeTokens`; answer 400 for any unknown
  - cut-api-rank-build (app/api/rank/route.ts)
    - writes_into: body
    - Hint: Map every Candidate to a RankItem using the pure scorer, set each RankItem.score as a number already rounded to two decimals, and fill `body` with all RankItem rows; in Session 2 you may sort by unrounded score in descending order, and in the final app always sort using `cmp` from lib/sort.ts; set `status` to 200 when successful
  - cut-ui-rank-fetch (app/page.tsx)
    - writes_into: items
    - Hint: When the active tokens change, call "/api/rank?active=..." and write the parsed RankItem array into the `items` state

### Session 3 - Stable comparator and threshold filter
- Goal: Make order deterministic with explicit tie‑breakers and add a minimum score filter.
- Teaches: Stable multi‑key comparator, ASCII collation, server‑side threshold filtering
- Builds: (uses ep-rank; adds lib/sort.ts comparator)
- Acceptance criteria
  - c-3-1: With no active tokens (?active=), if two items have the same unrounded score, the order is by name in ASCII codepoint order (A..Z < a..z); GET /api/rank reflects this order
  - c-3-2: With active=tag, GET /api/rank returns 200 with items ordered so that when two candidates have the same years and both either have or both lack the preferred tag, the tie is broken by name in ASCII order
  - c-3-3: With active=tag, when two candidates have the same years and exactly one has the preferred tag, the tagged candidate appears first in GET /api/rank
  - c-3-4: GET /api/rank?active=years&min=100 returns 200 with an empty JSON array
- Cut points (student blocks)
  - cut-sort-cmp (lib/sort.ts)
    - writes_into: cmp
    - Hint: Implement `cmp` so that it compares a and b by unrounded score DESC; when the "tag" token is active and one candidate has the preferred tag and the other does not, place the tagged candidate first; next break ties by years DESC; finally by name ASC using ASCII codepoint order
  - cut-api-rank-apply-min (app/api/rank/route.ts)
    - writes_into: body
    - Hint: If the 'min' query parameter is present, remove from `body` any RankItem whose ROUNDED two‑decimal score is strictly less than that threshold before responding