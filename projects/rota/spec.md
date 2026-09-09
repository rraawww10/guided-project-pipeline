## Outcome
Build a leave-request validator with explicit reasons. Employees submit inclusive integer day ranges; the engine approves or denies against per-day maxima ("minima" = staffing limits) and explains why. State is persisted to JSON under APP_DIR. One page UI shows a form, the most-recent decisions first, and an Undo Last that reverts the most-recent Approved decision.

## Out of scope
- Real dates, calendars or timezones (use integer day indexes only)
- Recurring rules, partial days, half-days
- External auth/services; no database

## Data model
- DayRange: { start: number; end: number } where start and end are inclusive day indexes. If start > end, the request is invalid.
- Approval: { id: string; employee: string; range: DayRange }
- Decision: { id: string; employee: string; range: DayRange; status: 'Approved' | 'Denied'; reasons: string[] }
- State (persisted): { approvals: Approval[]; decisions: Decision[] }
  - File path: APP_DIR/data/state.json
  - If state.json is absent on first run, create it with { approvals: [], decisions: [] }.
  - Persist decisions in append order with the most-recent decision LAST in the file.
- Minima (persisted): Record<number, number> mapping a day index to the maximum number of approvals allowed that day.
  - File path: APP_DIR/data/minima.json
  - If minima.json is absent on first run, create it with {}.
  - For any day key absent from minima.json, treat the allowed approvals as +∞ (no cap).

Engine rules
- overlaps(a, b): two inclusive ranges overlap when a.start <= b.end AND b.start <= a.end.
- apply(approvals, request, minima):
  - If request.range.start > request.range.end, return { status: 'Denied', reasons: ['invalid-range'] }.
  - Otherwise, compute, for every day d in the inclusive range [start, end], the count of existing approvals that include d. Let cap(d) = minima[d] if present, else +∞. If adding this request would make count(d) + 1 exceed cap(d) for any d, return { status: 'Denied', reasons: [at least one string of the form `minima-breach:day=<d>` for such a day] }.
  - If no day would exceed its cap, return { status: 'Approved', reasons: [] }.

List order
- One list, one order: most-recent-first everywhere. "Most-recent" is defined solely by append order in state.json. /api/state returns decisions sorted most-recent-first by that append order, and the UI renders in that given order without re-sorting.

Undo semantics
- Undo Last removes both the most-recent Approved decision record and its matching Approval from persisted state if one exists. After Undo, that id is no longer considered existing for idempotency; re-submitting the same id will recompute.

## Endpoints
- ep-apply-post: POST /api/apply
  - Request (JSON): { id: string; employee: string; range: DayRange }
  - Response (JSON): Decision. Always 200.
  - Idempotency: if a Decision with the same id exists in persisted state, return that exact Decision and perform no side effects. (Added in Session 2.)
  - Persistence: if the computed Decision is Approved or Denied and no prior Decision with that id exists, append the Decision to state.decisions; if Approved, also append { id, employee, range } to state.approvals. (Added in Session 2.)
  - Minima bootstrap: if minima.json is missing, treat minima as {} (no caps) without error.
- ep-state-get: GET /api/state
  - Response (JSON): { approvals: Approval[]; decisions: Decision[] } with decisions sorted most-recent-first by append order. Always 200. If state.json is missing, create it with { approvals: [], decisions: [] } and return that.
- ep-overlaps-get: GET /api/overlaps?start=NUMBER&end=NUMBER[&employee=STRING]
  - Response (JSON): Approval[] of existing approvals whose ranges overlap [start, end]. Always 200. Results are across all employees; the employee parameter is accepted but ignored.
- ep-undo-last: POST /api/undo-last
  - Effect: remove the most-recent Approved decision and its corresponding Approval from persisted state if one exists.
  - Response (JSON): { removed: Decision | null }. Always 200. removed is the Decision that was removed, or null if there was no Approved decision.

## Screens
- sc-home: route "/"
  - Elements: text input [data-testid="employee-input"], number input [data-testid="start-input"], number input [data-testid="end-input"], text input [data-testid="id-input"], button [data-testid="submit-btn"], button [data-testid="undo-btn"], list container [data-testid="decisions-list"], repeated row [data-testid^="decision-row-"] that includes the decision id and status text.
  - States: empty (no rows), loaded (rows present), after submit, after undo, error (network error text if a fetch fails).
  - List order: most-recent-first everywhere as defined above; the UI renders decisions exactly in the order returned by /api/state.

## Sessions

### Session 1 - Decision engine and basic POST
Goal: Compute a Decision from a request (invalid-range or Approved with reasons=[] when within caps) and expose it at POST /api/apply. No persistence yet is required by the criteria; the endpoint returns computed Decisions.
Teaches: range math, decision engine
Builds: ep-apply-post
Acceptance criteria:
- c-1-1: POST /api/apply returns 200 with a JSON Decision whose status is 'Approved' and reasons is [] for a request whose days do not exceed any minima cap.
  - Cuts: [cut-lib-evaluate-request, cut-ep-apply-assign]
- c-1-2: POST /api/apply returns 200 with a JSON Decision whose status is 'Denied' and reasons equals ['invalid-range'] when start > end.
  - Cuts: [cut-lib-evaluate-request, cut-ep-apply-assign]
Cuts:
- cut-lib-evaluate-request (lib/apply.ts)
  - writes_into: decision
  - Hint: If `decision` is already Denied, keep it. Otherwise, build a reasons array by scanning every day d in the inclusive [start, end] and adding `minima-breach:day=<d>` for each day where count of existing approvals including d plus 1 would exceed the cap (use minima[d] when present, otherwise treat the cap as unlimited). Set `decision` to Denied with those reasons when the array is non-empty; set it to Approved with [] when it is empty.
- cut-ep-apply-assign (app/api/apply/route.ts)
  - writes_into: body
  - Hint: Compute a Decision for the posted request using the engine and assign it to `body`, and set the HTTP `status` to 200.

### Session 2 - Persistence and idempotent POST, bootstrap state
Goal: Persist decisions and approvals to state.json, make POST /api/apply idempotent by id, and expose GET /api/state with bootstrap and ordering (server-side).
Teaches: file-backed state, idempotent upsert
Builds: ep-state-get
Acceptance criteria:
- c-2-1: GET /api/state returns 200 with { approvals: [], decisions: [] } when state.json is absent on first run.
  - Cuts: [cut-ep-state-read-or-init]
- c-2-2: POST /api/apply twice with the same id returns 200 both times with the exact first Decision body and does not create a second record for that id in persisted state.
  - Cuts: [cut-ep-apply-upsert]
- c-2-3: GET /api/state returns 200 with decisions ordered most-recent-first by append order after at least two different ids have been submitted.
  - Cuts: [cut-ep-state-read-or-init]
Cuts:
- cut-ep-state-read-or-init (app/api/state/route.ts)
  - writes_into: body
  - Hint: Read APP_DIR/data/state.json; when the file is missing, create it with { approvals: [], decisions: [] }. Write that state's approvals and decisions into `body`, with `body.decisions` ordered most-recent-first by the file's append order, and set `status` to 200.
- cut-ep-apply-upsert (app/api/apply/route.ts)
  - writes_into: body
  - Hint: Look up a persisted Decision by the posted id; when one exists set `body` to that exact Decision and perform no changes to state. When none exists, compute a new Decision, append it to state.decisions, append to state.approvals only when the Decision is Approved, then set `body` to the Decision with `status` 200.
- cut-lib-overlaps (lib/range.ts)
  - writes_into: overlap
  - Hint: Set `overlap` to whether the two inclusive ranges share any day: a.start <= b.end AND b.start <= a.end.

### Session 3 - UI: hydrate and submit (most-recent-first)
Goal: Build the home page to hydrate from /api/state and submit requests, keeping one row per id with most-recent first.
Teaches: client fetch, list merge by id
Builds: sc-home
Acceptance criteria:
- c-3-1: GET / renders one row per Decision in /api/state and the first row is the most-recent Decision (as returned by /api/state).
  - Cuts: [cut-ui-hydrate-state, cut-ep-state-read-or-init]
- c-3-2: On /, submitting the same id twice shows exactly one row for that id, and its status matches the server's Decision.
  - Cuts: [cut-ui-submit-merge, cut-ep-apply-upsert]
- c-3-3: From /, submitting a request that would exceed a day's cap renders a new Denied row containing a reason that starts with 'minima-breach:day='.
  - Cuts: [cut-ui-submit-merge, cut-lib-evaluate-request]
Cuts:
- cut-ui-hydrate-state (app/page.tsx)
  - writes_into: decisions
  - Hint: On mount, fetch /api/state and replace `decisions` with the response's decisions array as is so the first row is the most-recent; do not re-sort in the client.
- cut-ui-submit-merge (app/page.tsx)
  - writes_into: decisions
  - Hint: On submit, POST /api/apply with the form values; put the returned Decision at the start of `decisions`, keeping only one row for that id by replacing the existing row when one was already present.

### Session 4 - Overlaps and Undo Last (end-to-end)
Goal: Expose overlaps and add Undo Last with a browser flow that persists across reloads.
Teaches: safe revert
Builds: ep-overlaps-get, ep-undo-last
Acceptance criteria:
- c-4-1: GET /api/overlaps?start=NUMBER&end=NUMBER returns 200 with a JSON array of Approval whose ranges overlap [start, end] across all employees.
  - Cuts: [cut-ep-overlaps-build, cut-lib-overlaps]
- c-4-2: POST /api/undo-last returns 200 with { removed: Decision|null } and, when an Approved decision exists, the removed Decision matches the most-recent Approved one in persisted state.
  - Cuts: [cut-ep-undo-last]
- c-4-3: GET /api/overlaps returns the same results whether or not the employee query parameter is present; 'employee' is accepted but ignored.
  - Cuts: [cut-ep-overlaps-build]
- c-4-4: Clicking Undo on / removes the most-recent Approved row from the page and it stays removed after a reload.
  - Cuts: [cut-ui-undo-apply, cut-ep-undo-last, cut-ui-hydrate-state, cut-ep-state-read-or-init]
Cuts:
- cut-ep-overlaps-build (app/api/overlaps/route.ts)
  - writes_into: body
  - Hint: Read all persisted approvals and write into `body` the subset whose ranges overlap the requested [start, end]; ignore any employee filter and set `status` to 200.
- cut-ep-undo-last (app/api/undo-last/route.ts)
  - writes_into: body
  - Hint: If an Approved decision exists in persisted state, remove the most-recent Approved decision and its matching approval from state and set `body` to { removed: that Decision } with `status` 200; otherwise leave state unchanged and set `body` to { removed: null } with `status` 200.
- cut-ui-undo-apply (app/page.tsx)
  - writes_into: decisions
  - Hint: When [data-testid="undo-btn"] is clicked, POST /api/undo-last; after it completes, fetch /api/state and replace `decisions` with its decisions array so the most-recent remains first.
