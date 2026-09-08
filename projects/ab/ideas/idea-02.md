# Finite-State Wizard Engine

**One line:** A branching multi-step form powered by a tiny finite-state machine (FSM) with explicit transitions and guards.

## Theme
Many UIs are state machines in disguise. This project makes the FSM explicit: steps, actions, and guards decide the next state. It is worth a session because it isolates transition logic into a pure, testable core and renders the path the user took.

## Sessions
1. Scaffold a 3–5 step wizard UI in React with Next routing (single page), render steps and capture answers; wire a placeholder `nextState` that just advances linearly so the page runs.
2. Implement the FSM: define a typed State union, Action union, a transition table with guard functions, and a pure `step(state, action, answers)` that returns the next state deterministically. Render the current step based on state.
3. Add replay and summary: show the path taken (list of states), allow Back, and allow resetting with a different branch. Serialize the path to JSON for inspection.

## What the student types
- Transition function `step(s, a, ctx)` implementing guarded edges from a small table.
- Guard predicates over collected answers (e.g., income > threshold -> skip step).
- Backtracking logic that pops the path without corrupting current answers.

## What this teaches that the shipped projects do not
Other projects manage UI state but do not build an explicit FSM with a typed transition table and guards. This makes branching logic auditable and reusable, which is a distinct pattern.

## Out of scope
- Real authentication, persistence, or URL-deep-linking individual steps.
- Timers or auto-advance; navigation only through explicit user actions.

## Risks
Over-complicating the guard language. Keep guards to simple boolean predicates on a tiny answer object so the core remains small and testable.
