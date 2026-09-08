# Session 1 - Setup and manual stepper

Time: 40 minutes
Students start from: skeleton boots, Sim (/) shows mode idle and no current
Students end with: clicking Alert shows current Alex and mode alerting; GET /api/state returns 200 with the seed

What they learn
- Where the state lives and how the UI reads it (mode/current and the log)
- Using a pure function from UI: dispatching an event into a reducer helper
- Reading JSON from disk under APP_DIR (seed vs live)

Before you start
- Run the app: cd projects/shift-rota/app; npm ci; npm run dev; open http://localhost:3000/
- Have these files open:
  - app/app/page.tsx (Sim UI)
  - app/lib/fsm.ts (initialAlert)
  - app/api/state/route.ts (GET handler)

The plan
| Minutes | What you do |
|---|---|
| 0-5   | Show Sim (/) idle. Point out data-testid=mode and the missing data-testid=current. Walk through the dispatch functions in page.tsx. |
| 5-10  | Open lib/fsm.ts. Explain currentContact and initialAlert. Show where the TODO sits. |
| 10-22 | Live‑code cut-logic-initial-alert: build the next state for the first alert and append a log entry. Trigger it from the Alert button. |
| 22-30 | Verify the log renders earliest-first; read the first row aloud. Show that current is Alex. |
| 30-36 | Live‑code cut-ep-state-get: read live if present else seed, resolved under APP_DIR. Hit /api/state in the browser. |
| 36-40 | Click Alert once more to confirm UI still works. Preview Session 2: a full reducer with guards. |

Cut points in this session
### cut-logic-initial-alert - lib/fsm.ts:11
- What students see: // TODO(cut-logic-initial-alert): Build the next State in `next` by setting mode to "alerting", currentIndex to 0, and appending a log entry {step: previous log length + 1, event: "alert", reason: "alert raised; current " + first contact}; preserve existing contacts and earlier log entries
- What they write: set mode to "alerting", index 0, append one LogEntry with step = old log length + 1 and a reason naming the first contact; do not mutate the old log array.
- Teach it like this: Move to alerting at the first contact and record why in the log; keep everything else the same.
- Passes when: criterion c-1-2 goes green

### cut-ep-state-get - api/state/route.ts:22
- What students see: // TODO(cut-ep-state-get): Read data/state.json when it exists, otherwise read data/state.seed.json, write the parsed State object into `body` and set `status` to 200
- What they write: resolve base = APP_DIR; if live exists, parse it, else parse the seed; set status 200.
- Teach it like this: Prefer the live file; fall back to the tracked seed; resolve against APP_DIR so it works in app/ and skeleton/.
- Passes when: criterion c-3-6 goes green

Where students get stuck
- “Alert does nothing” — edited page.tsx instead of the reducer — Say: The UI already dispatches; fill initialAlert in lib/fsm.ts.
- “current stays empty after Alert” — forgot to set currentIndex to 0 — Say: Mode must be alerting and index 0 to show Alex.
- “TypeError reading contacts[0]” — rebuilt next without copying contacts/log — Say: Start from {...state} and copy the existing log before appending.
- “GET /api/state 404” — touching the app/app/api wrapper or re‑exporting GET/POST — Say: Keep the declared wrapper as in app/app/api/state/route.ts; Next needs declarations, not a bare re‑export.

Check before moving on
- On /, clicking Alert shows data-testid=current with Alex and data-testid=mode with alerting.
- GET http://localhost:3000/api/state returns 200 JSON with contacts ["Alex","Beth","Chen"], mode "idle", log [].
