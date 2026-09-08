# Session 2 - Reducer with guards and escalation

Time: 40 minutes
Students start from: Alert switches to Alex and logs the alert; GET /api/state works
Students end with: reducer enforces guards (ack only by current, timeout escalates, resolve returns to idle); POST /api/state echoes a body

What they learn
- Pure reducer with guards returning { ok, next, error?, added? }
- Escalation logic as a helper (next index or stop at end)
- Writing JSON under APP_DIR via POST /api/state

Before you start
- Open app/lib/fsm.ts (escalateIndex and applyEvent) and app/app/page.tsx (dispatchers)
- Keep app/api/state/route.ts open for POST

The plan
| Minutes | What you do |
|---|---|
| 0-5   | Recap S1. Show applyEvent’s shape and the TODO. Explain ok/next/error and added. |
| 5-12  | Live‑code cut-logic-escalate-index. Demonstrate with Alert → Timeout to Beth. |
| 12-28 | Live‑code cut-logic-reducer-apply: idle→alerting via initialAlert; in alerting handle ack (only by current), timeout (use escalateIndex, block at end), resolve (return to idle). |
| 28-33 | Drive wrong‑actor ack to show the exact error text “only Alex can ack”. Drive timeout at Chen to show “no further escalation”. |
| 33-38 | Live‑code cut-ep-state-post: write body to data/state.json and return it. Test with curl or VS Code REST. |
| 38-40 | Summarise: we now have a guarded reducer and persistence. Preview S3 parser + runner. |

Cut points in this session
### cut-logic-escalate-index - lib/fsm.ts:34
- What students see: // TODO(cut-logic-escalate-index): Compute `nextIndex` as currentIndex + 1 when a later contact exists, otherwise keep the currentIndex unchanged
- What they write: if (currentIndex + 1 < contacts.length) use currentIndex + 1 else keep currentIndex.
- Teach it like this: Only move forward if another contact exists; otherwise stay put.
- Passes when: c-2-2 and c-2-5 go green

### cut-logic-reducer-apply - lib/fsm.ts:44
- What students see: // TODO(cut-logic-reducer-apply): Fill `out` by applying one event with guards: when State.mode is "idle", only "alert" is allowed and must set mode to "alerting", currentIndex to 0, and append a log entry; when mode is "alerting": an "ack" is allowed only when event.actor equals the current contact and must append a log entry without changing currentIndex; a "timeout" moves to the next contact using escalateIndex unless already at the last, in which case set ok false with a message naming "no further escalation" and leave the index unchanged; a "resolve" sets mode to "idle", clears currentIndex to null, and appends a log entry; for any other combination set ok false with a message that names the illegal transition; always carry forward contacts and the existing log into out.next
- What they write: branch on state.mode and event.type; build next from base state and a copied log array; append one LogEntry per successful transition; set exact error strings for illegal transitions.
- Teach it like this: Pure function, no side effects; derive next and one added log entry; guard each transition tightly.
- Passes when: c-2-1, c-2-2, c-2-3, c-2-4, c-2-5 go green (and later powers S3)

### cut-ep-state-post - api/state/route.ts:48
- What students see: // TODO(cut-ep-state-post): Read the request JSON into a typed State object, write that object to data/state.json, copy it into `body` and set `status` to 200
- What they write: const incoming = await req.json() as State; resolve APP_DIR; write JSON (mkdir -p); echo back with 200; on error 500 + message.
- Teach it like this: Round‑trip the posted state; ensure the directory exists before writing.
- Passes when: c-2-6 goes green

Where students get stuck
- “Timeout doesn’t move to Beth” — nextIndex always equals currentIndex — Say: Use contacts.length to gate currentIndex + 1; test both middle and end.
- “Ack by Beth passed” — forgot to compare actor to current contact — Say: Read current from state.contacts[state.currentIndex]. Error text must be exactly “only Alex can ack”.
- “Resolve leaves current visible” — forgot to clear currentIndex — Say: Set mode idle and currentIndex null.
- “All tests red after edits to /api/state” — wrapper route broken — Say: Do not re‑export in app/app/api/state/route.ts; keep the declared GET/POST that forward to the implementation.
- “POST fails with ENOENT” — wrote without creating the data directory — Say: mkdir recursive before write (see writeJSON helper in the file).

Check before moving on
- On /: Alert → select Alex → Ack shows “ack by Alex” in the last log and current still Alex.
- On /: Alert → Timeout shows current Beth; Alert → Timeout → Timeout → Timeout shows “no further escalation” and keeps Chen.
- POST /api/state with a body where mode is "alerting" returns 200 and echoes that mode.
