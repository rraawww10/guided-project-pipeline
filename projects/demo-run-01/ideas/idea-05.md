# Tiny Search with Ranking

**One line:** A client‑side search that ranks items by weighted signals (prefix, whole‑word, tag boost) and highlights matches.

## Theme
Move past “filter includes(query)” to a small scoring function that combines multiple signals and orders results deterministically. It’s worth it because ranking is common, libraries are often overkill, and writing one makes trade‑offs explicit and testable. All data is seeded and local.

## Sessions
1. Seed 20–30 items with { title, description, tags[] }. Render the full list and a basic text input that filters by substring on the client. End with a working list and a dumb filter.
2. Implement tokenizeQuery to split on spaces and extract tag:foo tokens. Write scoreItem(query, item) with weights: exact title startsWith gets most points, whole‑word match gets some, tag match gets a boost. Sort by score DESC, then title ASC for ties. Highlight matched segments. End with ranked, highlighted results.
3. Support multi‑term AND queries and an optional minimum score threshold. Add a simple explanation view per result that lists which signals fired and their points. End with predictable, explainable ranking.

## What the student types
- tokenizeQuery: parse free text into { terms[], tags[] } with simple rules.
- scoreItem: combine multiple weighted signals into one number and return firedSignals for explainability.
- highlightSegments: map match spans onto text to render <mark> elements deterministically.

## What this teaches that the shipped projects do not
- Scored ranking with multiple signals and explicit tie‑breaking, not just filtering.
- A tiny, purpose‑built query parser (tag:foo) and an explanation layer for why an item ranks where it does.

## Out of scope
- Fuzzy matching, stemming, or external search libraries.
- Large datasets or debounced network calls.
- Any date/time logic or real‑clock dependency.

## Risks
- Over‑tuning weights; fix weights in code and document them so tests can assert exact orders.
- Highlighting edge cases (overlaps, repeated terms); keep rules simple and deterministic.