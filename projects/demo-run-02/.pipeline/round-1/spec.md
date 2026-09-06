# FairShare: Expense Settlement Calculator

## Outcome
A small Next.js + React + TypeScript app that reads a seeded set of shared expenses, shows them in a table with per-person totals, and computes a deterministic "who pays whom" settlement. By the end, the API answers a computed summary (balances and proposed transfers), the UI renders the list of transfers, integer-safe currency formatting is applied, and a simple include/exclude toggle lets the user recompute without a reload.

## Out of scope
- Real currencies/locales, multi-currency, persistence beyond the seed data, or authentication.
- Importing from external services or using timers/real dates.

## Data model
- Person: string (name used as id in fixtures).
- Expense
  - id: string
  - description: string
  - amountCents: number (integer cents)
  - paidBy: string (person name)
  - participants: { person: string, weight?: number }[] (default weight 1)
- Transfer
  - from: string
  - to: string
  - amountCents: number
- SettlementResponse
  - balances: Record<string, number> (positive means the person is owed; negative means the person owes)
  - transfers: Transfer[] (deterministic order)

## Endpoints
- ep-expenses-list: GET /api/expenses
  - Request: none
  - Response: Expense[]
  - Status: 200
- ep-settlement: GET /api/settlement?include=a,b,c
  - Request: optional query param `include` as a comma-separated list of person names to include in the computation. If omitted, include all people found in expenses.
  - Response: SettlementResponse
  - Status: 200

## Screens
- sc-expenses (route "/")
  - Elements: expenses table (data-testid="expense-row" per item), per-payer totals (data-testid="payer-total-<name>"), proposed transfers list (data-testid="transfer-row"), transfer amount element (data-testid="transfer-amount"), include/exclude toggle per person (checkbox with data-testid="toggle-<name>")
  - States: loading, loaded, error

## Sessions

### Session 1 - App boots and shows data
Goal: Serve the seeded expenses and render them as a table with a per-payer totals section.

Teaches: Next.js route handler basics, GET endpoint, fetching data for a page, grouping and summing with Array.reduce.

Acceptance criteria:
- c-1-1: GET /api/expenses returns 200 with a JSON array of Expense (every item has amountCents as an integer number).
- c-1-2: sc-expenses renders one row per expense (count expense-row equals the number of expenses in the seed).
- c-1-3: sc-expenses renders a per-payer totals section (data-testid="payer-total-<name>") where each payer’s total equals the sum of amountCents they paid.

Cut points:
- cut-api-expenses-list (app/api/expenses/route.ts)
  - writes_into: body
  - hint: Put every seeded expense into `body` and set `status` to 200.
- cut-ui-fetch-expenses (app/(site)/page.tsx)
  - writes_into: expenses
  - hint: Fetch "/api/expenses", parse the JSON, and write the resulting array into `expenses`.
- cut-ui-totals-by-payer (app/(site)/page.tsx)
  - writes_into: totals
  - hint: Group the loaded expenses by payer and write each payer’s summed amount in cents into `totals`.

### Session 2 - Netting works
Goal: Compute per-person net balances and propose a naive greedy settlement; render the proposed transfers list.

Teaches: Pure functions at a server boundary, greedy matching, deterministic ordering, joining server compute to UI.

Acceptance criteria:
- c-2-1: GET /api/settlement returns 200 with balances where each person’s delta (paid minus owed) matches the seeded fixture in integer cents.
- c-2-2: GET /api/settlement includes a transfers array whose amounts sum to zero and whose totals match balances for each person (greedy proposal for the seed).
- c-2-3: GET /api/settlement returns transfers in a deterministic order (sorted by from, then to, both ascending), enabling exact assertions.
- c-2-4: sc-expenses shows a section title "Proposed transfers" when settlement data has been loaded.

Cut points:
- cut-lib-compute-balances (app/lib/settlement.ts)
  - writes_into: out
  - hint: For the given expenses and participants, compute each person’s net cents (paid minus an equal share by weight) and write the mapping into `out`.
- cut-lib-settle-greedy (app/lib/settlement.ts)
  - writes_into: out
  - hint: Using the balances mapping, greedily match the largest creditor with the largest debtor until all deltas are zero and write the list of transfers into `out`.
- cut-api-settlement (app/api/settlement/route.ts)
  - writes_into: body
  - hint: Compute balances and transfers for the current request and write both into `body` with `status` set to 200; sort `body.transfers` deterministically by from, then to ascending.
- cut-ui-load-settlement (app/(site)/page.tsx)
  - writes_into: settlement
  - hint: Fetch "/api/settlement", parse the JSON, and write the object into `settlement`.

### Session 3 - Minimal transfers and rounding
Goal: Refine the settlement to reduce the number of transfers while preserving totals, keep output deterministic, add an include/exclude toggle and integer-safe formatting.

Teaches: Algorithm refinement, tie-breaking for determinism, integer-safe currency formatting, UI toggle state and query parameters.

Acceptance criteria:
- c-3-1: GET /api/settlement on the seed produces a transfers list whose length matches the refined minimal strategy for the fixture and in a deterministic sequence.
- c-3-2: GET /api/settlement?include=<subset> excludes the omitted person(s): no transfer mentions an excluded name and the transfers still balance to zero.
- c-3-3: sc-expenses include/exclude toggle recomputes the transfers list immediately without a full page reload (toggling a person off removes any transfer involving them).
- c-3-4: sc-expenses renders, for each transfer-row, a transfer amount element (data-testid="transfer-amount") whose text equals the currency string for that row’s integer cents (e.g., $12.34).
- c-3-5: sc-expenses renders one row per transfer (count transfer-row equals the number of transfers from the settlement endpoint).

Cut points:
- cut-lib-refine-settle (app/lib/settlement.ts)
  - writes_into: out
  - hint: Refine the settlement so `out` contains a transfer set with the same totals but fewer payments than the naive greedy result, using tie-breaking that keeps a deterministic person-order.
- cut-lib-format-money (app/lib/format.ts)
  - writes_into: out
  - hint: Format an integer cents value into `out` as a currency string like "$12.34" without using floating-point rounding.
- cut-ui-toggle-include (app/(site)/page.tsx)
  - writes_into: included
  - hint: Maintain the set of included people in `included` and update it when a toggle is clicked, then trigger a reload of the settlement using the include list.
- cut-api-include-filter (app/api/settlement/route.ts)
  - writes_into: included
  - hint: Parse the request’s include query into the set `included` and apply it so only those people participate in balances and transfers.
- cut-ui-render-transfers (app/(site)/page.tsx)
  - writes_into: rows
  - hint: Build the array of renderable rows for the transfers list from `settlement.transfers` and write it into `rows`.
