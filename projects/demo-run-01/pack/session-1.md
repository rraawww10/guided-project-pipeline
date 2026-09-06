# Session 1 - Seed, list, and toggles

Time: 40 minutes
Students start from: the app boots at / with zero cards; years toggle is ON by default; GET /api/candidates answers 501 and the UI does not load items yet
Students end with: /api/candidates returns 200 with 10 items; "/" renders 10 cards; both toggles visible and start unchecked

What they learn
- Next.js App Router API route basics (export async function GET, NextResponse.json)
- useEffect + fetch + local state
- useState with Set for toggle tokens

Before you start
- In a terminal at projects/demo-run-01/app: npm run dev, then open http://localhost:3000
- Open these files side by side:
  - app/app/api/candidates/route.ts
  - app/app/page.tsx
  - app/data/candidates.ts

The plan
| Minutes | What you do |
|---|---|
| 0-4 | Frame the goal: return the seeded 10 candidates from /api/candidates and render them on "/". Point out the toggles; years is intentionally on at start. |
| 4-14 | Live-code cut-api-candidates-list in app/app/api/candidates/route.ts. Show the seed file and the GET handler shape. Set body to the seed and status to 200. Start devtools, hit /api/candidates, show 200 and 10 items. |
| 14-26 | Live-code cut-ui-load-candidates in app/app/page.tsx. Fetch /api/candidates on mount and write parsed JSON into items. Show the 10 cards render. |
| 26-33 | Live-code cut-ui-toggle-init in app/app/page.tsx. Initialize active to an empty Set so both toggles start unchecked. Refresh and point out that no rank fetch runs when nothing is active. |
| 33-38 | Students finish and catch up. You circulate and help them set status to 200, and ensure setItems gets the fetched array. |
| 38-40 | Recap: what runs now and what’s next (a scorer and /api/rank). |

Cut points in this session

### cut-api-candidates-list - app/api/candidates/route.ts:8
- What students see: // TODO(cut-api-candidates-list): Put every candidate from the seed into `body` and set `status` to 200
- What they write: assign the full seed array to body and set status = 200 before returning
- Teach it like this: The API route is just a function. Put data in body and choose the HTTP status. 200 means OK.
- Passes when: c-1-1 goes green (also unlocks c-1-4 and c-1-5)

Orientation from the real file (for you to point at, do not paste the answer):

import { NextResponse } from "next/server"
import { allCandidates } from "../../../lib/store"
import { Candidate } from "../../../lib/types"

export async function GET(): Promise<Response> {
  let body: Candidate[] = []
  let status = 501
  return NextResponse.json(body, { status })
}

### cut-ui-load-candidates - app/page.tsx:34
- What students see: // TODO(cut-ui-load-candidates): After fetching "/api/candidates", parse the JSON array and write it into the `items` state
- What they write: after a successful fetch, const data = await resp.json(); then setItems(data) if not cancelled
- Teach it like this: Fetch returns a Response; .json() parses it. Set React state with the parsed array to re-render.
- Passes when: c-1-2 goes green

Orientation from the real file:

React.useEffect(() => {
  let cancelled = false
  async function load() {
    try {
      const resp = await fetch("/api/candidates")
      if (!resp.ok) return
      const data = await resp.json()
    } catch (e) {
      // ignore in demo
    }
  }
  load()
  return () => {
    cancelled = true
  }
}, [])

### cut-ui-toggle-init - app/page.tsx:20
- What students see: // TODO(cut-ui-toggle-init): Initialize the `active` state to an empty Set of tokens (no signals active yet)
- What they write: change init to new Set<ToggleToken>() so both toggles start unchecked
- Teach it like this: Start from no signals. We’ll turn them on later; an empty Set also keeps the rank effect from running.
- Passes when: c-1-3 goes green

Where students get stuck
- “/api/candidates still shows 501” — Forgot to set status = 200 — Say: Set status to 200 before returning NextResponse.json.
- “I see no cards” — Fetched but never wrote to items — Say: After resp.json(), call setItems(data) (guarded by !cancelled).
- “Why is ‘years’ already on?” — That’s deliberate in the skeleton — Say: Replace the init with an empty Set, then refresh.

Check before moving on
- On http://localhost:3000 you see 10 cards. Network tab shows GET /api/candidates 200 with 10 items.
