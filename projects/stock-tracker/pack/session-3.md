# Session 3 - Trade plan under budget

**Time:** 40 minutes
**Students start from:** Allocation done. Plan API and UI plan rows are TODO; budget input is present (cents).
**Students end with:** POST /api/trade-plan returns PlanItem[]; UI renders one plan row per item with side/shares/cost.

## What they learn
- Ranking by drift with a deterministic tie-break
- Greedy integer allocation under a cash cap
- Reading a JSON body in a Next.js POST handler
- Rendering a second table from API data

## Before you start
- Keep dev server running.
- Open:
  - app/lib/plan.ts
  - app/app/api/trade-plan/route.ts
  - app/app/(dashboard)/page.tsx (plan table section)

## The plan
| Minutes | What you do |
|---|---|
| 0-5 | Recap drift; explain BUY vs SELL and that budget caps only BUYs. |
| 5-12 | Live-code cut-plan-rank: overweight first, then by abs(drift) desc, tie-break by symbol. |
| 12-25 | Live-code cut-plan-allocate: walk ranked rows, compute integer shares within budget; push BUY/SELL items. |
| 25-30 | Live-code cut-ep-plan-body: parse body safely, call generatePlan, 200. |
| 30-35 | Live-code cut-ui-plan-rows: render plan table with required testids. |
| 35-38 | Students verify budget respected and first symbol matches largest positive drift. |
| 38-40 | Preview editing targets and budget next. |

## Cut points in this session
### cut-plan-rank - lib/plan.ts:16
- **What students see:** `// TODO(cut-plan-rank): Build \`ranked\` as symbols ordered by absolute drift descending, breaking ties by symbol ascending to be deterministic`
- **What they write:** sort a copy of alloc so overweight (positive drift) appear first, then by absolute magnitude desc, tie-break by symbol ascending.
- **Teach it like this:** Determinism matters for tests; keep a stable tie-break.
- **Passes when:** c-3-3 goes green.

Context you can show (from app/):
```ts
// >>> CUT cut-plan-rank
ranked = [...alloc].sort((a, b) => {
  const ap = a.driftPercent
  const bp = b.driftPercent
  // Positive drifts (overweight) before negatives (underweight)
  if ((ap > 0) !== (bp > 0)) return ap > 0 ? -1 : 1
  // Within the same sign, sort by absolute magnitude desc
  const da = Math.abs(ap)
  const db = Math.abs(bp)
  if (db !== da) return db - da
  return a.symbol.localeCompare(b.symbol)
})
// <<< CUT cut-plan-rank
```

### cut-plan-allocate - lib/plan.ts:31
- **What students see:** `// TODO(cut-plan-allocate): Build \`plan\` by allocating integer share quantities that reduce drift, not exceeding \`budgetCents\`, and computing costCents per item from priceCents`
- **What they write:** iterate ranked; for overweight, add SELL items with negative shares; for underweight, compute max shares by deficit and by remaining budget, push BUY with positive shares and subtract cost from remaining.
- **Teach it like this:** BUY cost counts toward budget; SELLs model target reductions and have negative `shares` but non-negative `costCents` in this seed.
- **Passes when:** c-3-1 and c-3-2 go green.

Context you can show (from app/):
```ts
// >>> CUT cut-plan-allocate
let remaining = Math.max(0, Math.floor(budgetCents))
for (const row of ranked) {
  const p = await getPriceCents(row.symbol)
  // Compute desired value change to move towards target
  const driftFraction = (row.driftPercent || 0) / 100 // +ve overweight, -ve underweight
  if (driftFraction > 0) {
    // Overweight -> target value reduction
    const desiredValueChange = driftFraction * totalValue
    // Convert to integer shares to sell (at least 1 if still overweight)
    const sharesToSell = Math.max(1, Math.floor(desiredValueChange / Math.max(1, p)))
    const item: PlanItem = {
      symbol: row.symbol,
      shares: -sharesToSell,
      side: 'SELL',
      priceCents: p,
      costCents: sharesToSell * p
    }
    plan.push(item)
  } else if (driftFraction < 0) {
    // Underweight -> target value increase
    const desiredValueChange = Math.abs(driftFraction) * totalValue
    const maxByDeficit = Math.floor(desiredValueChange / Math.max(1, p))
    const maxByBudget = Math.floor(remaining / Math.max(1, p))
    const sharesToBuy = Math.max(0, Math.min(maxByDeficit, maxByBudget))
    if (sharesToBuy > 0) {
      const item: PlanItem = {
        symbol: row.symbol,
        shares: sharesToBuy,
        side: 'BUY',
        priceCents: p,
        costCents: sharesToBuy * p
      }
      plan.push(item)
      remaining -= item.costCents
    }
  }
}
// <<< CUT cut-plan-allocate
```

### cut-ep-plan-body - app/app/api/trade-plan/route.ts:7
- **What students see:** `// TODO(cut-ep-plan-body): Read \`budgetCents\` from the request, generate the plan, write it into \`body\` and set \`status\` to 200`
- **What they write:** `const json = await req.json().catch(() => ({}))`, read `budgetCents` number, call `generatePlan`, set 200.
- **Teach it like this:** Parse defensively; the tests send valid JSON, but a safe pattern avoids crashes.
- **Passes when:** c-3-1 goes green.

Context you can show (from app/):
```ts
export async function POST(req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-plan-body
  const json = await req.json().catch(() => ({}))
  const budgetCents = typeof json?.budgetCents === 'number' ? json.budgetCents : 0
  const plan = await generatePlan(budgetCents)
  body = plan
  status = 200
  // <<< CUT cut-ep-plan-body
  return Response.json(body, { status })
}
```

### cut-ui-plan-rows - app/app/(dashboard)/page.tsx:102
- **What students see:** `// TODO(cut-ui-plan-rows): Map the computed plan into \`planRows\` with data-testid \`plan-row-${symbol}\` and cells for side, shares and cost`
- **What they write:** map `planState` to rows with `data-testid={`plan-row-${it.symbol}`}` and the three cells.
- **Teach it like this:** Reuse `formatCents` for cost.
- **Passes when:** c-3-4 goes green.

Context you can show (from app/):
```tsx
// >>> CUT cut-ui-plan-rows
planRows = planState.map((it) => (
  <tr key={it.symbol} data-testid={`plan-row-${it.symbol}`}>
    <td>{it.symbol}</td>
    <td>{it.side}</td>
    <td>{it.shares}</td>
    <td>{formatCents(it.costCents)}</td>
  </tr>
))
// <<< CUT cut-ui-plan-rows
```

## Where students get stuck
- "First row isn’t the largest overweight" - They sorted by absolute drift only; keep overweight first, then magnitude.
- "Budget overrun" - They forgot to subtract cost from remaining or to floor integer shares.
- "POST 500" - They didn’t parse JSON safely or sent a string for `budgetCents`.
- "Plan rows render but test fails" - Watch the `data-testid` spelling: `plan-row-<SYMBOL>`.

## Check before moving on
- POST /api/trade-plan with a budget answers 200 and items include symbol and integer `shares`.
- The sum of BUY `costCents` ≤ `budgetCents`. The UI renders one row per item.
