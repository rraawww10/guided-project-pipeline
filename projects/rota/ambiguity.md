# Ambiguity report - rota

**Verdict:** 5 blocking, 3 worth a look

## Blocking
### A1 - Overlaps API: what does the `employee` query param do?
- **Where:** spec.md, Endpoints ep-overlaps-get; Session 3, criterion c-3-1
- **Owner:** test-runner
- **The line:** "ep-overlaps-get: GET /api/overlaps?start=NUMBER&end=NUMBER&employee=STRING" and c-3-1: "includes at least one Approval when there is an existing approval in that range"
- **Reading one:** The API filters overlaps to the given employee; only that employee's approvals are considered.
- **Reading two:** The API ignores the employee and returns all approvals that overlap the range, regardless of employee.
- **Why it matters:** The same seeded data can yield empty vs non-empty results depending on whether filtering happens. c-3-1 does not say "for that employee", so a builder who filters by employee could return [] and fail the suite, while another who ignores employee would pass. The test suite is the first place this would surface.
- **Suggested wording:** "GET /api/overlaps returns approvals that overlap the given range, across all employees; the `employee` parameter is ignored." OR "...returns only approvals for `employee` that overlap the given range; results are filtered by employee."

### A2 - Default for days missing from minima.json
- **Where:** spec.md, Data model (Minima), Session 1 criteria c-1-1..c-1-3
- **Owner:** nothing
- **The line:** "Minima ... mapping day index to the maximum number of approvals allowed that day" (no default stated for absent keys); c-1-1 gives a safe request example without mentioning minima for that day.
- **Reading one:** A day absent from minima implies no limit (treat as Infinity or a large number) — approvals on such days never breach minima.
- **Reading two:** A day absent from minima implies zero allowed approvals — any request touching that day must be Denied with a minima-breach reason.
- **Why it matters:** The decision engine's core rule changes: the same request can be Approved or Denied depending on the default. Tests might seed some minima explicitly and leave others implicit; a builder must guess the default to implement `apply`, and that guess can ship because no criterion pins it.
- **Suggested wording:** "For any day key absent from minima.json, treat the allowed approvals as +∞ (no cap)." OR "...treat it as 0 (no approvals permitted)."

### A3 - What defines "most‑recent‑first" on hydration (no timestamp, no source of truth)
- **Where:** spec.md, Screens sc-home (List order), S2 cut-ui-hydrate-from-state hint; spec.md, Endpoints ep-state-get
- **Owner:** nothing
- **The line:** "List order: most‑recent‑first everywhere (hints and criteria)" and "On mount, fetch /api/state and write its decisions into `decisions` with the most‑recent decision first."
- **Reading one:** /api/state returns decisions already ordered most‑recent‑first, and the UI preserves that order.
- **Reading two:** /api/state returns decisions in append order (or unspecified), and the UI is responsible for reordering to most‑recent‑first — but with no timestamp or defined key, "most‑recent" can only mean trusting array order.
- **Why it matters:** Two builders can implement opposite sources of truth (API sorts vs UI sorts) and both pass single-row checks, but diverge after reloads with multiple rows. Without a timestamp or a stated file order invariant, "most‑recent" is uncomputable except by convention. A reload in a later criterion could flip the first row unpredictably.
- **Suggested wording:** "Persist decisions append-most-recent-LAST in state.json. /api/state MUST return them sorted most‑recent‑first by append order, and the UI MUST render in that order (no client re-sort)." OR add "created_at" and define the sort on it.

### A4 - Undo Last: does it remove the Decision record as well as the Approval?
- **Where:** spec.md, Session 3 cut-ep-undo-last hint; c-3-2, c-3-4; Data model (State)
- **Owner:** nothing
- **The line:** "Remove the most‑recent Approved decision from persisted state if one exists" and "Undo via UI removes the most‑recent Approved row."
- **Reading one:** Undo removes only the Approval (capacity), preserving the Decision history; the UI hides a row locally but a reload would show it again.
- **Reading two:** Undo removes both the most‑recent Approval and its Decision record from persisted state; history and UI stay in sync across reloads.
- **Why it matters:** The idempotency rule (return the exact prior Decision for an existing id) conflicts with Undo unless it's clear whether a Decision survives Undo. Keeping the Decision means re-submitting the same id after Undo must short-circuit and not re-approve; removing it means the same id recomputes and can approve. The two behaviours ship different UX and state, and later tests can behave differently across reload.
- **Suggested wording:** "Undo removes both the Approval and its Decision record from persisted state; after Undo the same id is NOT considered existing for idempotency."

### A5 - Behaviour when APP_DIR/data files are absent on first run
- **Where:** spec.md, Data model (paths for state.json and minima.json); spec.md, Endpoints ep-state-get
- **Owner:** nothing
- **The line:** "State (persisted under APP_DIR/data/state.json)" and "Minima (persisted under APP_DIR/data/minima.json)"; ep-state-get always returns 200.
- **Reading one:** Endpoints must create missing files on demand and answer 200 with empty structures (e.g., minima {} and empty arrays) on first boot.
- **Reading two:** Missing files are an error (500), or the app must refuse to start until seeded; ep-state-get cannot promise 200 without explicit seeding.
- **Why it matters:** A builder cannot implement file IO without deciding bootstrapping behaviour. The tests may depend on being able to hit endpoints in a clean working copy. The two choices diverge at runtime and across sessions and can ship undetected if fixtures pre-seed files.
- **Suggested wording:** "If state.json or minima.json is absent, create it with { approvals: [], decisions: [] } and {} respectively and return 200."

## Worth a look
### W1 - UI duplicate handling for idempotent POST
- **Where:** spec.md, Session 2 cut-ui-submit-handler hint; c-2-1
- **Owner:** nothing
- **The line:** "On submit, POST ... then prepend the returned Decision to `decisions` ..."
- **Reading one:** Always prepend whatever the server returned, even if that id already exists in the list.
- **Reading two:** If the returned Decision id already exists, replace the existing row instead of adding a duplicate.
- **Why it matters:** Persisted decisions remain length 1 by c-2-1, but the UI can show duplicates until a reload if it always prepends. Hydration would silently "fix" it, producing a flicker between pre- and post-reload states.
- **Suggested wording:** "If the POST returns a Decision whose id is already present, update that row in place; do not add a duplicate."

### W2 - Range validation when start > end
- **Where:** spec.md, Data model (DayRange); Session 1 engine description
- **Owner:** nothing
- **The line:** "DayRange: { start: number; end: number } where start and end are inclusive day indexes"
- **Reading one:** The engine normalizes ranges (e.g., swaps start/end) before applying rules.
- **Reading two:** The engine treats start > end as invalid and Denies (with or without a specific reason), or rejects the request as a 400.
- **Why it matters:** Different choices change API shape (always 200 vs sometimes 400) and the decision engine's behaviour on malformed input. Tests may avoid this case, so either can ship.
- **Suggested wording:** "If start > end, return 200 with status 'Denied' and reasons ['invalid-range'] (no side effects)."

### W3 - What "most‑recent" means in the absence of timestamps
- **Where:** spec.md, Screens sc-home; S2/S3 hints and criteria referring to most‑recent‑first
- **Owner:** nothing
- **The line:** "most‑recent‑first everywhere (hints and criteria)"
- **Reading one:** "Most‑recent" is defined by append order in the persisted arrays.
- **Reading two:** "Most‑recent" is defined by request id or another implicit key (e.g., lexicographic), since no timestamp exists.
- **Why it matters:** Without an explicit key, different reasonable proxies produce stable but different orders; two builders could ship different UIs that both satisfy the current single-row assertions.
- **Suggested wording:** "Define 'most‑recent' as the last append to decisions; render with that item first. No other ordering key is used."
