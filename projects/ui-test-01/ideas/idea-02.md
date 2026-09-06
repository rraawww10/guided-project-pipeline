# Branching Quiz as a Finite-State Machine

**One line:** A quiz engine driven by an explicit finite-state machine (FSM) where each answer routes to the next node, with scoring and a replayable session log.

## Theme
Representing UI flow as data instead of if/else in components. Students define nodes, edges, and guards; write a tiny interpreter that steps the machine; and prove determinism with fixtures. Worth a session because many apps are implicit state machines—this makes one explicit and testable.

## Sessions
1. Scaffold + runner: define a small `Machine` shape and a pure `step(machine, state, answer)`; render the current question and answers; clicking advances deterministically.
2. Scoring and branching: add per-edge effects (score deltas), terminal nodes, and a summary screen; show the accumulated score and chosen path.
3. Navigation + sharing: implement back/forward and restart in a pure reducer; serialize state into the URL so a completed run is shareable and reload-stable.

## What the student types
- `step(machine, state, action)`: the state transition function, returning next node and effects.
- `scoreReducer(score, effect)`: folds per-edge effects into a total.
- `encodeRun(state) / decodeRun(query)`: stable, minimal URL encoding of the run so it replays.

## What this teaches that the shipped projects do not
Moves beyond CRUD to an explicit state machine model with a small interpreter. It teaches representing UI logic as data, writing pure transitions, and proving flow determinism under test.

## Out of scope
- Randomization, timers, or adaptive difficulty.
- Importing questions from files or external APIs.
- Internationalization and theming.

## Risks
Over-branching can overrun. Keep the graph tiny (e.g., 6–8 nodes) and the transition function pure so each session ends with a runnable demo and stable tests.
