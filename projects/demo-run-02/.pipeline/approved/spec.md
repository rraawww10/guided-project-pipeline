# FairShare: Expense Settlement Calculator

## Outcome
A small Next.js app that reads a seeded list of shared expenses and, on the home page, shows:
- a table of expenses;
- a per-person net balance (paid minus owed) computed in integer cents; and
- a proposed set of transfers ("who pays whom") produced by a deterministic greedy algorithm, with a toggle to switch to a refined ordering and a checkbox per person to include/exclude them from the calculation.

Every session ends with something that runs:
1) the API returns the seed and the page lists expenses and per-person totals-paid;
2) balances and a naive settlement render on the page and via an API;
3) formatting is integer-safe, transfers sort deterministically, and toggling people recomputes.

## Out of scope
- Real currencies/locales, multi-currency, persistence beyond the seed file, or authentication.
- Importing from external services or using timers/real dates.

## Data model
- PersonId: string (we use first names in the seed).
- AmountCents: integer number of cents.
- Expense: { id: string; description: string; amountCents: number; paidBy: PersonId; participants: { person: PersonId; weight?: number }[] }.
  - weights default to 1. Seed uses equal weights so shares divide evenly.
- BalanceMap: Record<PersonId, AmountCents> where positive means others owe them.
- Transfer: { from: PersonId; to: PersonId; amountCents: number }.

Seed (data/expenses.seed.json):
- People: Alice, Bob, Cara, Dan, Eve
- Expenses:
  - e1: "Lunch", 5200 cents, paidBy: Alice, participants: [Alice, Bob, Cara, Dan]
  - e2: "Groceries", 3000 cents, paidBy: Bob, participants: [Bob, Cara]
  - e3: "Taxi", 1500 cents, paidBy: Dan, participants: [Alice, Dan, Eve]
  - e4: "Tickets", 4000 cents, paidBy: Cara, participants: [Alice, Bob, Cara, Dan, Eve]

Derived (from the seed):
- Final net balances (cents): Alice +2600, Bob -600, Cara +400, Dan -1100, Eve -1300.
- A naive greedy settlement (largest creditor matched to largest debtor):
  - Eve -> Alice 1300
  - Dan -> Alice 1100
  - Bob -> Alice 200
  - Bob -> Cara 400

## Endpoints
- ep-expenses-list: GET /api/expenses → Expense[] (200)
- ep-naive-settlement: GET /api/settlement/naive → Transfer[] (200)

## Screens
- sc-home: route "/"
  - elements:
    - Expenses table (one row per expense) [data-testid="expense-row"]
    - Balances list (one row per person) [data-testid="balance-row"]
    - Proposed transfers list (one row per transfer) [data-testid="transfer-row"]
    - Per-person include/exclude checkboxes [data-testid="include-<name>"]
    - Minimal transfers toggle [data-testid="toggle-minimal"]
    - A formatting probe element [data-testid="money-sample"] showing formatMoney applied to -615
  - states: loading, loaded, error

## Sessions

### Session 1 - App boots and shows data
Goal: Boot the app, serve the seeded expenses via an API, render an expenses table, and show per-person totals-paid.

Teaches: fetch in Next.js app router, useState for loaded data, mapping arrays to summary totals in integer cents.

Acceptance criteria:
- c-1-1: GET /api/expenses returns 200 with a JSON array of 4 Expense
  - target: ep-expenses-list
  - cuts: [cut-api-expenses-list]
- c-1-2: sc-home renders 4 elements with data-testid="expense-row" after load
  - target: sc-home
  - cuts: [cut-ui-load-expenses]
- c-1-3: sc-home shows a per-person totals-paid summary with 5 rows and exact amounts: Alice $52.00, Bob $30.00, Cara $40.00, Dan $15.00, Eve $0.00
  - target: sc-home
  - cuts: [cut-ui-load-expenses, cut-ui-compute-paid-totals]

Cut points:
- cut-api-expenses-list (app/api/expenses/route.ts, writes_into: body)
  - Hint: Put every expense from the seed store into `body` and set `status` to 200.
- cut-ui-load-expenses (app/page.tsx, writes_into: items)
  - Hint: Fetch "/api/expenses" and write the parsed JSON array into `items`; keep the existing error and loading state handling unchanged.
- cut-ui-compute-paid-totals (app/page.tsx, writes_into: totals)
  - Hint: Accumulate the sum of `amountCents` each payer contributed into `totals` keyed by person id using integer cents already present in `items`.

---

### Session 2 - Netting works and a naive settlement renders
Goal: Compute per-person net balances (paid minus owed) and show a naive greedy settlement on the page; expose the same transfers via an API.

Teaches: pure functions over arrays and maps, integer-safe netting, deterministic greedy matching, wiring computed data into UI and an endpoint.

Acceptance criteria:
- c-2-1: sc-home renders 5 elements with data-testid="balance-row" in name-ASC order, with exact texts: Alice +$26.00; Bob -$6.00; Cara +$4.00; Dan -$11.00; Eve -$13.00
  - target: sc-home
  - cuts: [cut-lib-compute-balances, cut-ui-set-balances]
- c-2-2: sc-home renders a Proposed transfers list with 4 elements with data-testid="transfer-row" and the first item reads "Eve pays Alice $13.00"
  - target: sc-home
  - cuts: [cut-lib-compute-balances, cut-lib-settle-naive, cut-ui-set-transfers]
- c-2-3: sc-home shows a total transfers amount element [data-testid="transfers-total"] equal to "$30.00"
  - target: sc-home
  - cuts: [cut-lib-settle-naive, cut-ui-set-transfers]
- c-2-4: GET /api/settlement/naive returns 200 with a JSON array of 4 Transfer; the first element equals {"from":"Eve","to":"Alice","amountCents":1300}
  - target: ep-naive-settlement
  - cuts: [cut-lib-compute-balances, cut-lib-settle-naive, cut-api-naive-settlement]

Cut points:
- cut-lib-compute-balances (lib/settlement.ts, writes_into: out)
  - Hint: Compute each person's net in cents into `out` by adding amounts they paid and subtracting their share of each expense; divide an expense by the sum of participant weights (default 1) and subtract each share from that participant.
- cut-lib-settle-naive (lib/settlement.ts, writes_into: out)
  - Hint: From a `balances` map, build `out` as a list of transfers by repeatedly matching the largest positive balance to the largest (most negative) balance and moving the smaller absolute amount; continue until no balances remain nonzero.
- cut-ui-set-balances (app/page.tsx, writes_into: balances)
  - Hint: Derive `balances` from the loaded `items` (and the current included people) using the provided netting function.
- cut-ui-set-transfers (app/page.tsx, writes_into: transfers)
  - Hint: Derive `transfers` from the current `balances` using the naive settlement function and make it stable across renders.
- cut-api-naive-settlement (app/api/settlement/naive/route.ts, writes_into: body)
  - Hint: Populate `body` with the current naive settlement computed from the seeded expenses and set `status` to 200.

---

### Session 3 - Minimal-mode, integer formatting, and include/exclude
Goal: Add a minimal-mode toggle that switches to a refined, deterministically ordered settlement for display; format all money with integer-safe cents; and add include/exclude per person that immediately recomputes balances and transfers.

Teaches: stable sort and tie-breaking, integer-safe currency formatting, local UI toggles that drive recomputation.

Acceptance criteria:
- c-3-1: sc-home renders [data-testid="money-sample"] equal to "-$6.15"
  - target: sc-home
  - cuts: [cut-lib-format-money]
- c-3-2: With [data-testid="toggle-minimal"] set ON, sc-home renders the transfers in amount-descending order then payer then payee; the sequence reads exactly: "Eve pays Alice $13.00", "Dan pays Alice $11.00", "Bob pays Cara $4.00", "Bob pays Alice $2.00"
  - target: sc-home
  - cuts: [cut-lib-settle-minimal, cut-ui-use-minimal]
- c-3-3: Unchecking [data-testid="include-Eve"] removes Eve from balances and no [data-testid="transfer-row"] contains "Eve"
  - target: sc-home
  - cuts: [cut-ui-toggle-include]
- c-3-4: With [data-testid="toggle-minimal"] set ON, sc-home renders 4 elements with data-testid="transfer-row"
  - target: sc-home
  - cuts: [cut-lib-settle-minimal, cut-ui-use-minimal]
- c-3-5: With [data-testid="toggle-minimal"] set OFF, sc-home renders the last [data-testid="transfer-row"] item as "Bob pays Cara $4.00"
  - target: sc-home
  - cuts: [cut-ui-use-minimal]

Cut points:
- cut-lib-format-money (lib/money.ts, writes_into: out)
  - Hint: Format integer cents into `out` as "$X.YY" with a leading minus for negatives (e.g. -615 → "-$6.15"); do not use floats.
- cut-lib-settle-minimal (lib/settlement.ts, writes_into: out)
  - Hint: Produce `out` as a transfer list equivalent in totals to the naive result but ordered by amount descending, then payer asc, then payee asc; do not increase the number of transfers.
- cut-ui-toggle-include (app/page.tsx, writes_into: included)
  - Hint: Toggle the given person's id in the `included` Set while preserving every other selection; the next recompute must use exactly the currently included people.
- cut-ui-use-minimal (app/page.tsx, writes_into: transfers)
  - Hint: When minimal mode is ON, write the refined transfer sequence into `transfers` using the minimal function; when it is OFF, preserve the naive sequence already derived.
