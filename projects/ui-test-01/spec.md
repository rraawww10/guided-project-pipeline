## Outcome
A small Next + React + TypeScript app that allocates a paycheck across budget envelopes by deterministic rules and shows a clear rationale for every amount. Students model fixed and percent rules, add caps and ordering, distribute any remainder stably, and can compare two rule sets side-by-side. State can be shared and restored via the URL, and undo/redo is available for scenario edits.

## Out of scope
- External storage or APIs; everything is local state and pure functions.
- Real currency/locale libraries, calendars, or recurring income.
- Rule types beyond fixed amount, percent of paycheck, and a percent with a cap.

## Data model
- Envelope: { id: string; name: string }
- Rule:
  - FixedRule: { id: string; envelopeId: string; kind: "fixed"; amount: number }
  - PercentRule: { id: string; envelopeId: string; kind: "percent"; percent: number }
  - CappedPercentRule: { id: string; envelopeId: string; kind: "percent-cap"; percent: number; cap: number }
- Allocation: Record<envelopeId, number>
- TraceEntry: { envelopeId: string; ruleId: string; before: number; applied: number; after: number; reason: string }
- Scenario state (encoded in URL in session 3): { paycheck: number; envelopes: Envelope[]; rules: Rule[] }

## Endpoints
None. This project is pure UI + pure functions.

## Screens
- sc-main (route "/"): elements include "Paycheck" number input, a simple Rules editor, a Results list with one row per envelope, a "Total allocated" and "Remainder" summary, and per-envelope rationale UI.
  - states: empty (no rules), allocated (rules present and results shown)
- sc-compare (route "/compare"): shows two independent columns (Scenario A and Scenario B) each with its own rules editor and results list, plus a shareable URL field.
  - states: loaded (interactive), restored (state populated from URL)

## Sessions

### Session 1 - First pass allocation
Goal: Build a controlled input for the paycheck, a minimal rules editor, and a pure allocate(paycheck, rules) that applies fixed and percent rules. Render results that update as you type.

Teaches: useState, controlled inputs, mapping data to UI, a pure function over inputs

Acceptance criteria:
- c-1-1: sc-main renders a row for "Rent" with amount 300.00 after entering paycheck 1000 and a fixed rule of 300 to "Rent". (cuts: cut-allocate-fixed, cut-ui-build-rows)
- c-1-2: sc-main renders a row for "Food" with amount 50.00 after entering paycheck 500 and a 10% rule to "Food". (cuts: cut-allocate-percent, cut-ui-build-rows)
- c-1-3: sc-main renders one results row per distinct envelope after adding two envelopes with any rules. (cuts: cut-ui-build-rows)
- c-1-4: On sc-main, changing the Paycheck input from 400 to 600 renders updated totals immediately. (cuts: cut-ui-handle-paycheck-change, cut-ui-build-rows)

Cut points:
- cut-allocate-fixed (app/lib/allocate.ts, writes_into: out)
  Hint: Apply every fixed rule to its target envelope and add the fixed amount into `out` without touching percent rules.
- cut-allocate-percent (app/lib/allocate.ts, writes_into: out)
  Hint: For each percent rule, add paycheck * percent/100 into the matching envelope in `out` using the paycheck as the base.
- cut-ui-build-rows (app/app/page.tsx, writes_into: rows)
  Hint: Build `rows` from the current allocation so each envelope name and its numeric amount appear as a list row.
- cut-ui-handle-paycheck-change (app/app/page.tsx, writes_into: nextPaycheck)
  Hint: Read the input event and parse its numeric value into `nextPaycheck` so the paycheck state can be updated.

### Session 2 - Caps, ordering and rationale
Goal: Add rule priority and caps, implement remainder distribution with a stable order, and generate a per-envelope trace explaining how each amount was computed. Show the rationale in the UI.

Teaches: pure comparators, stable deterministic ordering, capped calculations, building an explanation trace

Acceptance criteria:
- c-2-1: On sc-main, a 50% rule with a cap of 100 applied to paycheck 1000 renders amount 100.00 for its envelope. (cuts: cut-apply-caps, cut-ui-build-rows)
- c-2-2: On sc-main, with two rules for the same envelope at different priorities, the rationale panel renders the higher-priority rule's line before the lower-priority one. (cuts: cut-rules-by-priority, cut-generate-trace, cut-ui-show-rationale)
- c-2-3: On sc-main, with remainder 30 and three eligible envelopes at equal priority, the Results list renders each of those three increased by 10.00. (cuts: cut-distribute-remainder, cut-ui-build-rows)
- c-2-4: On sc-main, expanding an envelope renders at least two rationale lines that include rule identifiers and applied amounts. (cuts: cut-generate-trace, cut-ui-show-rationale)
- c-2-5: On sc-main, after reloading the page with identical inputs, the Results list renders the same per-envelope amounts and the same remainder distribution order. (cuts: cut-distribute-remainder)
- c-2-6: On sc-main, clicking the rationale toggle shows the rationale panel; clicking it again hides the panel. (cuts: cut-ui-show-rationale)

Cut points:
- cut-rules-by-priority (app/lib/rules.ts, writes_into: ordered)
  Hint: Sort the given rules into `ordered` so higher priority comes first and ties are resolved stably by rule id.
- cut-apply-caps (app/lib/allocate.ts, writes_into: out)
  Hint: Limit any percent-with-cap contribution so the envelope’s addition into `out` never exceeds its declared cap.
- cut-distribute-remainder (app/lib/distribute.ts, writes_into: updated)
  Hint: Spread the leftover amount into `updated` across eligible envelopes in a fixed, repeatable order until no remainder or all caps are met.
- cut-generate-trace (app/lib/trace.ts, writes_into: trace)
  Hint: Build `trace` entries that record before, applied and after amounts per rule with a short reason string.
- cut-ui-show-rationale (app/app/page.tsx, writes_into: details)
  Hint: Build `details` for the selected envelope so its rationale text lines render under that row when expanded.

### Session 3 - Compare, undo/redo and shareable URLs
Goal: Let students compare two rule sets side-by-side, add undo/redo to the scenario editor, and encode/decode scenario state in the URL so a scenario opens reproducibly.

Teaches: useReducer, undo/redo patterns, URL encoding/decoding

Acceptance criteria:
- c-3-1: sc-compare renders headings "Scenario A" and "Scenario B" and shows one editor and one results list under each heading. (cuts: cut-ui-compare-columns)
- c-3-2: On sc-compare, after entering different rules into A and B, the page renders different totals per column. (cuts: cut-ui-compare-columns)
- c-3-3: On sc-compare, after pressing Undo, the active editor shows the previous value. (cuts: cut-reducer-undo-redo)
- c-3-4: On sc-compare, after pressing Redo, the active editor shows the value that was undone. (cuts: cut-reducer-undo-redo)
- c-3-5: On sc-compare, opening a copied share URL displays an identical scenario in both the editor and results. (cuts: cut-encode-url, cut-decode-url)
- c-3-6: On sc-compare, changing any scenario field updates the browser URL and the visible share link to show the current state. (cuts: cut-encode-url, cut-ui-share-link)

Cut points:
- cut-ui-compare-columns (app/app/compare/page.tsx, writes_into: rowsB)
  Hint: Build `rowsB` so Scenario B renders its own results list independently from Scenario A.
- cut-reducer-undo-redo (app/lib/state.ts, writes_into: next)
  Hint: Produce `next` from the current state and an action so UNDO steps back one past state and REDO steps forward when available.
- cut-encode-url (app/lib/url.ts, writes_into: url)
  Hint: Encode the current scenario into `url` as a query string that fully describes the scenario.
- cut-decode-url (app/lib/url.ts, writes_into: restored)
  Hint: Parse the browser location and fill `restored` with a complete scenario object so the UI can initialize from it.
- cut-ui-share-link (app/app/compare/page.tsx, writes_into: shareHref)
  Hint: Build `shareHref` from the current browser location so a copyable link always matches the visible scenario.
