# FixtureMaker: Round-Robin Scheduler

**One line:** Generate a fair round-robin schedule (with byes if needed) from a short list of teams and render it as rounds and pairings.

## Theme
A classic combinatorics problem in a practical wrapper. Given N team names, build a double-checked schedule using the "circle method", handling odd team counts with a bye. Valuable because it teaches algorithmic construction and stable ordering the UI can trust.

## Sessions
1. App boots and shows teams: seed teams.json, GET /api/teams returns the seed, render a simple list and a placeholder first round.
2. Pairings appear: implement generateRoundRobin(teams) using the rotation method; handle odd counts by inserting a BYE; render all rounds in a grid, skipping BYE pairings in the UI.
3. Balancing and export: flip home/away across rounds to balance appearances; ensure no immediate rematch pattern; add a download button that exports the schedule as TSV text (computed, not saved).

## What the student types
- rotatePairings(teams): core circle-method rotation that yields round slots.
- generateRoundRobin(teams): builds rounds with BYE handling and deterministic order.
- balanceHomeAway(rounds): pass that flips home/away to even out appearances.

## What this teaches that the shipped projects do not
- A constructive algorithm with edge cases (odd N) and invariants the tests can pin exactly.
- Deterministic, stable sorting/tie-breaks for predictable UI and test fixtures.
- Joining server-computed data to a grid UI without introducing network complexity.

## Out of scope
- Dates, times, venues, drag-and-drop reordering, or persistence beyond the seed file.

## Risks
Getting the rotation correct and stable for odd team counts. Keep fixtures small (4–8 teams) and make ordering rules explicit so tests don’t pass by coincidence.