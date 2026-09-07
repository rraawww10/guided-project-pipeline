# Portfolio Rebalancer

**One line:** A Next.js app that computes drift from target allocations and generates a concrete, rounded trade plan to rebalance a seeded portfolio.

## Theme
A practical calculation project: take a small, seeded portfolio, compare it to target weights, and compute the minimal set of buy/sell orders to reach targets under simple constraints. Worth it because it mixes percentages, rounding, and applying a plan back to persisted state — a realistic finance workflow without live data.

## Sessions
1. Bootstrap the app, Prisma + SQLite schema (assets, holdings, prices, targets), seed data, and a page that lists current positions with target weights. It builds and renders a table from the DB.
2. Compute current weights and drift per symbol (current vs target). Add an endpoint that returns a deterministic allocation report and a UI that highlights over/under-weight rows.
3. Generate a trade plan: given a cash budget and a minimum lot size, calculate integer share quantities to buy/sell per symbol to minimize drift. Show the proposed plan in the UI. It runs and returns a consistent plan for the seed.
4. What‑if scenarios: allow editing target weights and cash budget, persist them in SQLite, and recompute the plan. The page re-renders a new plan from saved inputs.
5. Apply plan and reconcile: when “Apply Plan” is clicked, write simulated trades, update holdings accordingly, and show before/after allocation and residual drift. The flow completes end‑to‑end.

## What the student types
- Weight and drift calculation: normalize by portfolio value, compute percentage drift per symbol.
- Integer trade allocation with rounding: distribute buys/sells across symbols under a cash cap and minimum lot constraint.
- Reconciliation: apply a sequence of trades to positions to produce the post‑rebalance state deterministically.

## What this teaches that the shipped projects do not
- A concrete optimization-ish allocation with rounding and a cash cap (distinct from list filtering or simple toggles in habit‑tracker/recipe‑box).
- Persisting and re‑deriving derived state from a normalized Prisma schema, then reconciling it back into base tables.
- Deterministic “what‑if” recomputation with no real clock and no network.

## Out of scope
- Live market data, brokerage APIs, authentication, and candlestick charts.
- Fractional shares and fee/slippage modeling.

## Risks
- Overpacking the trade allocation step: keep constraints minimal (cash cap + lot size) so the rounding/allocation stays teachable in one session without drifting into full optimization.