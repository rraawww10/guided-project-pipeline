# Tournament Standings Resolver

**One line:** Enter match results and get a live standings table computed with deterministic tie-break rules (points → goal difference → head-to-head).

## Theme
A multi-criteria ranking problem with a precise comparator and derived aggregates. Students compute a table from raw results, then resolve ties with ordered rules. Worth a session because it forces careful, testable ordering and edge-case handling.

## Sessions
1. Scaffold + points: seed a tiny league and a few fixtures; implement `computeTable(results)` to tally wins/draws/losses and points; render a standings table that updates as you edit scores.
2. Tie-breaker engine: implement a deterministic `compareTeams(a, b, rules)` that applies goal difference, then goals scored, then head-to-head if still tied; prove stability with fixtures.
3. What‑if editor: allow editing remaining fixtures and show the projected table; add undo/redo as a pure reducer.

## What the student types
- `computeTable(results)`: folds match rows into team aggregates.
- `compareTeams(a, b, rules)`: an ordered comparator implementing tie-break semantics with no ambiguity.
- `projectTable(current, edits)`: applies hypothetical changes immutably for a preview.

## What this teaches that the shipped projects do not
It is a deterministic, ordered comparator over derived data, not a filter UI. It teaches modeling of ranking rules, stable sorting, and handling pathological ties in a way tests can pin.

## Out of scope
- Brackets, schedules, or calendars beyond the seeded fixtures.
- Overtime, penalties, or probabilistic simulations.
- Loading/saving from external sources.

## Risks
Head-to-head sub-queries can explode in complexity. Keep the dataset tiny and the rule set to three ordered criteria so the comparator remains readable and testable within the time budget.
