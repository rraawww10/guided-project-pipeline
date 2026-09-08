# Session 3 - Script parser and runner

Time: 40 minutes
Students start from: guarded reducer + GET/POST work; Sim behaves for Alert/Ack/Timeout/Resolve
Students end with: a parser for lines and a runner that stops on first error; the demo script runs to idle with 4 log rows; unknown actors and illegal transitions surface as errors

What they learn
- Tiny line parser over a fixed grammar
- Driver that stops on the first error and surfaces messages
- Feeding the same reducer from a scripted source

Before you start
- Open app/lib/parse.ts and app/lib/runScript.ts
- Keep app/app/script/page.tsx open to show the UI hooks (script-input, btn-run-script, script-error, mode/current, log-count)

The plan
| Minutes | What you do |
|---|---|
| 0-6   | Show /script. Walk through the UI’s run button and how it calls runScript(script, initial). Explain initial comes from GET /api/state. |
| 6-18  | Live‑code cut-parse-line: accept alert/timeout/resolve exactly, and ack <name>; reject others with an error including the bad line. No contact validation here. |
| 18-32 | Live‑code cut-run-script: split lines, parse each, stop on parse error, validate ack actor against contacts, apply the reducer, append added log entries, stop on reducer error; after success, return ok true with final state and log. |
| 32-36 | Drive the happy script: alert → timeout → ack Beth → resolve. Show mode idle, log-count 4, first row mentions alert, last mentions resolve. |
| 36-40 | Drive two errors: “ack Dana” (unknown actor) and just “resolve” from idle (illegal transition). Point to where each error comes from (runner vs reducer). |

Cut points in this session
### cut-parse-line - lib/parse.ts:12
- What students see: // TODO(cut-parse-line): From one trimmed input line, set `event` to one of: {type: "alert"}, {type: "timeout"}, {type: "resolve"}, or {type: "ack", actor: <name>} when the line matches exactly "ack " + a non-empty name; reject any other shape with an error message that includes the bad line; do not validate the actor against contacts here
- What they write: trim, match the four forms, build one Event; otherwise return {ok:false, error:`bad line: ${line}`}; do not look up contacts here.
- Teach it like this: Parser checks shape only; runner checks names.
- Passes when: c-3-2 goes green (and feeds c-3-1 and c-3-5)

### cut-run-script - lib/runScript.ts:14
- What students see: // TODO(cut-run-script): Walk the lines in order; for each, obtain an event from the parser; if the parser yields an error, stop immediately and write that message into `result.error`; otherwise apply the reducer to the current State, append any new log entry the reducer indicates, and continue; after the final successful line, write the final State and full log into `result` with ok true
- What they write: for each line: parse; if parse fails, return {ok:false, error}; if ack, ensure actor is in state.contacts and error if not; applyEvent; on failure return reducer’s error; on success, append added to log and continue; return {ok:true, state, log} at the end.
- Teach it like this: One place owns actor validation (the runner) and one owns transition guards (the reducer). Stop on the first error.
- Passes when: c-3-1, c-3-3, c-3-4, c-3-5 go green

Where students get stuck
- “Parser says unknown actor Dana” — validated in the parser — Say: Keep parser to shapes; the runner validates actor names against state.contacts (see A2 in ambiguity.md).
- “Script keeps running after an error” — forgot to return immediately — Say: Stop on first error and surface its message in script-error.
- “Log-count is wrong” — double‑append vs trust state.log — Say: Prefer the reducer’s added when provided; otherwise mirror state.log.
- “Illegal transition message differs” — changed error text — Say: Keep messages literal; tests assert on exact text (e.g., "illegal transition").

Check before moving on
- On /script, running:
  alert\ntimeout\nack Beth\nresolve
  shows mode idle, log-count 4, first log row includes alert and last includes resolve.
- Running just: resolve shows script-error containing "illegal transition".
- Running: ack Dana shows script-error containing "unknown actor Dana" and log-count 0/1 depending on prior alert.
