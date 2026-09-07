# Session 5 - Apply plan and reconcile

**Time:** 40 minutes
**Students start from:** Plan renders and settings save; apply endpoint and trades list are TODO. The Apply button has no effect yet.
**Students end with:** Clicking Apply posts to the server, records trades, updates holdings, reduces drift, refreshes the UI, and shows an "Applied" notice.

## What they learn
- Server-side reconciliation that writes to Prisma
- Recording trades when applying a plan
- Refreshing the UI after a write action

## Before you start
- Keep dev server running.
- Open:
  - app/app/api/apply-plan/route.ts
  - app/lib/reconcile.ts
  - app/app/api/trades/route.ts
  - app/app/(dashboard)/page.tsx (onApply)

## The plan
| Minutes | What you do |
|---|---|
| 0-6 | Recap the end-to-end flow: record trades, apply to holdings, refresh view. |
| 6-18 | Live-code cut-ep-trade-record: read persisted budget, generate plan, createMany trades, set `created`. |
| 18-25 | Live-code cut-ep-apply-plan: recompute plan, apply trades, return `{ applied, updatedHoldings }`. |
| 25-30 | Live-code cut-reconcile-holdings: upsert holdings per item, return all holdings. |
| 30-34 | Live-code cut-ep-trades-list-body: list trades for verification. |
| 34-37 | Live-code cut-ui-apply-click: POST apply, then refetch positions/allocation/plan, set notice. |
| 37-40 | Students verify drift average is lower and notice shows. |

## Cut points in this session
### cut-ep-trade-record - app/app/api/apply-plan/route.ts:13
- **What students see:** `// TODO(cut-ep-trade-record): Insert one Trade per plan item and set \`created\` to the number inserted`
- **What they write:** read persisted `budgetCents` from settings, generate the plan, `prisma.trade.createMany` for items, assign `created` from the result.
- **Teach it like this:** Apply uses persisted settings; no request body.
- **Passes when:** contributes to c-5-1 (applied > 0).

Context you can show (from app/):
```ts
// >>> CUT cut-ep-trade-record
// Read persisted budget, generate the deterministic plan for this request,
// and record one Trade per item. Assign the inserted count into `created`.
const recBudgetSetting = await prisma.setting.findUnique({ where: { key: 'budgetCents' } })
const recBudgetCents = recBudgetSetting ? parseInt(recBudgetSetting.value, 10) || 0 : 0
const recordPlan = await generatePlan(recBudgetCents)
if (recordPlan.length > 0) {
  const payload = recordPlan.map((it) => ({
    assetSymbol: it.symbol,
    shares: it.shares,
    priceCents: it.priceCents,
    createdNote: 'apply-plan'
  }))
  const res = await prisma.trade.createMany({ data: payload })
  created = (res as any).count ?? recordPlan.length
}
// <<< CUT cut-ep-trade-record
```

### cut-ep-apply-plan - app/app/api/apply-plan/route.ts:33
- **What students see:** `// TODO(cut-ep-apply-plan): Compute the current plan, apply it, write \`{ applied, updatedHoldings }\` into \`body\` and set \`status\` to 200`
- **What they write:** read persisted budget again, generate plan, `applyTrades(plan)`, return body with `applied: created` and `updatedHoldings`.
- **Teach it like this:** The record and apply steps each recompute from the same settings for determinism.
- **Passes when:** c-5-1 and c-5-5 go green.

Context you can show (from app/):
```ts
// >>> CUT cut-ep-apply-plan
// Compute the current plan independently, then apply it to holdings. If the
// record step above inserted trades, we still report its `created` count in
// the response so tests can assert `applied > 0`.
const appBudgetSetting = await prisma.setting.findUnique({ where: { key: 'budgetCents' } })
const appBudgetCents = appBudgetSetting ? parseInt(appBudgetSetting.value, 10) || 0 : 0
plan = await generatePlan(appBudgetCents)
const updatedHoldings = await applyTrades(plan)
body = { applied: created, updatedHoldings }
status = 200
// <<< CUT cut-ep-apply-plan
```

### cut-reconcile-holdings - app/lib/reconcile.ts:8
- **What students see:** `// TODO(cut-reconcile-holdings): Build \`updatedHoldings\` by applying each TradeItem's integer shares to the corresponding Holding and persisting the new share counts`
- **What they write:** for each item, `findUnique` holding, compute `nextShares = max(0, existing + delta)`, `upsert`, then read all holdings and map to `{ assetSymbol, shares }`.
- **Teach it like this:** BUY is positive, SELL negative; clamp at 0.
- **Passes when:** c-5-4 goes green.

Context you can show (from app/):
```ts
// >>> CUT cut-reconcile-holdings
// Apply each trade's shares (BUY positive, SELL negative) to holdings
for (const item of plan) {
  const sym = item.symbol
  const delta = item.shares
  const existing = await prisma.holding.findUnique({ where: { assetSymbol: sym } })
  const nextShares = Math.max(0, (existing?.shares ?? 0) + delta)
  await prisma.holding.upsert({
    where: { assetSymbol: sym },
    update: { shares: nextShares },
    create: { assetSymbol: sym, shares: nextShares }
  })
}
const all = await prisma.holding.findMany({ orderBy: { assetSymbol: 'asc' } })
updatedHoldings = all.map((h) => ({ assetSymbol: h.assetSymbol, shares: h.shares }))
// <<< CUT cut-reconcile-holdings
```

### cut-ep-trades-list-body - app/app/api/trades/route.ts:10
- **What students see:** `// TODO(cut-ep-trades-list-body): Put every recorded Trade into \`body\` and set \`status\` to 200`
- **What they write:** `findMany` trades and map to `{ id, symbol, shares, priceCents }`, 200.
- **Teach it like this:** Order by id asc so tests read a stable sequence.
- **Passes when:** c-5-3 goes green.

Context you can show (from app/):
```ts
// >>> CUT cut-ep-trades-list-body
const trades = await prisma.trade.findMany({ orderBy: { id: 'asc' } })
body = trades.map((t) => ({ id: t.id, symbol: t.assetSymbol, shares: t.shares, priceCents: t.priceCents }))
status = 200
// <<< CUT cut-ep-trades-list-body
```

### cut-ui-apply-click - app/app/(dashboard)/page.tsx:151
- **What students see:** `// TODO(cut-ui-apply-click): On click of the apply button, call the apply endpoint, refresh the positions/allocation, set \`afterState\` so the notice (data-testid 'applied') is visible, and re-render the tables`
- **What they write:** POST `/api/apply-plan`, then refetch positions, allocation and plan; update state and set notice to "Applied".
- **Teach it like this:** Refresh all three so both tables reflect the new holdings.
- **Passes when:** c-5-2 goes green.

Context you can show (from app/):
```tsx
// >>> CUT cut-ui-apply-click
await fetch('/api/apply-plan', { method: 'POST' })
// Refresh positions and allocation and plan
const [newPositions, newReport] = await Promise.all([
  fetch('/api/positions').then((r) => r.json()),
  fetch('/api/allocation').then((r) => r.json())
])
setPositions(newPositions)
setReportState(newReport)
const cents = parseInt(budgetInput || '0', 10) || 0
const newPlan = await fetch('/api/trade-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) }).then((r) => r.json())
setPlanState(newPlan)
setNotice('Applied')
afterState = 'applied'
// <<< CUT cut-ui-apply-click
```

## Where students get stuck
- "Applied returns applied=0" - They didn’t create any trades; ensure `createMany` runs and `created` is set.
- "Holdings didn’t change" - `applyTrades` didn’t upsert or refetch holdings at the end.
- "UI didn’t update" - They only posted apply; you must refetch positions, allocation, and plan.
- "Trades list test fails" - Remember to map `assetSymbol` → `symbol` in the response and order by id asc.

## Check before moving on
- POST /api/apply-plan returns 200 with `applied > 0` and `updatedHoldings` length equals the number of assets.
- GET /api/trades returns a non-empty array.
- After applying, the average absolute drift from GET /api/allocation is lower than before.
