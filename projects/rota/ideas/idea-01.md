# Pairing Rota Generator

**One line:** Generate fair weekly pairs from a team list with no immediate repeats, odd-person handling, and a persisted history.

## Theme
A lightweight pairing rota for study buddies, code reviews or on-call shadowing. The core is a deterministic pairing algorithm with constraints: no self-pairs, avoid repeating a partner until all other options are exhausted, and handle an odd team member by creating one trio or a bye. State persists only in a JSON file under APP_DIR; the UI is plain React.

## Sessions
1. Boot Next/React/TS and a tiny file-store module. Seed a few names and expose a pure `makePairs(people, history)` that returns pairs and an optional trio. End: a POST /api/pairs computes pairs from seed data and returns JSON.
2. Wire the UI: list people, a Generate button that calls the endpoint and shows the suggested pairs, with an Undo Last action. Append the new round to `history.json` and re-render from file on reload. End: click-to-generate writes to disk and shows the new round.
3. Add fairness and stability: ensure no partner repeats until necessary, rotate who gets the trio/bye, and make tie-breakers stable (e.g., by sorted ids + round index). End: an end-to-end flow that adds a person, generates two rounds, and shows no repeat pairs across them, with history persisted.

## What the student types
- Pairing engine: build round-robin pairs with odd-person handling and a "no recent repeat" constraint.
- Fairness/tie-break logic: choose between multiple valid pairings deterministically; rotate the bye.
- History transitions: append and undo last round atomically in the JSON store.

## What this teaches that the shipped projects do not
Focuses on constrained matching and deterministic tie-breaking. Unlike shift-rota (which schedules shifts) or tip-split/stock-tracker (numeric aggregation), this is pair-matching with a trio edge case and a persisted round history, emphasizing fairness and reproducibility over time.

## Out of scope
Calendars or real dates/times, auth, multi-team accounts, and any external services. No drag/drop; inputs are plain text and numbers.

## Risks
Combinatorics and tie-breaking can overrun if designed expansively. Keep the generator greedy/deterministic with a capped team size in seeds. Ensure seed order does not trivially satisfy the constraints (e.g., avoid pre-paired alphabetical order).