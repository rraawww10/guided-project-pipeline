Rule-Based Budget Allocator (ui-live-01)

One page for the instructor. This project is a small Next.js app that:
- serves a seeded list of transactions from a local API;
- classifies each row with a deterministic, priority‑ordered rule engine;
- shows a live summary by category with “what‑if” budget deltas.

How to run it
- Requirements: Node 18+.
- From projects/ui-live-01/app:
  - npm install
  - npm run dev
  - Open http://localhost:3000
- Seed data lives at app/data/transactions.seed.json. The API is GET /api/transactions and reads that file at runtime.

Stable UI hooks (tests use these)
- Transaction table rows: <tr data-testid="tx-row"> with a cell <td data-testid="tx-memo">.
- From session 2: each row also renders <td data-testid="tx-category"> and <td data-testid="tx-rule">.
- Summary section container: data-testid="summary". Rows: <tr data-testid="summary-row"> with cells data-testid="summary-cat" and data-testid="summary-total".
- From session 3: Delta and Percent cells data-testid="summary-delta" and data-testid="summary-pct"; budget inputs data-testid="budget-<Category>"; a button data-testid="sort-delta" and a checkbox data-testid="toggle-over".

Default rule order (first‑match wins)
1) merchant == "ACME" → Supplies
2) memo contains "uber" (case‑insensitive) → Transport
3) amount < 0 → Expense
4) amount > 0 → Income
Otherwise → Other

Sessions at a glance (40 min each)
1) Setup and listing: build the API and render the ungrouped table from it.
2) Allocation engine and summary: pure functions to classify and to group, render category/rule cells and the summary.
3) Budgets, delta, sort and filter: client‑side budgets, delta/percent display, sort by delta, and over‑budget toggle.

What to have open when teaching
- app/api/transactions/route.ts
- app/page.tsx
- app/lib/rules.ts, app/lib/summary.ts, app/lib/budgets.ts (from session 2)
- app/lib/types.ts (for reference)

Cut markers and skeleton
- Students start from skeleton/, which contains TODO lines for each cut. The exact locations are recorded in skeleton/.cut-manifest.json.
- Every code example in this pack is copied from app/ so the guide always matches the shipped solution.
