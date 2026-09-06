# Shortlist Scorer

**One line:** Rank a small set of candidates by weighted rules with transparent reasons.

## Theme
Turn a plain list into a decision aid: compute a score per candidate from a few attributes, sort stably, and show exactly why each score was earned. It is worth a session because multi-criteria ranking and deterministic tie-breaking come up everywhere, and they exercise both server endpoints and client state in a way a simple filter does not. Everything runs offline with a tiny hand-seeded dataset.

## Sessions
1. Boot the Next+React+TS app with a seed file of 8–12 candidates and attributes (e.g., years, tags). Expose GET /api/candidates to return the data and render a simple list on "/". End with a working list and a toggle panel that turns factors on/off in local state (no scoring yet).
2. Implement a pure scoreApplicant(app, weights) that yields { score, reasons[] }. Add GET /api/rank?active=... that maps every candidate through the scorer and returns a sorted array with scores and reasons. The UI calls it on toggle and renders ranked cards with their score and a reasons summary. End with a live, ranked list.
3. Add deterministic tie-breakers (e.g., exact-match tag bonus first, then years, then name ASC) and a threshold filter that hides items below a cut-off. Make sort stable and predictable, and surface a “why this order” detail per card. End with a list whose order is explainable and repeatable for the same inputs.

## What the student types
- scoreApplicant: combine weighted signals (exact tag match, numeric normalization, bonus rules) into one number plus human-readable reasons.
- stableMultiKeySort: a comparator that orders by score DESC with explicit, documented tie-breakers.
- serializeActiveWeights: turn UI toggles into a query shape the API trusts and validate on the server.

## What this teaches that the shipped projects do not
- Stable multi-key sorting with explicit, testable tie-breakers rather than a single-key sort or a plain filter.
- “Explainability” strings that line up with the math that produced the score, not just showing raw fields.
- Deterministic outputs from pure functions: same inputs, same ranking every run.

## Out of scope
- CSV import/export, external data sources, or large datasets.
- Live weight sliders with persistence; weights remain simple toggles or small numeric inputs in memory.
- Any real-time or date-based criteria.

## Risks
- Overscoping the scoring rules. Keep signals few and fixed so session 2 stays within time.
- Getting tie-breakers wrong can make results feel random; mitigate with a documented comparator and small seed fixtures.