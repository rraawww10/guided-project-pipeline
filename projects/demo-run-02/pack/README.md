FairShare: Expense Settlement Calculator

One-page: A small Next.js app that reads a seeded list of shared expenses and shows an expenses table, per-person net balances in integer cents, and a proposed set of transfers (who pays whom). Session 3 adds a minimal-mode ordering and include/exclude per person.

How to run
- Node 18+ installed.
- In a fresh clone, run from the app directory:
  - npm ci
  - npm run dev
- Visit http://localhost:3000.
- Build/start for a production check:
  - npm run build
  - npm start

What’s in this project
- API
  - GET /api/expenses → seeded Expense[]
  - GET /api/settlement/naive → Transfer[] computed from current balances
- UI
  - route "/" renders:
    - expenses table [data-testid="expense-row"]
    - balances list [data-testid="balance-row"]
    - proposed transfers list [data-testid="transfer-row"]
    - transfers total [data-testid="transfers-total"]
    - include/exclude checkboxes [data-testid="include-<name>"]
    - minimal transfers toggle [data-testid="toggle-minimal"]
    - formatting probe [data-testid="money-sample"] showing formatMoney(-615)

Files you will open during teaching
- app/app/page.tsx — fetch, totals-paid summary, balances, transfers, toggle handlers
- app/app/api/expenses/route.ts — list expenses endpoint
- app/app/api/settlement/naive/route.ts — naive transfers endpoint
- app/lib/settlement.ts — computeBalances, settleNaive, settleMinimal
- app/lib/money.ts — formatMoney helper
- app/data/expenses.seed.json — the seed data used by the API

Sessions at a glance
- Session 1 (40 min): Boot + GET /api/expenses + render table + per-person totals-paid.
- Session 2 (40 min): Net balances + naive settlement on the page + naive settlement API.
- Session 3 (40 min): Integer-safe formatting, minimal-mode ordering, include/exclude recompute.

Tip for live-coding
- Keep integers end-to-end (cents). Avoid floats.
- Derive Set/objects immutably so useMemo/useEffect dependencies trigger.
- Keep ordering deterministic: sort by name ASC for display; transfers by amount DESC then payer then payee when minimal mode is ON.
