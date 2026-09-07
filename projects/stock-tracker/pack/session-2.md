# Session 2 - Allocation report and drift highlight

**Time:** 40 minutes
**Students start from:** S1 complete (rows + weight cell). Allocation API and UI fetch are TODO, so the page shows "Loading...".
**Students end with:** GET /api/allocation returns rows; the UI shows OVER/UNDER badges; loading text is visible during fetch.

## What they learn
- Normalising by total portfolio value to compute currentWeight
- Computing driftPercent as (current - target) × 100
- Next.js GET handler returning computed rows
- Client fetch with a visible loading state and conditional rendering

## Before you start
- Keep dev server running.
- Open:
  - app/lib/allocation.ts
  - app/app/api/allocation/route.ts
  - app/app/(dashboard)/page.tsx (allocation section)

## The plan
| Minutes | What you do |
|---|---|
| 0-5 | Recap percent math. Point at computeAllocation and the TODO. |
| 5-15 | Live-code cut-calc-weights: map positions to AllocationRow and compute driftPercent. |
| 15-20 | Live-code cut-ep-allocation-body: return rows and 200. |
| 20-27 | Live-code cut-ui-fetch-allocation: fetch, set loading, then set report. Explain the tiny timeout. |
| 27-30 | Live-code cut-ui-drift-badge: render OVER/UNDER based on sign. |
| 30-38 | Students finish and verify both OVER and UNDER appear. |
| 38-40 | Summarise: weights sum to ~1.000 (3dp). Tease plan generation next. |

## Cut points in this session
### cut-calc-weights - lib/allocation.ts:15
- **What students see:** `// TODO(cut-calc-weights): Build \`weights\` as an array of {symbol, valueCents, currentWeight, targetWeight, driftPercent} by dividing each position's value by the portfolio total and subtracting the target weight`
- **What they write:** map each position to an object with valueCents, currentWeight = value/total (0 when total is 0), targetWeight from store, driftPercent = (current - target) × 100.
- **Teach it like this:** Total is a scalar; divide valueCents by total to get a fraction.
- **Passes when:** c-2-1 and c-2-5 go green.

Context you can show (from app/):
```ts
export async function computeAllocation(): Promise<AllocationRow[]> {
  const positions = await getPositions()
  const total = positions.reduce((sum, p) => sum + p.shares * p.priceCents, 0)
  let weights: AllocationRow[] = []
  // >>> CUT cut-calc-weights
  weights = positions.map((p) => {
    const valueCents = p.shares * p.priceCents
    const currentWeight = total > 0 ? valueCents / total : 0
    const targetWeight = p.targetWeight
    const driftPercent = (currentWeight - targetWeight) * 100
    return { symbol: p.symbol, valueCents, currentWeight, targetWeight, driftPercent }
  })
  // <<< CUT cut-calc-weights
  return weights
}
```

### cut-ep-allocation-body - app/app/api/allocation/route.ts:10
- **What students see:** `// TODO(cut-ep-allocation-body): Put every allocation row computed from the store into \`body\` and set \`status\` to 200`
- **What they write:** call computeAllocation(), assign to body, set status = 200.
- **Teach it like this:** Same shape as positions; the return stays outside the cut.
- **Passes when:** c-2-1 goes green.

Context you can show (from app/):
```ts
export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-allocation-body
  const rows = await computeAllocation()
  body = rows
  status = 200
  // <<< CUT cut-ep-allocation-body
  return Response.json(body, { status })
}
```

### cut-ui-fetch-allocation - app/app/(dashboard)/page.tsx:50
- **What students see:** `// TODO(cut-ui-fetch-allocation): Load the allocation report into \`report\` and render a visible 'Loading...' text while \`report\` is undefined`
- **What they write:** `useEffect` that sets `reportState` undefined (to show Loading...), fetches `/api/allocation`, then sets `reportState`.
- **Teach it like this:** The 50ms setTimeout makes "Loading..." observable even on fast SQLite.
- **Passes when:** c-2-4 goes green and enables c-2-2/c-2-3.

Context you can show (from app/):
```tsx
// >>> CUT cut-ui-fetch-allocation
useEffect(() => {
  let active = true
  setReportState(undefined)
  // Defer fetch slightly so the Loading... text is observably visible even on fast SQLite
  const id = setTimeout(() => {
    fetch('/api/allocation')
      .then((r) => r.json())
      .then((data) => {
        if (!active) return
        report = data
        setReportState(data)
      })
  }, 50)
  return () => {
    active = false
    clearTimeout(id)
  }
}, [])
// <<< CUT cut-ui-fetch-allocation
```

### cut-ui-drift-badge - app/app/(dashboard)/page.tsx:74
- **What students see:** `// TODO(cut-ui-drift-badge): Set \`driftClass\`/label on each row so overweight shows a badge with text 'OVER' and underweight shows 'UNDER' at data-testid \`drift-${symbol}\``
- **What they write:** set class/label based on `row.driftPercent > 0 ? 'OVER' : row.driftPercent < 0 ? 'UNDER' : ''`.
- **Teach it like this:** Only the text and testid matter for tests; class names are not asserted.
- **Passes when:** c-2-2 and c-2-3 go green.

Context you can show (from app/):
```tsx
// >>> CUT cut-ui-drift-badge
driftClass = row.driftPercent > 0 ? 'over' : row.driftPercent < 0 ? 'under' : 'even'
label = row.driftPercent > 0 ? 'OVER' : row.driftPercent < 0 ? 'UNDER' : ''
// <<< CUT cut-ui-drift-badge
```

## Where students get stuck
- "My weights don’t sum to 1" - Sum unrounded fractions; rounding happens only when the test reads to 3dp.
- "Loading never shows" - They didn’t set `reportState` to undefined before fetch or removed the small timeout.
- "Division by zero" - Guard `total > 0 ? value/total : 0` as in the snippet.
- "Badge never says UNDER" - Their sign logic is reversed; driftPercent is current - target.

## Check before moving on
- /api/allocation returns an array with symbol/currentWeight/targetWeight/driftPercent.
- The page shows at least one OVER and one UNDER badge; "Loading..." is visible briefly.
