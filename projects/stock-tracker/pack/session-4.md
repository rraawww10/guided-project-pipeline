# Session 4 - What‑if: edit targets and budget, persist and recompute

**Time:** 40 minutes
**Students start from:** Plan table renders from a fixed budget; inputs and save flow are TODO. PUT routes return 501.
**Students end with:** Editing a target and/or budget persists via PUT, refetches the plan, and shows a "Saved" notice.

## What they learn
- Controlled inputs bound to per-symbol target weights (fractions 0..1)
- PUT routes that upsert via Prisma and return 200
- Refetching dependent data after save to update the UI in place

## Before you start
- Keep dev server running.
- Open:
  - app/app/api/targets/route.ts
  - app/app/api/settings/route.ts
  - app/app/(dashboard)/page.tsx (targets/budget and onSave)
  - app/lib/prisma.ts (Prisma client wiring)

## The plan
| Minutes | What you do |
|---|---|
| 0-5 | Recap: targets are fractions (0..1), budget is cents. Show inputs UI. |
| 5-12 | Live-code cut-ep-targets-update: upsert weights per symbol, 200. |
| 12-18 | Live-code cut-ep-settings-update: persist budgetCents, 200. |
| 18-27 | Live-code cut-ui-target-inputs: seed `targetsState` from the report. |
| 27-35 | Live-code cut-ui-apply-edits: send targets and budget, refetch plan, set notice. |
| 35-38 | Students edit one symbol, click save, and confirm plan rows change for that symbol. |
| 38-40 | Wrap: notice uses the same testid as Apply. |

## Cut points in this session
### cut-ep-targets-update - app/app/api/targets/route.ts:7
- **What students see:** `// TODO(cut-ep-targets-update): Upsert incoming target weights and set \`status\` to 200`
- **What they write:** parse `[{symbol, weight}]`, validate types, `prisma.target.upsert({ where: { assetSymbol }, update: { weight }, create: { assetSymbol, weight } })`, return `{ ok: true }`, 200.
- **Teach it like this:** Upsert by `assetSymbol`; ignore invalid items.
- **Passes when:** c-4-1 goes green.

Context you can show (from app/):
```ts
// >>> CUT cut-ep-targets-update
const updates: Array<{ symbol: string; weight: number }> = await req.json().catch(() => [])
for (const u of updates) {
  if (!u || typeof u.symbol !== 'string' || typeof u.weight !== 'number') continue
  await prisma.target.upsert({
    where: { assetSymbol: u.symbol },
    update: { weight: u.weight },
    create: { assetSymbol: u.symbol, weight: u.weight }
  })
}
body = { ok: true }
status = 200
// <<< CUT cut-ep-targets-update
```

### cut-ep-settings-update - app/app/api/settings/route.ts:7
- **What students see:** `// TODO(cut-ep-settings-update): Persist the incoming \`budgetCents\` setting and set \`status\` to 200`
- **What they write:** parse JSON, read numeric `budgetCents`, upsert `{ key: 'budgetCents', value: String(Math.floor(budgetCents)) }`, return `{ ok: true }`, 200.
- **Teach it like this:** Persist as a string; normalise to an integer number of cents.
- **Passes when:** c-4-2 goes green.

Context you can show (from app/):
```ts
// >>> CUT cut-ep-settings-update
const json = await req.json().catch(() => ({}))
const budgetCents = typeof json?.budgetCents === 'number' ? json.budgetCents : undefined
if (typeof budgetCents === 'number') {
  await prisma.setting.upsert({
    where: { key: 'budgetCents' },
    update: { value: String(Math.floor(budgetCents)) },
    create: { key: 'budgetCents', value: String(Math.floor(budgetCents)) }
  })
}
body = { ok: true }
status = 200
// <<< CUT cut-ep-settings-update
```

### cut-ui-target-inputs - app/app/(dashboard)/page.tsx:87
- **What students see:** `// TODO(cut-ui-target-inputs): Keep edited weights in \`targetsState\` per symbol and bind each to an input with data-testid \`target-input-${symbol}\``
- **What they write:** on first report load, initialise `targetsState` from rows; inputs already bind `value` and `onChange` to that state.
- **Teach it like this:** This seed uses fractions 0..1; the inputs already have min/max/step.
- **Passes when:** enables c-4-3.

Context you can show (from app/):
```tsx
// >>> CUT cut-ui-target-inputs
useEffect(() => {
  if (reportState && Object.keys(targetsState).length === 0) {
    const init: Record<string, number> = {}
    for (const row of reportState) init[row.symbol] = row.targetWeight
    setTargetsState(init)
  }
}, [reportState])
// <<< CUT cut-ui-target-inputs
```

### cut-ui-apply-edits - app/app/(dashboard)/page.tsx:126
- **What students see:** `// TODO(cut-ui-apply-edits): On save, send edited targets and budget, then refresh \`planRefresh\` by refetching the plan so the rows reflect the new values, and show a 'Saved' notice (data-testid 'applied')`
- **What they write:** read latest input values, PUT `/api/targets` if any changed, PUT `/api/settings` with budget cents, POST `/api/trade-plan` to refresh `planState`, set notice to "Saved".
- **Teach it like this:** Read inputs from the DOM to avoid a React state race; tests await the recompute.
- **Passes when:** c-4-3 and c-4-4 go green.

Context you can show (from app/):
```tsx
// >>> CUT cut-ui-apply-edits
// Read the latest input values directly to avoid a race with React state batching
const inputs = Array.from(document.querySelectorAll<HTMLInputElement>('[data-testid^="target-input-"]'))
const edited: Array<{ symbol: string; weight: number }> = []
for (const inp of inputs) {
  const testid = inp.getAttribute('data-testid') || ''
  const symbol = testid.replace('target-input-', '')
  const val = parseFloat(inp.value)
  if (symbol && !Number.isNaN(val)) edited.push({ symbol, weight: val })
}
if (edited.length > 0) {
  await fetch('/api/targets', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(edited) })
}
const cents = parseInt(budgetInput || '0', 10) || 0
await fetch('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) })
const plan = await fetch('/api/trade-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) }).then((r) => r.json())
setPlanState(plan)
setNotice('Saved')
planRefresh = (planRefresh + 1) | 0
// <<< CUT cut-ui-apply-edits
```

## Where students get stuck
- "Saved but rows didn’t change" - They didn’t refetch the plan after PUTs; ensure the POST to `/api/trade-plan` runs last and updates `planState`.
- "Weights look like 12.5 not 0.125" - Inputs accept fractions 0..1 for targets in this project; adjust test data and state accordingly.
- "Budget looks like dollars" - The UI and server both use raw cents.
- "Notice test fails" - The test reads `data-testid="applied"` even for Saved. Set `setNotice('Saved')` and leave the testid as-is.

## Check before moving on
- PUT /api/targets and PUT /api/settings both return 200.
- After editing one target and clicking Save, the plan shows a different `shares` for that symbol; saving with no changes shows a visible "Saved" notice and plan rows are unchanged.
