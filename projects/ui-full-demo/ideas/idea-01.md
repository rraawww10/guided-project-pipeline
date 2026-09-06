# League Standings: Deterministic Tie‑Breaker Table

**One line:** A single-screen league standings table computed from a handful of seeded match results, with deterministic multi-key tie-breakers and an expandable per-team rationale.

## Theme
Turn a small set of match results into a ranked table with clear, reproducible rules. This is worth a session because ranking is where simple totals meet careful ordering: points first, then goal difference, then goals for, then a stable alphabetical tiebreak. Students practice folding raw events into per-team stats and expressing a comparator that cannot “wiggle”.

## Sessions
1. Setup + totals: seed 10–12 matches in JSON, fold them into per-team stats (played, W/D/L, GF/GA, points) and render a basic table at "/" from local data. It runs with totals correct but unsorted.
2. Ranking and ties: implement a pure rankTeams(stats) that sorts by points desc, goal difference desc, goals for desc, then team name asc, and computes rank numbers with shared ranks for ties. Add GET /api/standings that returns the ranked rows; the page reads and renders it.
3. Rationale on demand: clicking a team opens a panel listing the matches that contributed its points with per-match deltas, all computed locally from the same seed. Edits to one score in-memory recompute the table deterministically.

## What the student types
- statsFromMatches(matches): a reducer that accumulates per-team GF/GA, W/D/L and points.
- rankTeams(stats): a stable multi-key comparator plus a pass that assigns rank numbers to tie blocks.
- buildTeamRationale(team, matches): select and explain contributions per match (e.g. “win vs B: +3 pts, GD +2”).

## What this teaches that the shipped projects do not
- Unlike the Ledger project’s per-key totals and the Budget Allocator’s rule priority, this adds a deterministic multi-key ranking with explicit tie handling and rank-number assignment.
- It differs from Bowling’s lookahead and Elevator’s dispatch by being a pure reduce+sort with a stable comparator contract, not a time-stepper.
- No shipped grid app (Minesweeper, Nonogram) ranks entities or teaches stable tie blocks; this does.

## Out of scope
- Schedules, live fixtures, pagination, head-to-head rules, strength-of-schedule, or importing data. One screen, one endpoint, seeded JSON only.

## Risks
- Over-scoping the rationale UI can eat minutes. Keep it to a simple expandable list derived from the same seed, and make the comparator strictly multi-key so tests don’t depend on engine sort stability.