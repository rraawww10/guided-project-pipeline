## Outcome
A small Next.js app that serves a seeded list of transactions, classifies each row with a deterministic, priority-ordered rule engine, and shows a live summary by category with “what-if” budget deltas. By the end:
- Session 1: GET /api/transactions answers with the seeded data and the page renders every row from the local API.
- Session 2: Each row shows its chosen category and which rule fired; a Summary section groups totals by category.
- Session 3: Per-category budget inputs recalculate delta/percent on the client; the summary can sort by delta and toggle to show only over‑budget categories.

## Out of scope
- Real money, dates, or time windows; recurring transactions.
- Persisting edited budgets; multiple users; auth.
- CSV import/export; external APIs; databases.

## Data model
Types (TypeScript):
- Transaction (Tx): { id: string; memo: string; merchant: string; amount: number } where amount < 0 for outflows (spend), amount > 0 for inflows (refunds/income).
- Category: one of ["Transport", "Supplies", "Expense", "Income", "Other"].
- Rule: { id: string; when: { memoContains?: string; merchantEquals?: string; amountLessThan?: number; amountGreaterThan?: number }; category: Category }.
- ClassifiedTx: Tx & { category: Category; ruleId: string }.
- SummaryRow: { category: Category; spent: number } where spent is computed as -sum(amount) per category (refunds decrease spend).
- WithDelta: SummaryRow & { budget: number; delta: number; pct: number } where delta = spent - budget and pct = budget > 0 ? (spent / budget) * 100 : 0.

Seed data (app/data/transactions.seed.json): 10–15 rows. Each Transaction in the seed and in the API response includes an id: string. The fixtures below elide ids for brevity; use any unique ids. Must include at least these fixtures (ids may vary, memos/merchants as written):
- { memo: "Uber trip downtown", merchant: "UBER", amount: -35.00 }
- { memo: "Groceries - FreshFarm", merchant: "FreshFarm", amount: -60.00 }
- { memo: "ACME paper", merchant: "ACME", amount: -25.00 }
- { memo: "Refund - FreshFarm", merchant: "FreshFarm", amount: 10.00 }
- { memo: "Uber refund", merchant: "UBER", amount: 15.00 }
- { memo: "Coffee", merchant: "Blue Bottle", amount: -5.00 }
- { memo: "Office chair", merchant: "OfficeCo", amount: -120.00 }

Default rules (ordered, first‑match wins):
1) merchant == "ACME" → Supplies
2) memo contains "uber" (case‑insensitive) → Transport
3) amount < 0 → Expense
4) amount > 0 → Income
Otherwise → Other

Summary math:
- Per category, spent = -sum(amount). Example with the fixtures above:
  - Transport: amounts [-35, +15] → spent = 20
  - Supplies: [-25] → 25
  - Expense: [-60, -5, -120] → 185
  - Income: [+10] → -10 (not used in budget checks)

## Endpoints
- ep-transactions-list: GET /api/transactions → 200 JSON array of Transaction from the seed file.

## Screens
- sc-dashboard (route "/")
  - Elements and hooks (stable, testable):
    - A table body of transaction rows; each row has data-testid="tx-row" and contains cells with data-testid="tx-memo" and, from session 2, data-testid="tx-category" and data-testid="tx-rule".
    - A Summary section container with data-testid="summary". Inside, zero or more rows with data-testid="summary-row"; each row has cells data-testid="summary-cat", data-testid="summary-total", and from session 3 data-testid="summary-delta" and data-testid="summary-pct".
    - From session 3: one input per category with data-testid="budget-<category>" (e.g., budget-Transport), a button with data-testid="sort-delta" to sort by delta descending, and a checkbox with data-testid="toggle-over" to show only categories with delta > 0.
  - States: loading, loaded (empty and non-empty), error.
  - This screen owns the fetch of GET /api/transactions in session 1.

## Sessions

### Session 1 - Setup and listing
Goal: Serve seeded transactions from a local API and render an ungrouped table. End: GET /api/transactions returns data and the page renders one row per transaction.

Teaches: Next.js route handler, fetching from a local API, React state/effect, rendering a repeated list with stable test hooks.

Acceptance criteria:
- c-1-1: GET /api/transactions returns 200 with a JSON array of Transaction (target: ep-transactions-list). Cuts: cut-api-transactions-list.
- c-1-2: Screen sc-dashboard renders one row per transaction (counts elements with data-testid="tx-row"). Cuts: cut-ui-fetch-transactions, cut-ui-render-rows.
- c-1-3: Screen sc-dashboard renders each row’s memo (find data-testid="tx-memo" in each tx-row). Cuts: cut-ui-render-rows.

Cut points:
- cut-api-transactions-list (app/api/transactions/route.ts, writes_into: body)
  Hint: Put every seeded transaction into `body` and set `status` to 200.
- cut-ui-fetch-transactions (app/page.tsx, writes_into: rows)
  Hint: Fetch "/api/transactions" once on load and write the parsed list into `rows`.
- cut-ui-render-rows (app/page.tsx, writes_into: rowsView)
  Hint: Build `rowsView` as one <tr data-testid="tx-row"> per item in `rows`, including a cell with data-testid="tx-memo" showing its memo.

---

### Session 2 - Allocation engine and summary
Goal: Classify each transaction with ordered rules and show a grouped summary with transparent traceability. End: every row shows its category and matching rule; the Summary section lists totals by category.

Teaches: Deterministic rule precedence (first-match wins), pure function design, grouping and stable ordering, rendering a secondary view from derived data.

Acceptance criteria:
- c-2-1: Screen sc-dashboard shows category "Transport" for the seeded "Uber trip downtown" row (reads data-testid="tx-category"). Cuts: cut-lib-apply-rules, cut-ui-render-category-cell.
- c-2-2: Screen sc-dashboard shows the matched rule label for the seeded "Uber trip downtown" row as "memo contains 'uber'" (reads data-testid="tx-rule"). Cuts: cut-lib-apply-rules, cut-ui-render-category-cell.
- c-2-3: Screen sc-dashboard Summary lists one row per category (data-testid="summary-row") and shows the total for Supplies as 25 (reads data-testid="summary-cat"=="Supplies" then data-testid="summary-total"). Cuts: cut-lib-summarize-by-category, cut-ui-render-summary.
- c-2-4: Screen sc-dashboard renders category "Transport" (not "Income") for the seeded "Uber refund" row (amount 15) in data-testid="tx-category". Cuts: cut-lib-apply-rules, cut-ui-render-category-cell.
- c-2-5: Screen sc-dashboard renders a visible heading "Summary by category" exactly once. Cuts: cut-ui-render-summary.
- c-2-6: Screen sc-dashboard Summary shows the Transport total as 20 (reads data-testid="summary-cat"=="Transport" then data-testid="summary-total"). Cuts: cut-lib-apply-rules, cut-lib-summarize-by-category, cut-ui-render-summary.

Cut points:
- cut-lib-apply-rules (lib/rules.ts, writes_into: out)
  Hint: Walk `rules` in order and set `out` to the first rule’s category whose conditions match `tx` (memoContains, merchantEquals, amountLessThan/GreaterThan); if none match, set `out` to "Other".
- cut-lib-summarize-by-category (lib/summary.ts, writes_into: out)
  Hint: Group the classified rows by category and write `out` as an array of { category, spent } where spent is -sum(amount) for that category, sorted by category name ascending.
- cut-ui-render-category-cell (app/page.tsx, writes_into: categoryCell)
  Hint: Build `categoryCell` so the row includes a <td data-testid="tx-category"> with the transaction’s category and a <td data-testid="tx-rule"> with the matched rule label.
- cut-ui-render-summary (app/page.tsx, writes_into: summaryView)
  Hint: Render a section titled "Summary by category" into `summaryView` with one <tr data-testid="summary-row"> per summary row, each showing data-testid="summary-cat" and data-testid="summary-total".
- cut-lib-compute-delta (lib/budgets.ts, writes_into: out)
  Hint: Join each summary row with its budget (default 0) and write `out` as { category, spent, budget, delta: spent - budget, pct: budget > 0 ? (spent / budget) * 100 : 0 }.

---

### Session 3 - Budgets, delta, sort and filter
Goal: Add client-side budgets and live deltas/percents; enable sorting and over‑budget filtering. End: editing a budget recomputes delta/percent; the table can sort by delta and toggle to over‑budget only.

Teaches: Controlled inputs and derived state, simple numeric transforms, list sorting and predicate filtering, UI toggles.

Acceptance criteria:
- c-3-1: After typing 30 into the Transport budget input (data-testid="budget-Transport"), the Transport row’s delta shows -10 (reads data-testid="summary-delta"). Cuts: cut-ui-budgets-state, cut-lib-compute-delta, cut-ui-render-delta.
- c-3-2: Clicking the Sort by delta button (data-testid="sort-delta") sorts summary rows by delta descending; with the fixtures and the step above, the first summary row is "Expense". Cuts: cut-lib-compute-delta, cut-ui-sort-by-delta, cut-ui-render-delta.
- c-3-3: Toggling Over budget only (data-testid="toggle-over") hides categories with delta ≤ 0; after the step above, Transport disappears while Expense remains. Cuts: cut-lib-compute-delta, cut-ui-toggle-overbudget, cut-ui-render-delta.
- c-3-4: The Percent column shows one decimal place; after the step above, Transport percent reads 66.7% (data-testid="summary-pct"). Cuts: cut-lib-compute-delta, cut-ui-render-delta.
- c-3-5: Screen sc-dashboard renders a visible column header "Delta" exactly once. Cuts: cut-ui-render-delta.

Cut points:
- cut-ui-budgets-state (app/page.tsx, writes_into: budgets)
  Hint: Maintain an in-memory `budgets` map from category to number and update `budgets` when a budget input changes (do not write to the server).
- cut-ui-render-delta (app/page.tsx, writes_into: summaryView)
  Hint: Extend `summaryView` to include Delta (data-testid="summary-delta") and Percent (data-testid="summary-pct") columns and render their values for each row, plus a visible "Delta" header.
- cut-ui-sort-by-delta (app/page.tsx, writes_into: sorted)
  Hint: When the Sort by delta button is clicked, order the displayed summary rows by descending `delta` and write the result into `sorted`.
- cut-ui-toggle-overbudget (app/page.tsx, writes_into: showOver)
  Hint: When the Over budget only checkbox is checked, set `showOver` and filter the displayed summary rows to those with `delta` > 0.
