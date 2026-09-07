# Troubleshooting

Real errors students will hit and how to fix them fast.

API handlers
- Symptom: "Expected 200 but got 501" on an API.
  - Cause: They set `body` but not `status = 200` inside the cut.
  - Say: “Keep the return outside the block and assign both `body` and `status`.”

- Symptom: POST /api/trade-plan 500s or returns an empty plan.
  - Cause: Didn’t parse JSON safely or read `budgetCents` as a number.
  - Say: “`const json = await req.json().catch(() => ({}))` and guard `typeof json?.budgetCents === 'number'`.”

- Symptom: PUT routes crash with unique constraint errors.
  - Cause: Used `create` instead of `upsert` on `assetSymbol` (targets/holdings) or `key` (settings).
  - Say: “Use `upsert({ where, update, create })` with the correct unique field.”

- Symptom: Trades list shape doesn’t match tests.
  - Cause: Returned Prisma rows directly.
  - Say: “Map to `{ id, symbol: assetSymbol, shares, priceCents }` and order by `id: 'asc'`.”

Math and ranking
- Symptom: c-2-5 fails (weights don’t sum to 1.000 at 3dp).
  - Cause: Summed rounded items or forgot the `total > 0 ? ... : 0` guard.
  - Say: “Sum raw fractions; compute each weight as value/total.”

- Symptom: c-3-3 fails (first plan item wrong).
  - Cause: Sorted only by absolute drift or missed the tie-break.
  - Say: “Overweight first, then abs(magnitude) desc, tie-break `symbol` asc.”

- Symptom: c-3-2 fails (budget overrun).
  - Cause: Didn’t subtract BUY cost from remaining, or didn’t floor to integer shares.
  - Say: “`remaining -= item.costCents`; compute `Math.floor` shares.”

UI wiring
- Symptom: c-1-2 fails though rows appear.
  - Cause: `data-testid` typo or wrong symbol casing.
  - Say: “Must be exactly `pos-row-<SYMBOL>`.”

- Symptom: c-1-3 fails (weight cell).
  - Cause: Forgot `toFixed(1)` or to multiply by 100.
  - Say: “Return a string like `${(w * 100).toFixed(1)}%`.”

- Symptom: c-2-4 fails (Loading... not visible).
  - Cause: Didn’t clear to `undefined` before fetch or removed the small delay.
  - Say: “Set `reportState(undefined)` then fetch; keep the 50ms `setTimeout`.”

- Symptom: c-4-3 fails (editing target doesn’t change plan rows).
  - Cause: Didn’t refetch the plan after PUTs, or inputs bound to wrong unit.
  - Say: “POST `/api/trade-plan` after saving; targets are fractions 0..1.”

- Symptom: c-5-2 fails (notice missing).
  - Cause: Set a different testid for Saved/Applied.
  - Say: “Tests look for `data-testid="applied"` for both messages; set `setNotice('Saved'|'Applied')`.”

Prisma and install
- Symptom: "Prisma Client not known to Node" or similar.
  - Cause: `node_modules` missing or client not generated.
  - Say: “From app/, run `npm ci` (postinstall runs `prisma generate`, `db push` and seeds).”

- Symptom: Seeded values don’t match after experiments.
  - Cause: DB mutated across runs.
  - Say: “Re-seed with `node prisma/seed.js` (already in postinstall) or `npm ci` to start clean.”

Import paths
- Symptom: TS cannot find module '../../../lib/...'.
  - Cause: Wrong number of `../` from route handlers.
  - Say: “From app/app/api/*, imports are `../../../lib/...`.”

Notes on caching
- Some API routes declare `export const dynamic = 'force-dynamic'` so results reflect new DB state after applies. Don’t remove it while teaching.
