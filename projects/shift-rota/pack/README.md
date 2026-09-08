# Escalation Simulator: On‑Call as a State Machine

One page for instructors. Three 40‑minute sessions. Build a tiny on‑call simulator with a manual stepper (/) and a script runner (/script). Core is a pure reducer; persistence is a JSON file under APP_DIR via /api/state.

How to run locally
- cd projects/shift-rota/app
- npm ci
- npm run dev
- Open http://localhost:3000/ (Sim) and http://localhost:3000/script (Script)

Stack and entry points
- Next 16 + React 18 + TypeScript (see app/package.json scripts):
  {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
- Screens: app/app/page.tsx (Sim), app/app/script/page.tsx (Script)
- Core logic: app/lib/fsm.ts (initialAlert, escalateIndex, applyEvent)
- Parser/runner: app/lib/parse.ts, app/lib/runScript.ts
- API implementation: app/api/state/route.ts
- API route registration (required by Next): app/app/api/state/route.ts (declares GET/POST and forwards)

Data and persistence
- Live file: app/data/state.json (gitignored)
- Seed file: app/data/state.seed.json (tracked)
- Tests reset the live file between runs. Do not read the real clock or date.

What the UI renders
- Sim (/) shows data-testid="mode"; when alerting, data-testid="current"; actor select data-testid="actor-select"; buttons data-testid btn-alert/btn-ack/btn-timeout/btn-resolve; a chronological log list (earliest first) with rows data-testid^=log-row-.
- Script (/script) shows a textarea data-testid="script-input", a run button data-testid="btn-run-script", error text data-testid="script-error", mode/current mirrors the final state after a run, data-testid="log-count" shows number of log rows.

Cut ownership per session (from spec.json)
- S1: cut-logic-initial-alert (lib/fsm.ts), cut-ep-state-get (api/state/route.ts)
- S2: cut-logic-escalate-index, cut-logic-reducer-apply (lib/fsm.ts), cut-ep-state-post (api/state/route.ts)
- S3: cut-parse-line (lib/parse.ts), cut-run-script (lib/runScript.ts)

Sanity check before class
- GET /api/state returns the seed (contacts Alex→Beth→Chen, mode idle, empty log)
- From /, clicking Alert shows current Alex and mode alerting
- From /script, the demo script:
  alert\ntimeout\nack Beth\nresolve
  ends idle and shows log-count 4

Notes that matter while teaching
- Next only registers handlers declared under app/app/.../route.ts. The project declares GET/POST there and forwards to app/api/state/route.ts so the Cutter can see the markers. Keep that wrapper.
- File I/O resolves under APP_DIR. See app/api/state/route.ts helper appDir().
