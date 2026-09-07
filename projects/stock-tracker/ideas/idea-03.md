# Candle Maker & Pattern Highlighter

**One line:** Aggregate seeded trade ticks into fixed‑interval candles and detect simple patterns (doji, engulfing), with a UI to explore and highlight them.

## Theme
An aggregation and rules project: group raw events into windows, compute OHLC summaries, and tag patterns. It’s valuable because it teaches windowed computation and deterministic analysis with small, seeded data.

## Sessions
1. Schema and seed: Prisma models for Ticks and Candles. Seed a short run of minute ticks. Render a simple candles table (time, open, high, low, close, volume) from SQLite.
2. Aggregation: implement a function to roll N minute ticks into 5‑minute candles with correct open/high/low/close and summed volume. Persist candles via an endpoint and display them.
3. Pattern detection: compute boolean markers for at least two patterns (e.g., doji by body/range ratio, bullish/bearish engulfing by consecutive candles) and store flags on each candle.
4. UI exploration: a page that can filter by pattern and highlight matches. Keep rendering simple (CSS bars or text markers) to avoid external chart libs.
5. Simple backtest: count how often a chosen pattern appears and show the following candle’s direction as a rough “win rate” table. All offline and reproducible.

## What the student types
- Window aggregation from ticks to candles with correct boundary handling and gap marking.
- Pattern rules: doji ratio, engulfing comparisons across consecutive windows.
- A tiny backtest reducer over persisted candles to compute counts and next‑bar outcomes.

## What this teaches that the shipped projects do not
- Windowed grouping and cross‑row rules over derived tables (distinct from prior item lists and single‑row toggles).
- Designing and persisting derived artifacts (Candles) alongside base events (Ticks) with Prisma.

## Out of scope
- Live data, real charts, technical indicator libraries, or multi‑symbol dashboards.
- Timezone/locale dependence: all timestamps come from seeded rows; no calls to the real clock.

## Risks
- Charting can become a rabbit hole; keep visuals textual/minimal and focus on correct aggregation and rules.