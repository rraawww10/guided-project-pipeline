# Capital Gains Lot Calculator

**One line:** Compute realized and unrealized P/L per symbol by pairing buys and sells under FIFO/LIFO/average‑cost strategies on seeded trades.

## Theme
A focused accounting calculation: given a small ledger of trades and closing prices, pair lots and calculate gains. It’s valuable because it forces careful algorithmic handling of quantities, rounding, and cross‑record state without reaching for external data.

## Sessions
1. Schema and seed: Prisma models for Trades and Positions. Seed a short trade history and show it in a page. An endpoint returns normalized trades from SQLite.
2. FIFO lot pairing: implement a function that walks sells, pairs them to prior buys, and emits realized P/L rows with remaining lot balances. Render a realized P/L table.
3. Alternative strategies: add LIFO and average‑cost modes, selected via UI, using pure functions. The page recomputes deterministically for the seed.
4. Unrealized P/L: with seeded end‑of‑day prices, compute per‑symbol unrealized P/L and a portfolio summary.
5. What‑if: add a small helper that proposes tax‑loss harvesting candidates based on unrealized losses over a threshold. No advice; just a deterministic screen.

## What the student types
- Lot‑pairing algorithm (FIFO/LIFO) producing realized P/L with quantity spills across buys.
- Average‑cost calculator and per‑symbol summary reducers.
- Deterministic application of a pricing table to open positions to compute unrealized P/L.

## What this teaches that the shipped projects do not
- Multi‑row accounting logic with lot pairing and cross‑row state, distinct from prior single‑row toggles or simple splits.
- Strategy‑switchable computations with shared types and tests over the same seeded dataset.

## Out of scope
- Tax rules beyond basic lot selection (no wash‑sale legal detail), brokers, or live prices.
- Multiple currencies; assume a single currency and round to two decimals.

## Risks
- Edge cases in quantity math (partial fills, rounding). Keep seeds small and add explicit tests for fractional spillover to prevent regressions.