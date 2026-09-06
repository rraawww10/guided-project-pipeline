# Session 3 - Stable comparator and threshold filter

Time: 40 minutes
Students start from: Session 2 complete — /api/rank works and the UI shows scores and reasons when a toggle is on; ordering may still be by score only
Students end with: Stable, deterministic ordering using explicit tie-breakers; optional min filter applied to the rounded score; all c-3-* green

What they learn
- Designing and implementing a stable multi-key comparator
- ASCII codepoint name ordering vs locale-aware collation
- Server-side threshold filtering applied to the rounded score

Before you start
- Keep npm run dev running
- Open these files:
  - app/lib/sort.ts
  - app/app/api/rank/route.ts

The plan
| Minutes | What you do |
|---|---|
| 0-6  | Frame the goal: make ordering predictable for the same inputs. Walk through the required tie-breaker order. |
| 6-24 | Live-code cut-sort-cmp in app/lib/sort.ts. Implement primary key by unrounded DESC, tie-break on tag when active, special-case no-active to name ASC, then years DESC, then name ASC (ASCII). Refresh and exercise ties. |
| 24-32 | Live-code cut-api-rank-apply-min in app/app/api/rank/route.ts. Parse "min" and filter out rows whose rounded score is strictly less than the threshold. |
| 32-38 | Students finish and you circulate. Test a few URLs together. |
| 38-40 | Recap: sorting is stable and filtering uses rounded values. |

Cut points in this session

### cut-sort-cmp - lib/sort.ts:13
- What students see: // TODO(cut-sort-cmp): Implement `cmp` so that it compares a and b by unrounded score DESC; when the 'tag' token is active and one candidate has the preferred tag and the other does not, place the tagged candidate first; next break ties by years DESC; finally by name ASC using ASCII codepoint order
- What they write: define cmp = (a, b, active) => { if a.unrounded != b.unrounded return DESC; if active has 'tag' and hasPreferredTag differs, prefer true; if active.size === 0 then name ASC; else break ties by years DESC, then name ASC (string < / > using codepoint order) }
- Teach it like this: Make the order explicit and in this fixed sequence. Use direct < and > to get ASCII codepoint order; avoid localeCompare.
- Passes when: c-3-1, c-3-2, c-3-3 go green

Orientation from the real file (non-answer lines you can point at):

export type Cmp = (a: RankWorking, b: RankWorking, active: Set<ToggleToken>) => number

export let cmp: Cmp = () => 0

### cut-api-rank-apply-min - app/api/rank/route.ts:52
- What students see: // TODO(cut-api-rank-apply-min): If the 'min' query parameter is present, remove from `body` any RankItem whose ROUNDED two‑decimal score is strictly less than that threshold before responding
- What they write: read min = Number(url.searchParams.get("min")); if it’s a number, filter body = body.filter(it => it.score >= min)
- Teach it like this: The filter is on the rounded numeric score you already expose to clients — keep rows with rounded >= min.
- Passes when: c-3-4 goes green

Where students get stuck
- “I used localeCompare for names and a test fails” — Tests assume ASCII order — Say: Use `<` and `>` comparisons for strings; that yields ASCII codepoint order.
- “Min filter seems to do nothing” — Filtering before body is built or comparing strings — Say: Apply the filter after you’ve built numeric scores and ensure you convert query string to a Number.
- “Tie-breaker by tag doesn’t seem to apply” — Only applies when 'tag' is active — Say: Guard that branch with active.has('tag').

Check before moving on
- GET /api/rank with no active tokens orders by name ASC (ASCII) for equal scores.
- GET /api/rank?active=tag orders tagged first on equal scores; same-tag ties break by name.
- GET /api/rank?active=years&min=100 returns [].
