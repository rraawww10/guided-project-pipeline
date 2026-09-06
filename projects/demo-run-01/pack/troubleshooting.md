Troubleshooting — Shortlist Scorer

Real issues students hit and what to say

API and data
- /api/candidates returns 501
  - Cause: status never set to 200 in cut-api-candidates-list
  - Say: Set status = 200 before returning NextResponse.json(body, { status }).
- RankItem.score is a string ("0.6") instead of a number
  - Cause: toFixed applied on the server or JSON sent as string
  - Say: Keep score numeric in JSON; round to two decimals with Math.round(unrounded*100)/100; UI formats with toFixed(2).
- /api/rank accepts unknown tokens and still returns 200
  - Cause: parseActive(req) not called or its error path ignored
  - Say: Call parseActive(req); if !ok return NextResponse.json({ error }, { status: 400 }) early.

Sorting and reasons
- Order looks almost right but two neighbors are swapped
  - Cause: sorted by rounded score instead of unrounded, or forgot a tie-breaker
  - Say: Sort by unrounded DESC (or use cmp). Then apply the stated tie-breakers.
- Name ordering test fails when using localeCompare
  - Cause: Tests assume ASCII codepoint order
  - Say: Use simple `<` / `>` string comparisons to get ASCII order.
- Tag tiebreak seems ignored
  - Cause: Applied regardless of active tokens
  - Say: Only apply the tag preference when active.has("tag").

UI state and effects
- “I still see no cards on /”
  - Cause: Fetched but never wrote to items in cut-ui-load-candidates
  - Say: After resp.json(), setItems(data) (guarded by !cancelled) to trigger a render.
- Rank fetch runs on first load before toggles are touched
  - Cause: The skeleton intentionally starts with years ON outside the markers
  - Say: Implement cut-ui-toggle-init to new Set<ToggleToken>() so tokens.length === 0 and the rank effect won’t run until toggled.

Minimum filter
- Adding ?min=... has no effect
  - Cause: Compared strings or applied filter before body was populated
  - Say: Convert min with Number(...); if not NaN, filter body using the numeric, rounded score: it.score >= min.

TypeScript and imports
- “Cannot find name Candidate / RankItem”
  - Cause: Editing imports
  - Say: Do not change the provided imports; use what’s already at the top of each file. The paths are correct:
    - app/app/api/candidates/route.ts imports from ../../../lib/...
    - app/app/api/rank/route.ts imports cmp, maxYears, toPublic, toWorking
    - lib/score.ts imports PREFERRED_TAG from ./store

Comparator return values
- “Sort is backwards”
  - Cause: Returned 1/−1 in the wrong places
  - Say: For DESC by a value v: if (a.v !== b.v) return a.v > b.v ? -1 : 1.
