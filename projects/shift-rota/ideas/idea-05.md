# Escalation Simulator: On‑Call as a State Machine

**One line:** Simulate an on‑call escalation chain with explicit events (alert, ack, timeout, resolve) driven by a tiny script language and a pure reducer.

## Theme
On‑call flows are rotas with state. This project encodes the flow as a finite state machine (FSM) over a small, fixed contact order. It is valuable because it mixes a compact parser with deterministic transitions you can step through and grade without real time.

## Sessions
1. Setup + manual stepper: seed a contact order (e.g., Alex → Beth → Chen). Render a small panel with the current state and buttons to dispatch events (Alert, Ack, Timeout, Resolve). Persist the log to a JSON file. Runs with a visible “current contact” after Alert.
2. Reducer: implement the FSM as a pure function (state, event) → state with guards: Alert only from Idle; Ack only by current contact; Timeout escalates to the next contact unless at end; Resolve returns to Idle. Manual stepping updates UI and log.
3. Script runner: implement a mini parser for lines like “alert”, “ack Beth”, “timeout”, “resolve”. Validate actor names and illegal transitions, stop on error with a message. A textarea runs the script end‑to‑end and shows the final state and log.

## What the student types
- A total, typed reducer for the FSM and its guards.
- A small line parser that tokenizes commands and validates arguments.
- A simulator that feeds parsed events to the reducer and accumulates a log with reasons.

## What this teaches that the shipped projects do not
Nothing else in the set pairs a parser with a state machine. The result is not a sorted list or a financial total but an explainable sequence of transitions, all deterministic and testable.

## Out of scope
- Real timers; “timeout” is an explicit event in tests.
- Notifications or integrations.
- Multi‑tenant auth.

## Risks
Grammar drift can make the parser bigger than planned. Keep commands to 3–4 verbs, fixed order of tokens, and short seeds so every transition is graded twice (happy and illegal).