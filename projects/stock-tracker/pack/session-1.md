# Session 1 - Seed, positions API, and table

**Time:** 40 minutes
**Students start from:** Next dev server boots; the page renders headings and shows a blank table. API handlers return 501 with TODOs.
**Students end with:** GET /api/positions returns rows; the table renders one row per position and a current-weight % cell.

## What they learn
- Prisma seed and reading from the store (already seeded for them)
- Next.js route handler (GET) that responds with JSON and status 200
- Mapping data to JSX rows with stable data-testids
- Computing a percent string to one decimal place

## Before you start
- Run the app:
  - cd projects/stock-tracker/app
  - npm ci
  - npm run dev and open http://localhost:3000
- Open these files side by side:
  - app/app/api/positions/route.ts
  - app/app/(dashboard)/page.tsx
  - app/lib/store.ts (to see getPositions)

## The plan
| Minutes | What you do |
|---|---|
| 0-5 | Recap the goal. Show the empty table at /. Point at the positions endpoint TODO. |
| 5-15 | Live-code cut-ep-positions-body: return Position[] from the store and 200. |
| 15-25 | Live-code cut-ui-positions-rows: render one <tr> per position with the required testids and cells. |
| 25-30 | Live-code cut-ui-weight-cell: compute and render a one-decimal percent in the pos-weight cell. |
| 30-38 | Students finish wiring rows/weight; you circulate. |
| 38-40 | Confirm rows render and the weight cell ends with %. Preview allocation math next. |

## Cut points in this session
### cut-ep-positions-body - app/app/api/positions/route.ts:10
- **What students see:** `// TODO(cut-ep-positions-body): Put every position with symbol, name, shares, priceCents and targetWeight into \`body\` and set \`status\` to 200`
- **What they write:** read all positions from the store, map only the required fields into `body`, and set `status = 200`.
- **Teach it like this:** The handler builds a typed fallback and you replace the assignment. Keep return outside the cut.
- **Passes when:** criterion c-1-1 goes green.

Context you can show (from app/):

```ts
export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-positions-body
  const positions = await getPositions()
  body = positions.map((p) => ({
    symbol: p.symbol,
    name: p.name,
    shares: p.shares,
    priceCents: p.priceCents,
    targetWeight: p.targetWeight
  }))
  status = 200
  // <<< CUT cut-ep-positions-body
  return Response.json(body, { status })
}
```

### cut-ui-positions-rows - app/app/(dashboard)/page.tsx:32
- **What students see:** `// TODO(cut-ui-positions-rows): Build \`rows\` so it renders one <tr> per position with data-testid \`pos-row-${symbol}\` and cells for symbol, shares, price and target weight`
- **What they write:** set `rows = positions.map(...)` with a `<tr key>` per symbol, `data-testid={`pos-row-${p.symbol}`}`, and `<td>` cells for symbol, shares, formatted price, target % and weight cell.
- **Teach it like this:** The rows mirror the API shape. Use the provided `formatCents` for price. Testids must match exactly.
- **Passes when:** criterion c-1-2 goes green (and supports c-1-3).

Context you can show (from app/):

```tsx
let rows: JSX.Element[] = []
// >>> CUT cut-ui-positions-rows
rows = positions.map((p) => {
  const weightText = weightTextFor(p.shares, p.priceCents, totalValue)
  return (
    <tr key={p.symbol} data-testid={`pos-row-${p.symbol}`}>
      <td>{p.symbol}</td>
      <td>{p.shares}</td>
      <td>{formatCents(p.priceCents)}</td>
      <td>{(p.targetWeight * 100).toFixed(1)}%</td>
      <td data-testid={`pos-weight-${p.symbol}`}>{weightText}</td>
    </tr>
  )
})
// <<< CUT cut-ui-positions-rows
```

### cut-ui-weight-cell - app/app/(dashboard)/page.tsx:24
- **What students see:** `// TODO(cut-ui-weight-cell): Compute \`weightText\` for a row as the current weight percentage to one decimal place (e.g. '12.3%') and render it in the cell with data-testid \`pos-weight-${symbol}\``
- **What they write:** define `weightTextFor(shares, priceCents, total)` to return `(shares*price/total)*100` formatted with `toFixed(1) + '%'`; handle total 0.
- **Teach it like this:** Compute a fraction then format as percent with one decimal place; `toFixed` returns a string.
- **Passes when:** criterion c-1-3 goes green.

Context you can show (from app/):

```ts
// Provide a binding the row renderer can call. Default does NOT satisfy the percentage regex.
let weightTextFor: (shares: number, priceCents: number, totalValue: number) => string = () => 'N/A'
// >>> CUT cut-ui-weight-cell
weightTextFor = (shares: number, priceCents: number, totalValue: number) => {
  const w = totalValue > 0 ? (shares * priceCents) / totalValue : 0
  return `${(w * 100).toFixed(1)}%`
}
// <<< CUT cut-ui-weight-cell
```

## Where students get stuck
- "My rows render but the test still fails" - The data-testid must be exactly `pos-row-<SYMBOL>`; check casing and template literal braces.
- "Percent shows 12% not 12.3%" - They forgot `toFixed(1)` or to multiply by 100.
- "/api/positions still returns 501" - They set `body` but not `status = 200`.
- "Import path error in route.ts" - Use `import { getPositions } from '../../../lib/store'` (three `../`).

## Check before moving on
- The page shows one row per position and a current weight cell ending with `%`. GET /api/positions answers 200 with the required fields.
