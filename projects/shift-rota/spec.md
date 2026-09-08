# Escalation Simulator: On‑Call as a State Machine

## Outcome
Build a small on‑call escalation simulator with two ways to drive it: a manual stepper and a script runner. The contact order is fixed (seeded as Alex → Beth → Chen). The app renders the current mode and current contact, keeps a chronological log (earliest first), and exposes simple endpoints to load/save State as JSON under APP_DIR. The core is a pure reducer (state, event) → result with guards; the script runner parses lines like "alert", "ack Beth", "timeout", "resolve" and feeds them through the same reducer.

## Out of scope
- Real timers or background jobs. "timeout" is an explicit event triggered by a button or a script line.
- Notifications or integrations (SMS, email, PagerDuty, etc.).
- Multi‑tenant auth or roles.
- Any use of the real clock or date.

## Data model
- Contact: a string name (seeded: ["Alex", "Beth", "Chen"]).
- Event:
  - "alert"
  - { type: "ack", actor: string }
  - "timeout"
  - "resolve"
- Mode: "idle" | "alerting".
- State: { contacts: string[]; mode: Mode; currentIndex: number | null; log: LogEntry[] }
- LogEntry: { step: number; event: "alert" | "ack" | "timeout" | "resolve"; actor?: string; reason: string }
- Persistence: data/state.json (live, gitignored) with a tracked seed file data/state.seed.json (contacts [Alex, Beth, Chen], mode "idle", currentIndex null, log []). Tests reset the live file between runs.

## Endpoints
- ep-state-get — GET /api/state
  - Request: none
  - Response: 200 with a JSON object of shape State (contacts, mode, currentIndex, log)
- ep-state-save — POST /api/state
  - Request: JSON body of shape State
  - Response: 200 with the same JSON object after writing it to data/state.json

## Screens
- sc-sim — route "/"
  - Elements: a text element data-testid="mode" showing "idle" or "alerting"; a text element data-testid="current" showing the current contact name only when mode is "alerting"; a select data-testid="actor-select" listing the contacts; four buttons with data-testid="btn-alert", "btn-ack", "btn-timeout", "btn-resolve"; a log list rendered in chronological order (earliest first) with rows carrying data-testid starting with "log-row-".
  - States: empty (before load), loaded (idle), loaded (alerting)
- sc-script — route "/script"
  - Elements: a textarea data-testid="script-input"; a button data-testid="btn-run-script"; a text element data-testid="script-error" for the first error message; text elements data-testid="mode" and data-testid="current" mirroring the final State after a run; a text element data-testid="log-count" showing the number of log rows produced; the same log list as sc-sim in chronological order (earliest first).
  - States: ready, running, error, finished

## Sessions

### Session 1 - Setup and manual stepper
Goal: Seed the contact order and show the current contact after an Alert on the manual stepper.

Teaches: React state+effect for loading; using a pure function from UI.

Acceptance criteria:
- c-1-1 — On sc-sim initial load, the page shows data-testid="mode" with text "idle" and no element with data-testid="current". Target: sc-sim. Cuts: (none).
- c-1-2 — On sc-sim, after clicking [data-testid=btn-alert], the page shows data-testid="current" with text "Alex" and data-testid="mode" with text "alerting". Target: sc-sim. Cuts: cut-logic-initial-alert.

Cut points:
- cut-logic-initial-alert — app/lib/fsm.ts — writes_into: next — Hint: Build the next State in `next` by setting mode to "alerting", currentIndex to 0, and appending a log entry {step: previous log length + 1, event: "alert", reason: "alert raised; current " + first contact}; preserve existing contacts and earlier log entries.
- cut-ep-state-get — app/api/state/route.ts — writes_into: body — Hint: Read data/state.json when it exists, otherwise read data/state.seed.json, write the parsed State object into `body` and set `status` to 200.

### Session 2 - Reducer with guards and escalation
Goal: Implement a pure reducer that enforces the guards and updates State and the log; manual stepper drives it.

Teaches: Pure reducer with guards; deriving the next index.

Acceptance criteria:
- c-2-1 — On sc-sim, after clicking Alert and selecting "Alex" in data-testid="actor-select", clicking [data-testid=btn-ack] shows data-testid="mode" as "alerting", data-testid="current" still "Alex", and a new last log row whose text includes "ack by Alex". Target: sc-sim. Cuts: cut-logic-reducer-apply.
- c-2-2 — On sc-sim, after clicking Alert then [data-testid=btn-timeout], the page shows data-testid="current" with text "Beth". Target: sc-sim. Cuts: cut-logic-reducer-apply, cut-logic-escalate-index.
- c-2-3 — On sc-sim, after clicking Alert, selecting "Beth" in data-testid="actor-select" and clicking [data-testid=btn-ack], the page shows an error containing "only Alex can ack" and still shows data-testid="current" as "Alex". Target: sc-sim. Cuts: cut-logic-reducer-apply.
- c-2-4 — On sc-sim, after clicking Alert then [data-testid=btn-resolve], the page shows data-testid="mode" with text "idle" and no element with data-testid="current". Target: sc-sim. Cuts: cut-logic-reducer-apply.
- c-2-5 — On sc-sim, after clicking Alert, then [data-testid=btn-timeout] twice to reach "Chen", clicking [data-testid=btn-timeout] again shows an error message containing "no further escalation" and still shows data-testid="current" as "Chen". Target: sc-sim. Cuts: cut-logic-reducer-apply, cut-logic-escalate-index.
- c-2-6 — POST /api/state with a JSON body where mode is "alerting" returns 200 with a JSON object whose mode equals "alerting". Target: ep-state-save. Cuts: cut-ep-state-post.

Cut points:
- cut-logic-escalate-index — app/lib/fsm.ts — writes_into: nextIndex — Hint: Compute `nextIndex` as currentIndex + 1 when a later contact exists, otherwise keep the currentIndex unchanged.
- cut-logic-reducer-apply — app/lib/fsm.ts — writes_into: out — Hint: Fill `out` by applying one event with guards: when State.mode is "idle", only "alert" is allowed and must set mode to "alerting", currentIndex to 0, and append a log entry; when mode is "alerting": an "ack" is allowed only when event.actor equals the current contact and must append a log entry without changing currentIndex; a "timeout" moves to the next contact using `escalateIndex` unless already at the last, in which case set ok false with a message naming "no further escalation" and leave the index unchanged; a "resolve" sets mode to "idle", clears currentIndex to null, and appends a log entry; for any other combination set ok false with a message that names the illegal transition; always carry forward contacts and the existing log into out.next.
- cut-ep-state-post — app/api/state/route.ts — writes_into: body — Hint: Read the request JSON into a typed State object, write that object to data/state.json, copy it into `body` and set `status` to 200.

### Session 3 - Script parser and runner
Goal: Parse a tiny command language and run it end‑to‑end through the reducer; surface reducer errors in the UI.

Teaches: Line parser over a tiny grammar; driver that stops on first error; surfacing reducer errors; persist JSON under APP_DIR.

Acceptance criteria:
- c-3-1 — On sc-script, entering the lines: "alert\ntimeout\nack Beth\nresolve" then clicking [data-testid=btn-run-script] shows data-testid="mode" as "idle", data-testid="log-count" with text "4", the first log row contains "alert" and the last contains "resolve". Target: sc-script. Cuts: cut-parse-line, cut-logic-reducer-apply, cut-run-script.
- c-3-2 — On sc-script, entering the line: "ack Dana" and clicking [data-testid=btn-run-script] shows data-testid="script-error" containing "unknown actor Dana". Target: sc-script. Cuts: cut-parse-line.
- c-3-3 — On sc-script, entering the single line: "resolve" and clicking [data-testid=btn-run-script] shows data-testid="script-error" containing "illegal transition". Target: sc-script. Cuts: cut-logic-reducer-apply, cut-run-script.
- c-3-4 — On sc-script, entering the lines: "alert\nack Beth" then clicking [data-testid=btn-run-script] shows data-testid="script-error" containing "only Alex can ack". Target: sc-script. Cuts: cut-logic-reducer-apply, cut-run-script.
- c-3-5 — On sc-script, entering the lines: "alert\nack Dana\ntimeout" then clicking [data-testid=btn-run-script] shows data-testid="log-count" with text "1" and data-testid="script-error" containing "unknown actor Dana". Target: sc-script. Cuts: cut-run-script, cut-parse-line.
- c-3-6 — GET /api/state returns 200 with a JSON object whose contacts equal ["Alex", "Beth", "Chen"], mode is "idle", and log is an empty array. Target: ep-state-get. Cuts: cut-ep-state-get.

Cut points:
- cut-parse-line — app/lib/parse.ts — writes_into: event — Hint: From one trimmed input line, set `event` to one of: {type: "alert"}, {type: "timeout"}, {type: "resolve"}, or {type: "ack", actor: <name>} when the line matches exactly "ack " + a non‑empty name; reject any other shape with an error message that includes the bad line; do not validate the actor against contacts here.
- cut-run-script — app/lib/runScript.ts — writes_into: result — Hint: Walk the lines in order; for each, obtain an event from the parser; if the parser yields an error, stop immediately and write that message into `result.error`; otherwise apply the reducer to the current State, append any new log entry the reducer indicates, and continue; after the final successful line, write the final State and full log into `result` with ok true.
