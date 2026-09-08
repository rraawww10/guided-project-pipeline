# Ambiguity report - shift-rota

**Verdict:** 5 blocking, 8 worth a look

## Blocking
### A1 - No error hook defined on sc-sim but criteria require showing an error
- **Where:** spec.md, Screens -> sc-sim elements; spec.md Session 2 criteria c-2-3 and c-2-5
- **Owner:** test-runner
- **The line:** "Elements: a text element data-testid=\"mode\" ...; [no error element named]" and "... shows an error containing \"only Alex can ack\"" / "... shows an error message containing \"no further escalation\""
- **Reading one:** The UI exposes a dedicated error element (e.g., data-testid="sim-error") where reducer/guard errors are rendered.
- **Reading two:** Errors are surfaced elsewhere (toast, alert(), inline near buttons, or not rendered in DOM at all), with no stable selector.
- **Why it matters:** The Verifier must target a specific element to assert the error text; the Builder must choose a location without guidance. A mismatch makes the UI tests unwriteable or flaky.
- **Suggested wording:** "sc-sim Elements include a text element data-testid=\"sim-error\" that renders the latest reducer/guard error; tests read error texts from this element."

### A2 - Parser vs runner responsibility for unknown actors contradicts
- **Where:** spec.json, Session 3, criterion c-3-2 (cuts: ["cut-parse-line"]; error "unknown actor Dana"); spec.md/spec.json cut-parse-line hint ("do not validate the actor against contacts here"); spec.md c-3-5 (cuts: ["cut-run-script", "cut-parse-line"]) 
- **Owner:** test-runner
- **The line:** "do not validate the actor against contacts here" (cut-parse-line hint) versus c-3-2 "shows ... \"unknown actor Dana\"" with cuts only [cut-parse-line]
- **Reading one:** The parser validates actor names against contacts and returns the "unknown actor Dana" error (so c-3-2 is correct; runner just sequences events).
- **Reading two:** The parser only parses shape (ack <name>); the runner validates the actor against contacts (making c-3-2's cut list and responsibility wrong; c-3-5 suggests this by naming cut-run-script too).
- **Why it matters:** It splits where the error comes from and which cut owns the behavior. A Builder implementing the hint will fail c-3-2; implementing the criterion will violate the hint. Tests will pin one, forcing a rebuild.
- **Suggested wording:** Pick one and align both files: either (a) move validation into the parser (remove "do not validate ..." and keep c-3-2 on cut-parse-line), or (b) keep the hint and change c-3-2 to include cut-run-script (like c-3-5) with wording "runner reports unknown actor Dana".

### A3 - Reducer result shape and log ownership are unspecified and internally inconsistent
- **Where:** spec.md Session 2 cut-logic-reducer-apply hint; spec.md Session 3 cut-run-script hint
- **Owner:** test-runner
- **The line:** "writes_into: out — Hint: Fill `out` by applying one event ... append a log entry ... always carry forward ... into out.next" and "cut-run-script ... append any new log entry the reducer indicates"
- **Reading one:** The reducer returns a Result like { ok, next: State, error? } where next.log already includes the appended entry; the runner should never append logs itself.
- **Reading two:** The reducer signals a log delta separate from next State; the runner is responsible for appending the new log entry to produce the final log.
- **Why it matters:** Double-appending or never-appending changes log-count and contents (e.g., c-3-1 expects 4, c-3-5 expects 1). Without a declared Result type and ownership of appending, a competent Builder must guess.
- **Suggested wording:** "Reducer result type is { ok: boolean; next: State; error?: string }. The reducer mutates next.log to include any new log entry. The runner never appends logs on its own; it uses result.next as-is."

### A4 - Script runner starting state is not defined (seed vs persisted)
- **Where:** spec.md, Screens -> sc-script elements ("log-count showing the number of log rows produced"); Session 3 criteria c-3-1 and c-3-5
- **Owner:** test-runner
- **The line:** No statement of initial State for the script run; c-3-1/5 talk only about the entered lines and "log-count".
- **Reading one:** The script runner always starts from the seed State (contacts [Alex, Beth, Chen], mode idle, empty log), regardless of any persisted live state.
- **Reading two:** The script runner starts from the current persisted State loaded via ep-state-get, so prior manual steps affect outcomes; "log-count" might then be total or delta.
- **Why it matters:** c-3-1 and c-3-5 implicitly assume a fixed baseline (counts 4 and 1). Starting from a mutated live state or counting total vs delta makes these assertions fail.
- **Suggested wording:** "The script runner always starts from the seed State (GET /api/state when the live file is absent) and log-count displays the number of successfully applied lines in this run (delta), not the pre-existing total."

### A5 - File path base for data/state.json is ambiguous (APP_DIR vs relative)
- **Where:** spec.md Outcome ("under APP_DIR"); spec.json/spec.md cut-ep-state-get and cut-ep-state-post hints ("Read data/state.json ... write that object to data/state.json")
- **Owner:** test-runner
- **The line:** "exposes simple endpoints to load/save State as JSON under APP_DIR" vs hints that omit APP_DIR and name bare paths
- **Reading one:** Resolve both files relative to APP_DIR (the env var given to tests), ensuring paths are correct in app/, skeleton/ and clean copies.
- **Reading two:** Use process working directory or a relative path from the route file (e.g., path.resolve("data/state.json")), ignoring APP_DIR.
- **Why it matters:** The same suite runs against app/ and skeleton/ in different CWDs; a relative path can pass locally and fail in the skeleton or deploy contexts. The Builder must guess unless APP_DIR is stated in the hints.
- **Suggested wording:** "Resolve data/state.json and data/state.seed.json against APP_DIR (from process.env), not process CWD."

## Worth a look
### W1 - State names differ between spec.md and spec.json for sc-sim
- **Where:** spec.md Screens -> sc-sim states ("loaded (idle)", "loaded (alerting)"); spec.json screens[0].states (["loaded-idle", "loaded-alerting"]).
- **Owner:** nothing
- **The line:** Two different namings of the same states.
- **Reading one:** Names are descriptive and unused by tests.
- **Reading two:** Names are normative and may be referenced in pack text or tests.
- **Why it matters:** Minor drift that can confuse a reader; unlikely to affect grading but worth aligning.
- **Suggested wording:** Use the same canonical labels in both files.

### W2 - Example script in c-3-1 includes stray leading spaces in spec.json
- **Where:** spec.json c-3-1 check string vs spec.md c-3-1
- **Owner:** nothing
- **The line:** spec.json shows "'alert\n timeout\n ack Beth\n resolve'" while spec.md shows ""alert\ntimeout\nack Beth\nresolve"".
- **Reading one:** Lines are trimmed per the parser hint, so examples with or without leading spaces are equivalent.
- **Reading two:** Examples are literal and the space suggests the parser must accept indented lines.
- **Why it matters:** Low risk, but the two files should agree to avoid test wording drift.
- **Suggested wording:** Make the example identical in both files.

### W3 - Function name vs cut id: "using escalateIndex" vs cut-logic-escalate-index
- **Where:** spec.md Session 2 c-2-2 and cut list
- **Owner:** nothing
- **The line:** "using `escalateIndex`" (unquoted function) while the cut id is "cut-logic-escalate-index".
- **Reading one:** The reducer calls a helper named escalateIndex exported from the same module.
- **Reading two:** The reducer computes the index inline; no helper function exists.
- **Why it matters:** Minor naming drift; not test-visible but could confuse the Builder.
- **Suggested wording:** Either name the helper explicitly and require it, or remove the name from the criterion.

### W4 - Idea/session drift on when persistence is built
- **Where:** idea.md Session 1 ("Persist the log to a JSON file."); spec.json/spec.md place POST /api/state (ep-state-save) in Session 2.
- **Owner:** nothing
- **The line:** Idea asks for persistence in Session 1; spec defers writes to Session 2.
- **Reading one:** Persistence is taught in S1.
- **Reading two:** Persistence is taught in S2.
- **Why it matters:** Teaching flow only; not test-visible, but note the drift.
- **Suggested wording:** Align the session plan or note the deliberate change in why.md.

### W5 - Option order in actor-select not specified
- **Where:** spec.md Screens -> sc-sim elements (actor select listing the contacts)
- **Owner:** test-runner
- **The line:** "a select data-testid=\"actor-select\" listing the contacts"
- **Reading one:** Options appear in contact order [Alex, Beth, Chen].
- **Reading two:** Options sorted alphabetically or by some other rule.
- **Why it matters:** Low risk since tests select by visible text, but order-dependent tests would be brittle.
- **Suggested wording:** "Options are listed in contact order (seed order)."

### W6 - Case sensitivity for actor names not stated
- **Where:** spec.md Data model (Contact: string); script examples use capitalized names
- **Owner:** test-runner
- **The line:** No rule for case matching in parser/validation.
- **Reading one:** Matching is case-sensitive ("beth" is unknown).
- **Reading two:** Matching is case-insensitive ("beth" matches "Beth").
- **Why it matters:** Decides whether inputs like "ack beth" are accepted; tests should pin one.
- **Suggested wording:** "Actor name matching is case-sensitive (must match contacts exactly)."

### W7 - Directory creation behavior for data/ not declared
- **Where:** spec.md/spec.json cut-ep-state-post hint (write to data/state.json)
- **Owner:** test-runner
- **The line:** No instruction to create data/ if missing.
- **Reading one:** Implementations must ensure the directory exists (mkdir -p) before write.
- **Reading two:** Assume tests/seeds create it.
- **Why it matters:** A naive write can fail with ENOENT depending on project scaffolding.
- **Suggested wording:** "Ensure the data directory exists before writing state.json."

### W8 - Reducer error messaging: log on illegal transitions?
- **Where:** spec.md cut-logic-reducer-apply hint ("set ok false with a message ...") and multiple criteria that assert errors but not log effects
- **Owner:** test-runner
- **The line:** No guidance on whether failed transitions also append a log entry.
- **Reading one:** Illegal transitions set ok=false and DO NOT append to log.
- **Reading two:** Illegal transitions also append an explanatory log entry.
- **Why it matters:** Affects log-count and contents if tests or pack reference them; current criteria do not pin it, but clarifying avoids future drift.
- **Suggested wording:** "Illegal transitions do not append log entries."
