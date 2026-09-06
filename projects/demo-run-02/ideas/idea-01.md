# FairShare: Expense Settlement Calculator

**One line:** A small Next.js app that turns a handful of shared expenses into balanced “who pays whom” transfers with minimal transactions.

## Theme
A focused, offline calculation project. Given a few expenses and who participated (with optional weights), compute each person’s net and propose a minimal set of transfers to settle up. Worth it because it blends solid TypeScript modeling with a concrete algorithm students can reason about and test.

## Sessions
1. App boots and shows data: scaffold Next/React/TS, seed a tiny expenses.json, add GET /api/expenses that returns the seed, and render a simple table of expenses and a per-person total column.
2. Netting works: implement a pure function that computes per-person net balances (paid minus owed) and show a naive settlement (greedy match largest creditor to largest debtor). Render a “proposed transfers” list.
3. Minimal transfers and rounding: refine to reduce the number of transfers while preserving totals, use integer cents to avoid float drift, add a simple UI toggle to include/exclude a person and immediately recompute.

## What the student types
- computeBalances(expenses, participants): map of person -> integer cents delta.
- settleDebts(balances): deterministic greedy/heap variant that proposes transfers summing to zero with as few payments as practical.
- formatMoney(cents): integer-safe currency formatting and rounding rules.

## What this teaches that the shipped projects do not
- A concrete optimization-style algorithm (debt netting with minimal transfers) rather than another list-with-filter.
- Modeling and testing pure functions at the server boundary (API returns computed shape, UI renders it), with integer-safe arithmetic.
- Deterministic ordering and tie-breaking in algorithms so tests can assert exact sequences, not just totals.

## Out of scope
- Real currencies/locales, multi-currency, persistence beyond the seed data, or authentication.
- Importing from external services or using timers/real dates.

## Risks
Keeping the "minimal" transfers step small enough for the time budget. Mitigate by scoping to a deterministic greedy approach and integer math so fixtures are stable and offline.