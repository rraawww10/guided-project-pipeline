# Rule-Based Budget Allocator

**One line:** Categorize a tiny set of seeded transactions with a priority rule engine and show per-category totals and deltas.

## Theme
Turn a flat table into information by teaching a simple, deterministic rules engine: each transaction is classified by text/amount rules in priority order, and the UI shows grouped totals with a small “what-if” tweak. It’s a contained calculation with visible payoff and no dates or external dependencies.

## Sessions
1. Setup and listing: seed `app/data/transactions.seed.json` (10–15 rows). Build an API that returns transactions and a page that renders an ungrouped table. End: a table loads from the local API and renders every row.
2. Allocation engine: implement ordered rules (e.g., memo contains "uber" -> Transport; amount < 0 -> Expense; merchant == "ACME" -> Supplies). Apply first-match wins; produce `{category, amount}` outputs per row. Add a grouped summary by category. End: summary totals match expectations and every row shows its chosen rule.
3. What-if and controls: add a per-category budget input (in-memory) and compute delta/percent to budget. Add sort-by-delta and a toggle to view only over-budget categories. End: interactive summary recalculates without touching the server beyond the local API.

## What the student types
- `applyRules(tx: Tx, rules: Rule[]): Category` – first-match classification with clear precedence.
- `summarizeByCategory(rows: ClassifiedTx[]): Summary[]` – grouping and total math with stable sort.
- `computeDelta(summary: Summary, budgets: Record<Category, number>): WithDelta[]` – derive over/under budget metrics.

## What this teaches that the shipped projects do not
- A deterministic, priority-ordered rules engine and transparent grouping math; different from tip-split’s one-off numeric split and recipe-box’s filter/search list.
- Traceability: surfacing which rule fired for a row and why, a pattern not emphasized in existing demos.

## Out of scope
- Real money, dates, or time windows; recurring transactions.
- Persisting edited budgets to disk; multiple users; auth.
- CSV import/export.

## Risks
- Keeping the rules readable and testable in session 2; constrain to text contains/equals and numeric comparisons to stay on time.
