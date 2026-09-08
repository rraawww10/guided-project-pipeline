# Troubleshooting

Real errors students hit, their causes, and what to say.

API and routing
- Symptom: Every UI test fails; /api/state 404 in the browser devtools
  - Cause: Next did not register the API route because the file only re‑exports handlers. A declaration is required under app/app/api/state/route.ts.
  - Say: Keep a declared wrapper and forward to the implementation. The project ships this wrapper:
    
    // Real route handlers, defined here because Next only registers handlers that
    // are DECLARED in a file under the app directory. The previous version was
    // `export { GET, POST } from "../../../api/state/route"`, and a re-export is
    // not picked up: `next build` listed only /, /_not-found and /script, so
    // /api/state 404'd. That single 404 failed all 14 criteria - the two API ones
    // directly, and every UI one because page.tsx throws "failed to load" on mount
    // when the fetch is not ok, so no testid ever renders.
    //
    // The implementation stays in app/api/state/route.ts because spec.json places
    // cut-ep-state-get and cut-ep-state-post in that file; moving it would put the
    // cut markers somewhere the cutter does not look. This wrapper only forwards.
    import { GET as getState, POST as postState } from "../../../api/state/route";
    
    export const dynamic = "force-dynamic";
    
    export async function GET(): Promise<Response> {
      return getState();
    }
    
    export async function POST(req: Request): Promise<Response> {
      return postState(req);
    }

- Symptom: GET /api/state works locally but fails from the skeleton or another machine
  - Cause: Paths resolved against CWD instead of APP_DIR.
  - Say: Resolve both files against APP_DIR. The helpers in app/api/state/route.ts show the pattern:
    
    function appDir(): string {
      return process.env.APP_DIR || process.cwd();
    }

    await fs.mkdir(path.dirname(p), { recursive: true }) // before write

Reducer and state
- Symptom: Clicking Alert does nothing
  - Cause: initialAlert not implemented; editing the UI instead of the reducer.
  - Say: Implement cut-logic-initial-alert in lib/fsm.ts; the UI already dispatches.

- Symptom: current remains empty after Alert
  - Cause: currentIndex not set to 0 or mode not set to alerting.
  - Say: Set both in the next state and append a log entry.

- Symptom: Timeout from Alex doesn’t move to Beth
  - Cause: escalateIndex never increments or off‑by‑one.
  - Say: Increment only if currentIndex + 1 < contacts.length; otherwise keep index.

- Symptom: Ack by Beth passes or error text mismatches
  - Cause: Not comparing event.actor to current contact; error message differs.
  - Say: Compare to state.contacts[state.currentIndex]; emit exactly "only Alex can ack" when Alex is current.

Parser and runner
- Symptom: "ack Dana" shows no error, or shows from the wrong place
  - Cause: Validating actor in the parser or forgetting to validate in the runner.
  - Say: The parser checks shapes; the runner validates names against state.contacts and stops with "unknown actor Dana".

- Symptom: Script keeps running after a bad line
  - Cause: Not returning on the first parse/reducer error.
  - Say: Stop immediately and surface the message in data-testid=script-error.

- Symptom: log-count is off by one or two
  - Cause: Double‑appending added entries or ignoring reducer.added.
  - Say: Prefer the reducer’s added; if absent, mirror state.log.

I/O
- Symptom: POST /api/state 500 ENOENT: no such file or directory
  - Cause: Writing without creating the data directory.
  - Say: mkdir -p before write (see writeJSON helper). Tests assume directory creation.

Smoke checks (fast)
- GET http://localhost:3000/api/state → 200 with seed: contacts Alex, Beth, Chen; mode idle; empty log
- POST http://localhost:3000/api/state with {"mode":"alerting",...} → 200 and echoes mode alerting
- / → Alert shows current Alex; /script → alert\ntimeout\nack Beth\nresolve → idle and log-count 4
