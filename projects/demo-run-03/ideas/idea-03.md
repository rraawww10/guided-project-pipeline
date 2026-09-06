# Budget Rollup by Category and Period

**One line:** Compare planned vs actual amounts by category for named periods and persist quick edits, all with Prisma + SQLite.

## Theme
A compact reporting grid that exercises Prisma groupBy-style queries and a small write path. Periods are stored as explicit strings like "2026-01" to avoid real-clock dependence. Seeds and migrations run cleanly; no external services.

## Sessions
1. Setup and category list.
   - Prisma schema: Category(id, name), Entry(id, category_id, period TEXT, kind ENUM('budget','actual'), amount_cents INT).
   - Migration + seed: 6 categories; entries for two periods with varied numbers.
   - A Categories view renders names and shows seeded periods available.
2. Single-period rollup grid.
   - GET /api/rollup?period=2026-01 returns per-category totals: budget, actual, variance (actual - budget).
   - UI grid renders one row per category with those three numbers and a per-row variance cell styled via className.
3. Two-period comparison.
   - GET /api/compare?p1=2026-01&p2=2026-02 returns aligned rows {category, p1_actual, p2_actual, delta}.
   - UI shows a side-by-side view and sorts by descending delta with a stable secondary key (name ASC) so ordering is testable.
4. Quick budget edit with persistence.
   - POST /api/budget/upsert updates or inserts a budget entry for a {category_id, period} tuple; returns the updated rollup.
   - UI allows editing one budget cell and re-renders the rollup after the save.

## What the student types
- A grouped aggregation over entries filtered by period and kind, shaped into a stable JSON view model.
- A two-period alignment query that joins or merges results by category, then applies a deterministic sort with a tie-breaker.
- An idempotent upsert for a composite key (category_id + period) and a post-save re-query.

## What this teaches that the shipped projects do not
- Prisma-powered reporting queries and alignment across two filtered datasets, plus a write that feeds an immediate recompute.
- Stable, testable sorting over computed numbers with explicit tie-breakers and seed data chosen to avoid accidental orderings.

## Out of scope
- Real dates, timezones, and calendars; multi-currency; file import/export.
- Auth and concurrent edit resolution.

## Risks
- Under-specifying the sort can yield flaky tests; seed data must avoid matching any default order. Keep the edit path to a single cell upsert so session 4 stays inside budget.