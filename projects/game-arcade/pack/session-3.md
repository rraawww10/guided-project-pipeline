# Session 3 - Deterministic hint and remaining candidates

Time: 40 minutes
Students start from: scoring working; rows render with black/white
Students end with: GET /hint returns remaining + suggestion; UI shows both

What they learn
- Constraint filtering over the finite 6^4 space
- Deterministic ordering for reproducible hints
- Client fetch to display a computed server hint

Before you start
- Keep a game with a couple of guesses on /
- Open these files:
  - app/lib/candidates.ts (filterCandidates, nextCandidate)
  - app/app/api/games/[id]/hint/route.ts (build hint from history)
  - app/app/page.tsx (fetch + display hint)

The plan
| Minutes | What you do |
|---|---|
| 0-6 | Explain the search space (6^4 = 1296) and the idea: keep only codes consistent with history; pick the first deterministically. |
| 6-14 | Live-code cut-filter-candidates: start from allCodes(); keep codes whose score vs each recorded guess equals that guess's black/white. |
| 14-20 | Live-code cut-next-candidate: compute candidates, sort lexicographically, pick the first or null. Stress determinism. |
| 20-26 | Live-code cut-ep-hint-build: read guesses, map to { code, black, white }, compute candidates and suggestion, build { remaining, suggestion }. |
| 26-32 | Live-code cut-ui-hint-fetch: fetch /api/games/:id/hint and set hintState; show remaining and suggestion. |
| 32-38 | Students try with and without guesses; you circulate. |
| 38-40 | Recap: same history → same suggestion; set up for listing and branching next. |

Cut points in this session

### cut-filter-candidates - lib/candidates.ts:17
- What students see: `// TODO(cut-filter-candidates): From the 6^4 search space, keep only those codes in \`candidates\` whose score against each recorded guess equals that guess's stored black/white`
- What they write: get the full space, then filter by recomputing scoreGuess(code, g.code) and keeping matches for every history item.
- Teach it like this: The filter is pure and small; reuse the tested scoreGuess and compare exact black/white pairs for every past guess.
- Passes when: c-3-2 goes green (and supports c-3-1).

### cut-next-candidate - lib/candidates.ts:31
- What students see: `// TODO(cut-next-candidate): Choose the deterministic next guess as the lexicographically first code from the candidate set and assign it to \`suggestion\`, or null when the set is empty`
- What they write: call filterCandidates(history), sort by a,b,c,d ascending, take the first or null.
- Teach it like this: Determinism is the point: sorting fixes the choice so two games with the same history agree.
- Passes when: c-3-1 and c-3-4 go green.

### cut-ep-hint-build - app/api/games/[id]/hint/route.ts:10
- What students see: `// TODO(cut-ep-hint-build): Load the game's guesses, compute the remaining candidate set and a deterministic next guess, and place { remaining, suggestion } into \`body\` with status 200`
- What they write: map DB guesses to plain { code:number[], black:number, white:number }, compute candidates and suggestion, assign body = { remaining: candidates.length, suggestion }.
- Teach it like this: Transform persistence shapes once at the edge; keep compute code in lib/.
- Passes when: c-3-1 and c-3-2 go green.

### cut-ui-hint-fetch - app/page.tsx:60
- What students see: `// TODO(cut-ui-hint-fetch): Fetch the hint endpoint for the active game and write its { remaining, suggestion } into \`hintState\` for display`
- What they write: after a successful GET, setHintState(body).
- Teach it like this: Simple client fetch → state; tests read hint-remaining and hint-suggestion text.
- Passes when: c-3-3 goes green.

Where students get stuck
- "My suggestion changes run-to-run" - You didn't sort candidates; pick lexicographic first so the hint is reproducible.
- "Remaining is wrong after a scored guess" - You compared only blacks or only whites; compare the pair (black, white) exactly for every history item.
- "UI shows 'null' even when guesses exist" - You never set hintState or you set it before the fetch resolved. Await the fetch and set state from the parsed JSON.

Check before moving on
- With no guesses, GET /api/games/:id/hint returns remaining 1296 and suggestion [0,0,0,0]; on the page, both remaining and suggestion render.
