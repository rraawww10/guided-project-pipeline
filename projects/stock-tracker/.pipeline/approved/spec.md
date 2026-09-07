# Portfolio Rebalancer

A Next.js + Prisma app that reads a seeded portfolio, computes drift from target weights, generates a concrete trade plan under a cash cap, and applies the plan to update holdings. One dashboard screen evolves over five sessions, with deterministic data and no external APIs.

## Outcome
- A working dashboard at "/" that lists current positions, shows overweight/underweight drift, proposes an integer-share trade plan under a cash budget, lets the user edit targets and budget, and applies the plan to update holdings.
- A small JSON API that powers the UI: positions, allocation report, trade plan, settings updates, and plan application.
- Deterministic behaviour from a Prisma + SQLite seed with no real-time clock and no network calls.

## Out of scope
- Live market data, brokerage integrations, authentication, real orders, and charts.
- Fractional shares, fees, slippage, or tax lots.

## Data model
- Asset: symbol (PK, string), name (string), lotSize (integer, shares per lot).
- Holding: assetSymbol (FK -> Asset.symbol), shares (integer).
- Price: assetSymbol (FK -> Asset.symbol), priceCents (integer).
- Target: assetSymbol (FK -> Asset.symbol), weight (decimal 0..1).
- Trade: id (PK), assetSymbol, shares (integer, positive = buy, negative = sell), priceCents (integer), createdNote (string). Used only for simulated apply.
- Setting: single-row key/value store for budgetCents (integer). Budget is also editable in the UI.

All tables are seeded with a small fixed set of assets, holdings, prices and targets. No timestamps are read; all recomputation is deterministic from stored values.

## Endpoints
- ep-positions-list: GET /api/positions → 200 with Position[]: {symbol, name, shares, priceCents, targetWeight}.
- ep-allocation-report: GET /api/allocation → 200 with AllocationRow[]: {symbol, valueCents, currentWeight, targetWeight, driftPercent}.
- ep-plan-generate: POST /api/trade-plan with {budgetCents: number} → 200 with TradeItem[]: {symbol, shares, side: "BUY"|"SELL", priceCents, costCents}.
- ep-targets-update: PUT /api/targets with TargetUpdate[]: {symbol, weight} → 200 with {ok: true}.
- ep-settings-update: PUT /api/settings with {budgetCents: number} → 200 with {ok: true}.
- ep-apply-plan: POST /api/apply-plan → 200 with {applied: number, updatedHoldings: Holding[]}.
- ep-trades-list: GET /api/trades → 200 with Trade[]: {id, symbol, shares, priceCents}.

## Screens
- sc-dashboard (route "/")
  - Elements: positions table (data-testid="pos-row-<SYMBOL>"), current weight cell (data-testid="pos-weight-<SYMBOL>"), drift badge per row showing "OVER" or "UNDER" (data-testid="drift-<SYMBOL>"), plan table (data-testid="plan-row-<SYMBOL>"), target weight inputs (data-testid="target-input-<SYMBOL>"), budget input (data-testid="budget-input"), save button (data-testid="save-settings"), apply button (data-testid="apply-plan"), applied notice (data-testid="applied"), loading state (text "Loading...").
  - States: empty, loaded, loading, saving, applied.

## Sessions

### Session 1 - Seed, positions API, and table
Goal: Boot the project, create the schema and seed, and render a positions table that joins holdings with targets and prices.

Teaches: Prisma schema + seed, GET route handler in Next, mapping data to JSX rows with testids.

Acceptance criteria
- c-1-1: GET /api/positions returns 200 with a JSON array of Position objects that each include symbol, shares, priceCents and targetWeight. Targets: ep-positions-list. Cuts: [cut-ep-positions-body].
- c-1-2: sc-dashboard renders one row per position with data-testid of the form "pos-row-<SYMBOL>". Targets: sc-dashboard. Cuts: [cut-ui-positions-rows].
- c-1-3: sc-dashboard shows current weight as a percentage in a cell with data-testid "pos-weight-<SYMBOL>" (e.g. ends with "%"). Targets: sc-dashboard. Cuts: [cut-ui-positions-rows, cut-ui-weight-cell].

Cut points
- cut-ep-positions-body (app/api/positions/route.ts, writes_into=body): Put every position with symbol, name, shares, priceCents and targetWeight into `body` and set `status` to 200.
- cut-ui-positions-rows (app/(dashboard)/page.tsx, writes_into=rows): Build `rows` so it renders one <tr> per position with data-testid `pos-row-${symbol}` and cells for symbol, shares, price and target weight.
- cut-ui-weight-cell (app/(dashboard)/page.tsx, writes_into=weightText): Compute `weightText` for a row as the current weight percentage to one decimal place (e.g. "12.3%") and render it in the cell with data-testid `pos-weight-${symbol}`.

### Session 2 - Allocation report and drift highlight
Goal: Compute current weights and drift per symbol and expose them via an API; highlight over/under-weight rows in the UI.

Teaches: Weight normalisation by total value, pure calculation module, client data fetching, conditional UI badges.

Acceptance criteria
- c-2-1: GET /api/allocation returns 200 with a JSON array whose items include symbol, currentWeight, targetWeight and driftPercent (positive for overweight, negative for underweight). Targets: ep-allocation-report. Cuts: [cut-calc-weights, cut-ep-allocation-body].
- c-2-2: sc-dashboard shows an "OVER" badge (data-testid "drift-<SYMBOL>") for at least one overweight symbol from the seed. Targets: sc-dashboard. Cuts: [cut-ui-fetch-allocation, cut-ui-drift-badge].
- c-2-3: sc-dashboard shows an "UNDER" badge (data-testid "drift-<SYMBOL>") for at least one underweight symbol from the seed. Targets: sc-dashboard. Cuts: [cut-ui-fetch-allocation, cut-ui-drift-badge].
- c-2-4: While the allocation report is loading, the page shows the text "Loading...". Targets: sc-dashboard. Cuts: [cut-ui-fetch-allocation].
- c-2-5: GET /api/allocation returns 200 and the sum of all currentWeight values across items equals 1.000 when rounded to three decimal places. Targets: ep-allocation-report. Cuts: [cut-calc-weights].

Cut points
- cut-calc-weights (lib/allocation.ts, writes_into=weights): Build `weights` as an array of {symbol, valueCents, currentWeight, targetWeight, driftPercent} by dividing each position's value by the portfolio total and subtracting the target weight.
- cut-ep-allocation-body (app/api/allocation/route.ts, writes_into=body): Put every allocation row computed from the store into `body` and set `status` to 200.
- cut-ui-fetch-allocation (app/(dashboard)/page.tsx, writes_into=report): Load the allocation report into `report` and render a visible "Loading..." text while `report` is undefined.
- cut-ui-drift-badge (app/(dashboard)/page.tsx, writes_into=driftClass): Set `driftClass`/label on each row so overweight shows a badge with text "OVER" and underweight shows "UNDER" at data-testid `drift-${symbol}`.

### Session 3 - Trade plan under budget
Goal: Generate a deterministic integer-share trade plan given a cash budget, and show it in the UI.

Teaches: Ranking by drift, greedy distribution under a cap, integer rounding to whole shares, POST route with JSON body.

Acceptance criteria
- c-3-1: POST /api/trade-plan with {budgetCents} returns 200 with a JSON array of items that each include symbol and an integer shares field. Targets: ep-plan-generate. Cuts: [cut-plan-allocate, cut-ep-plan-body].
- c-3-2: POST /api/trade-plan with {budgetCents} returns 200 and the sum of costCents across BUY items is less than or equal to budgetCents. Targets: ep-plan-generate. Cuts: [cut-plan-allocate].
- c-3-3: POST /api/trade-plan with {budgetCents} returns 200 and the first plan item's symbol corresponds to the candidate with the largest absolute positive drift. Targets: ep-plan-generate. Cuts: [cut-plan-rank].
- c-3-4: sc-dashboard renders one row per plan item with data-testid of the form "plan-row-<SYMBOL>". Targets: sc-dashboard. Cuts: [cut-ui-plan-rows].

Cut points
- cut-plan-rank (lib/plan.ts, writes_into=ranked): Build `ranked` as symbols ordered by absolute drift descending, breaking ties by symbol ascending to be deterministic.
- cut-plan-allocate (lib/plan.ts, writes_into=plan): Build `plan` by allocating integer share quantities that reduce drift, not exceeding `budgetCents`, and computing costCents per item from priceCents.
- cut-ep-plan-body (app/api/trade-plan/route.ts, writes_into=body): Read `budgetCents` from the request, generate the plan, write it into `body` and set `status` to 200.
- cut-ui-plan-rows (app/(dashboard)/page.tsx, writes_into=planRows): Map the computed plan into `planRows` with data-testid `plan-row-${symbol}` and cells for side, shares and cost.

### Session 4 - What‑if: edit targets and budget, persist and recompute
Goal: Allow editing target weights and the cash budget, persist them, and recompute the plan in-place.

Teaches: Controlled inputs, PUT routes that persist via Prisma, refetching dependent data after a save.

Acceptance criteria
- c-4-1: PUT /api/targets with a changed {symbol, weight} returns 200. Targets: ep-targets-update. Cuts: [cut-ep-targets-update].
- c-4-2: PUT /api/settings with a changed {budgetCents} returns 200. Targets: ep-settings-update. Cuts: [cut-ep-settings-update].
- c-4-3: After editing a target weight and clicking save, sc-dashboard renders a different shares value for that symbol in the plan table. Targets: sc-dashboard. Cuts: [cut-ui-target-inputs, cut-ui-apply-edits].
- c-4-4: Clicking save with no changes shows a visible "Saved" notice without changing the plan rows. Targets: sc-dashboard. Cuts: [cut-ui-apply-edits].

Cut points
- cut-ep-targets-update (app/api/targets/route.ts, writes_into=status): Upsert incoming target weights and set `status` to 200.
- cut-ep-settings-update (app/api/settings/route.ts, writes_into=status): Persist the incoming `budgetCents` setting and set `status` to 200.
- cut-ui-target-inputs (app/(dashboard)/page.tsx, writes_into=targetsState): Keep edited weights in `targetsState` per symbol and bind each to an input with data-testid `target-input-${symbol}`.
- cut-ui-apply-edits (app/(dashboard)/page.tsx, writes_into=planRefresh): On save, send edited targets and budget, then refresh `planRefresh` by refetching the plan so the rows reflect the new values, and show a "Saved" notice (data-testid "applied").

### Session 5 - Apply plan and reconcile
Goal: Apply the proposed plan to holdings, write simulated trades, refresh the view, and show reduced residual drift.

Teaches: Server-side reconciliation, posting actions from the UI.

Acceptance criteria
- c-5-1: POST /api/apply-plan returns 200 with a JSON body that includes an "applied" count greater than 0. Targets: ep-apply-plan. Cuts: [cut-ep-apply-plan, cut-ep-trade-record].
- c-5-2: After clicking Apply Plan, sc-dashboard refreshes and shows a visible notice (data-testid "applied"). Targets: sc-dashboard. Cuts: [cut-ui-apply-click].
- c-5-3: GET /api/trades returns 200 with a JSON array of Trade objects that include symbol and shares. Targets: ep-trades-list. Cuts: [cut-ep-trades-list-body].
- c-5-4: After applying, the average absolute drift across all symbols from GET /api/allocation is lower than it was before applying. Targets: ep-allocation-report. Cuts: [cut-reconcile-holdings].
- c-5-5: POST /api/apply-plan returns 200 with a JSON body that includes updatedHoldings whose length equals the number of assets. Targets: ep-apply-plan. Cuts: [cut-ep-apply-plan].

Cut points
- cut-ep-apply-plan (app/api/apply-plan/route.ts, writes_into=body): Compute the current plan, apply it, write `{ applied, updatedHoldings }` into `body` and set `status` to 200.
- cut-reconcile-holdings (lib/reconcile.ts, writes_into=updatedHoldings): Build `updatedHoldings` by applying each TradeItem's integer shares to the corresponding Holding and persisting the new share counts.
- cut-ui-apply-click (app/(dashboard)/page.tsx, writes_into=afterState): On click of the apply button, call the apply endpoint, refresh the positions/allocation, set `afterState` so the notice (data-testid "applied") is visible, and re-render the tables.
- cut-ep-trade-record (app/api/apply-plan/route.ts, writes_into=created): Insert one Trade per plan item and set `created` to the number inserted.
- cut-ep-trades-list-body (app/api/trades/route.ts, writes_into=body): Put every recorded Trade into `body` and set `status` to 200.
