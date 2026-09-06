# Session 2 - Pure scorer and rank endpoint

Time: 40 minutes
Students start from: Session 1 complete — 10 cards render from /api/candidates; both toggles unchecked
Students end with: Toggling “years” shows scores to two decimals and a reasons line containing “years”; GET /api/rank?active=years returns 10 RankItem ordered by unrounded score DESC

What they learn
- Pure functions and deterministic outputs (no I/O)
- Mapping domain to DTOs and rounding at the API boundary
- Parsing query strings safely and returning 400 on bad input
- Descending sort by a numeric key (Session 2 can sort by unrounded score only)

Before you start
- Keep npm run dev running at http://localhost:3000
- Open these files:
  - app/lib/score.ts
  - app/app/api/rank/route.ts
  - app/app/page.tsx

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Set the goal: build a scorer and a /api/rank endpoint that returns score + reasons and is called when a toggle is on. |
| 5-14 | Live-code cut-score-apply in lib/score.ts. Compute unrounded from years normalization (+ optional +1 tag), build reasons, then round to two decimals. Return both rounded and unrounded. |
| 14-20 | Live-code cut-api-rank-parse-query in app/app/api/rank/route.ts. Call parseActive(req); on failure return 400 early; otherwise set activeTokens. |
| 20-30 | Live-code cut-api-rank-build in app/app/api/rank/route.ts. Map candidates to working items, sort (Session 2 can sort by unrounded score or use cmp already), convert to public rows, set status 200. Hit /api/rank?active=years and show shape. |
| 30-35 | Live-code cut-ui-rank-fetch in app/app/page.tsx. When active changes and is non-empty, fetch /api/rank?active=..., write parsed RankItem[] into items. Show scores and reasons render. |
| 35-38 | Students finish and you circulate. |
| 38-40 | Recap: scores are deterministic; next time we’ll make ordering stable under ties and add a min filter. |

Cut points in this session

### cut-score-apply - lib/score.ts:29
- What students see: // TODO(cut-score-apply): Set fields on `out`: compute `out.score` from the rules (years normalization plus optional preferred‑tag bonus) and fill `out.reasons` with one entry per active signal
- What they write: compute base = years/maxYears when "years" is active; if "tag" is active add +1.0 only when candidate has the preferred tag; push one reason string per active signal; round to two decimals for out.rounded; keep unrounded too; record hasPreferredTag
- Teach it like this: Keep the math pure. Same inputs, same outputs. Round only at the boundary that returns JSON.
- Passes when: c-2-4 goes green

Orientation from the real file:

export function scoreApplicant(
  c: Candidate,
  active: Set<ToggleToken>,
  maxY: number
): ScoreResult {
  let out: ScoreResult = { unrounded: 0, rounded: 0, reasons: [], hasPreferredTag: false }
  const wantYears = active.has("years")
  const wantTag = active.has("tag")

  const pref = hasPreferredTag(c.tags)
  // … compute out …
  return out
}

### cut-api-rank-parse-query - app/api/rank/route.ts:31
- What students see: // TODO(cut-api-rank-parse-query): Parse the 'active' query by splitting on commas after merging repeated keys, drop empty tokens, validate each token against {years, tag}, and write the valid set into `activeTokens`; answer 400 for any unknown
- What they write: call the provided parseActive(req); if !ok return NextResponse.json({error}, {status: 400}); else set activeTokens and (optionally) status = 200 for the build that follows
- Teach it like this: Parse once, validate, and fail fast with a 400 when input is wrong.
- Passes when: c-2-1 goes green

Orientation from the real file:

function parseActive(req: NextRequest): { ok: true; active: Set<ToggleToken> } | { ok: false; message: string } {
  const url = new URL(req.url)
  const sp = url.searchParams
  // Merge repeated keys by joining with commas in arrival order
  const parts: string[] = sp.getAll("active")
  const merged = parts.join(",")
  const tokens = merged.split(",").map((s) => s.trim()).filter((s) => s.length > 0)
  const out = new Set<ToggleToken>()
  const valid: ToggleToken[] = ["years", "tag"]
  for (const t of tokens) {
    if (!valid.includes(t as ToggleToken)) {
      return { ok: false, message: `unknown token: ${t}` }
    }
    out.add(t as ToggleToken)
  }
  return { ok: true, active: out }
}

### cut-api-rank-build - app/api/rank/route.ts:41
- What students see: // TODO(cut-api-rank-build): Map every Candidate to a RankItem using the pure scorer, set each RankItem.score as a number already rounded to two decimals, and fill `body` with all RankItem rows; in Session 2 you may sort by unrounded score in descending order, and in the final app always sort using `cmp` from lib/sort.ts; set `status` to 200 when successful
- What they write: get all candidates; compute maxYears; map to working rows with toWorking(candidate, activeTokens, maxY); sort (Session 2: by unrounded DESC is acceptable); body = toPublic(working); status = 200
- Teach it like this: Separate working shape (unrounded included) from public DTO (rounded only). Sort the working rows.
- Passes when: c-2-1 goes green (also enables c-2-2)

Orientation from the real file (non-answer lines you can point at):

import { cmp } from "../../../lib/sort"
import { maxYears, toPublic, toWorking } from "../../../lib/score"

### cut-ui-rank-fetch - app/page.tsx:58
- What students see: // TODO(cut-ui-rank-fetch): When the active tokens change, call "/api/rank?active=..." and write the parsed RankItem array into the `items` state
- What they write: build qs with new URLSearchParams({ active: tokens.join(",") }); fetch(`/api/rank?${qs}`); const data = await resp.json(); setItems(data) if not cancelled
- Teach it like this: Drive the server from UI state; when the toggles change, refetch and render scores.
- Passes when: c-2-3 goes green

Where students get stuck
- “active=years,tag still 200 but order looks random” — Sorted by rounded score or forgot to sort — Say: Either use cmp already, or in Session 2 sort by the unrounded value for order.
- “Unknown token doesn’t 400” — parseActive is not called or its !ok path isn’t returned — Say: Call parseActive(req) and return a 400 early on failure.
- “reasons never include ‘years’” — Did not push a reason string for the years branch — Say: When years is active, push `years +${base.toFixed(2)}` into reasons.

Check before moving on
- On "/": turn on the “years” toggle. Each card shows a score to two decimals and at least one reasons entry contains the word "years". GET /api/rank?active=years returns 200 with 10 items ordered by unrounded score DESC.
