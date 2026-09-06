# Bracket Builder

**One line:** Generate and play through a single‑elimination bracket for 4–16 teams, with deterministic seeding and undo/redo.

## Theme
Model a tree of matches and propagate winners forward. It’s valuable because trees and index‑based addressing appear in many apps, and this keeps the surface small while demanding careful, deterministic updates. All data is local and small; no dates, no network calls beyond app‑local routes.

## Sessions
1. Seed 8–12 team names. Build a bracket data structure (rounds → matches → slots) and render it as nested lists. Allow selecting a winner in a first‑round match and see the next slot fill. End with a bracket that renders and advances within round one.
2. Implement buildBracket(teams) with deterministic seeding (1 vs N, 2 vs N‑1, etc.) and bye placement. Wire advanceWinner(tree, matchId, teamId) to fill downstream slots correctly and clear dependents when a prior result changes. End with full progression across all rounds.
3. Add an undo/redo stack of match results and a final standings list (Champion, Finalist, Semifinalists). Disallow selecting both sides at once and show a short reason if a click would violate invariants. End with a robust, reversible bracket.

## What the student types
- buildBracket: compute rounds and matches for any team count 4–16, placing byes deterministically.
- advanceWinner: propagate a selection forward and invalidate downstream results if upstream changes.
- history reducer: push/pop stacks to support undo/redo and re‑apply to the tree.

## What this teaches that the shipped projects do not
- Tree structures and propagation across dependent nodes, rather than flat list transforms.
- Deterministic seeding and bye logic, plus reversible state changes with an explicit history.

## Out of scope
- Drag layout or SVG rendering; stick to simple nested lists/cards.
- Double‑elimination or round‑robin formats.
- Persistence beyond in‑memory state.

## Risks
- Off‑by‑one and indexing bugs in match addressing; mitigate with small, fixed fixtures (e.g., 4, 5, 8 teams) and clear helper functions.
- Undo/redo can sprawl; keep history to simple stacks of matchId→winner snapshots.