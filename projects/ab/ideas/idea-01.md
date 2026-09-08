# League Standings Calculator

**One line:** A mini league table that computes standings and tie-breaks from a seeded set of match results, with a live “what-if” editor.

## Theme
Turn a small list of match results into a sorted standings table with realistic tie-break rules. It is worth a session because it mixes aggregation, multi-key sorting and a simple UI that makes the math visible and testable without any external data or time.

## Sessions
1. Scaffold Next + React + TypeScript app with a seeded JSON of 6 teams and ~10 results; render a basic table fed by an API endpoint returning precomputed standings placeholders.
2. Implement the core: compute team aggregates from results (played, W/D/L, points, goals for/against, goal difference) and a deterministic multi-key comparator (points DESC, GD DESC, GF DESC, name ASC). Endpoint returns computed standings; UI renders sorted table.
3. Add a “what-if” sandbox: an in-memory form to edit or add one pending fixture and recompute standings locally without touching the seed. Show the delta (movement up/down) alongside the rank.

## What the student types
- Aggregator over matches -> per-team stats map (reduce by team, derive points and GD).
- Stable multi-key comparator for tie-breaks with explicit order and fallbacks.
- Pure function to apply a hypothetical result onto the aggregates without mutating the seed.

## What this teaches that the shipped projects do not
Stocks and tips projects do arithmetic, but none combine a reduce-to-stats pass with a multi-key, domain-like tie-break sort and a local “what-if” projection. It contrasts pure recomputation vs. mutation clearly.

## Out of scope
- Real leagues, live scores, or external APIs.
- Persistence beyond the small seed file.
- Head-to-head or circular tie-break rules (kept for a future extension).

## Risks
Cramming too many tie-breakers into one step. Keep it to clearly stated keys and ensure seed data exercises at least two ties so the comparator is meaningfully graded.
