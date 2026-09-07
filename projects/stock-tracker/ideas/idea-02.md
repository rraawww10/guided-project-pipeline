# Single‑Stock Limit Order Book Simulator

**One line:** Submit, match, and cancel limit orders for one seeded symbol with a deterministic price–time engine and a live order book UI.

## Theme
A small state‑machine project: encode price–time priority, partial fills, and cancels for a single instrument. It’s valuable because it forces clear state transitions and idempotent persistence without clocks or networks.

## Sessions
1. Schema and scaffold: Prisma models for orders and trades; seed a few resting orders. Render a book view (best bid/ask ladders) and a simple order form. It loads from SQLite and shows the initial book.
2. Matching engine v1: on order submit, cross against the opposite side by price–time, create trades, and update remaining quantity. An endpoint runs the match and returns updated book + trades.
3. Partial fills and remainders: support multiple matches per incoming order, leaving the unfilled remainder resting. Display a trade tape on the page.
4. Cancels and replaces: implement order cancel/replace, with valid state transitions and idempotent behavior. The UI can cancel a resting order and the book updates.
5. Replay: load a seeded sequence of orders, advance a deterministic “step” counter stored in the DB, and replay one step at a time to verify engine determinism. No wall‑clock; all steps are data‑driven.

## What the student types
- Core matching loop (price–time priority) with creation of trade records and decrementing quantities.
- State transition logic for order statuses (new, partial, filled, canceled) with transactional updates.
- Book view computation: aggregate by price level and side from the orders table.

## What this teaches that the shipped projects do not
- A real state machine with ordered transitions and persistence, beyond CRUD lists or simple calculations.
- Deterministic replayability and idempotent endpoints, which are not covered by prior list‑oriented demos.

## Out of scope
- Multi‑symbol routing, market orders vs. limit/stop varieties beyond what’s needed, and any live market connectivity.
- Latency, concurrency, or fairness beyond single‑threaded deterministic behavior.

## Risks
- The matching rules can sprawl; constrain scope to one symbol, limit orders only, and price–time priority so it stays within session budgets.