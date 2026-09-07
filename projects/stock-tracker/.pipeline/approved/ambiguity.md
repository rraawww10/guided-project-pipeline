# Ambiguity report - stock-tracker

**Verdict:** 5 blocking, 6 worth a look

## Blocking
### A1 - Lot size vs single-share allocation
- **Where:** spec.md, Data model; Session 3 cut points (cut-plan-allocate)
- **Owner:** test-runner
- **The line:** "Asset: symbol (PK, string), name (string), lotSize (integer, shares per lot)." and "Build `plan` by allocating integer share quantities that reduce drift, not exceeding `budgetCents`"
- **Reading one:** Plan shares must respect `lotSize` (allocate in multiples of each asset’s lot size).
- **Reading two:** Plan shares are per single share (ignore `lotSize` entirely).
- **Why it matters:** It changes the computed plan and downstream reconciliation; tests will either expect lot-size multiples or single-share quantities, and the Builder must guess which to implement.
- **Suggested wording:** "Allocate integer share quantities in single shares (ignore lotSize)" or "Allocate in integer multiples of each asset’s `lotSize`" — pick one and state it in Session 3 and the TradeItem shape.

### A2 - Target weight input units (percent vs fraction)
- **Where:** spec.md, Data model (Target.weight 0..1) and Session 4 (target inputs, c-4-1, cut-ui-target-inputs)
- **Owner:** test-runner
- **The line:** "Target: ... weight (decimal 0..1)." and "target weight inputs (data-testid=\"target-input-<SYMBOL>\")"
- **Reading one:** UI inputs accept fraction 0..1 (e.g. 0.125 for 12.5%).
- **Reading two:** UI inputs accept percent 0..100 (e.g. 12.5 for 12.5%).
- **Why it matters:** The same keystrokes produce very different plans; tests that edit a weight must agree with the input’s unit.
- **Suggested wording:** "Target inputs accept a fraction 0..1 (e.g. 0.125), persisted as-is" or "Target inputs accept percent 0..100 (e.g. 12.5) and are converted to 0..1 on save".

### A3 - Budget input units (cents vs dollars)
- **Where:** spec.md, Data model (Setting.budgetCents) and Screens; spec.json ep-settings-update request
- **Owner:** test-runner
- **The line:** "Setting: ... budgetCents (integer). Budget is also editable in the UI." and "budget input (data-testid=\"budget-input\")" / "request": "{budgetCents: number}"
- **Reading one:** The UI accepts whole dollars and the server converts to cents on save.
- **Reading two:** The UI accepts raw cents (integer) and saves them unchanged.
- **Why it matters:** A 500 input could mean $500.00 or 500¢; plan generation and budgets will diverge.
- **Suggested wording:** "Budget input is in dollars; server persists `budgetCents = dollars * 100`" or "Budget input is raw cents (integer)".

### A4 - Which budget ep-apply-plan uses
- **Where:** spec.md, Endpoints (ep-apply-plan), Session 4 (settings), Session 5 cut-ep-apply-plan
- **Owner:** test-runner
- **The line:** "ep-apply-plan: POST /api/apply-plan → 200 with {applied, updatedHoldings}" and "Compute the current plan, apply it" (no request body)
- **Reading one:** Apply uses the persisted `budgetCents` from settings.
- **Reading two:** Apply uses the last UI-entered budget transiently (caller must pass/hold it), or a default.
- **Why it matters:** The same holdings produce different applied trades depending on which budget is read; tests must seed and assert against one source of truth.
- **Suggested wording:** "Apply recomputes the plan using the persisted `budgetCents` setting (no request body)" or "Apply requires a `budgetCents` in the request and ignores settings".

### A5 - SELL item semantics in TradeItem (signs and cost)
- **Where:** spec.md, Endpoints (ep-plan-generate), Session 3 criteria c-3-1..c-3-2
- **Owner:** test-runner
- **The line:** "TradeItem[]: {symbol, shares, side: \"BUY\"|\"SELL\", priceCents, costCents}" and "the sum of costCents across BUY items is ≤ budgetCents"
- **Reading one:** Sells appear in the plan with `side: "SELL"`, `shares` positive, and `costCents` either omitted or non-negative (only BUY costs are summed).
- **Reading two:** Sells appear with negative `shares` and negative `costCents`, with the array mixing buys and sells.
- **Why it matters:** Sign and inclusion rules affect cost accounting and reconciliation; the UI and tests must know how to render and total items consistently.
- **Suggested wording:** "Plan includes only BUY items" or "Plan may include SELL items with `side` set; `shares` are positive; `costCents` is non-negative for buys and zero for sells (not counted in c-3-2)." Alternatively specify negative conventions explicitly.

## Worth a look
### W1 - Ranking phrase mixes “absolute” and “positive”
- **Where:** spec.md, Session 3, criterion c-3-3; spec.json c-3-3
- **Owner:** test-runner
- **The line:** "the first plan item's symbol corresponds to the candidate with the largest absolute positive drift"
- **Reading one:** Rank by largest positive drift (overweight only).
- **Reading two:** Rank by largest absolute drift (over- or underweight), i.e. magnitude regardless of sign.
- **Why it matters:** It changes which symbol appears first; the test will pick one reading and the Builder will have to match it.
- **Suggested wording:** "largest positive drift" or "largest absolute drift by magnitude" — choose one.

### W2 - Positions endpoint: name required or not
- **Where:** spec.md, Endpoints (ep-positions-list) vs Session 1 c-1-1; Session 1 cut-ep-positions-body
- **Owner:** nothing
- **The line:** "Position[]: {symbol, name, shares, priceCents, targetWeight}" vs "include symbol, shares, priceCents and targetWeight" (c-1-1)
- **Reading one:** `name` is required by the endpoint contract.
- **Reading two:** `name` is optional; tests only require the four listed fields.
- **Why it matters:** The API shape promised to the UI may drift from what is asserted; a Builder could omit `name` and still pass tests.
- **Suggested wording:** Either add `name` to c-1-1’s required fields or remove it from the endpoint description.

### W3 - Reusing data-testid “applied” for a Saved notice
- **Where:** spec.md, Session 4 cut-ui-apply-edits; Screens; Session 5 c-5-2
- **Owner:** test-runner
- **The line:** "show a 'Saved' notice (data-testid \"applied\")" and screen element "applied notice (data-testid=\"applied\")"
- **Reading one:** The same element/testid is reused for both “Saved” after save and “Applied” after apply.
- **Reading two:** Separate notices are intended and this is a slip; “Saved” should have its own testid.
- **Why it matters:** Tests looking for a specific message may conflict if the same hook serves two meanings.
- **Suggested wording:** Use distinct testids (e.g. `saved` vs `applied`) or state explicitly that the notice uses the same testid with different text.

### W4 - Current weight formatting precision
- **Where:** spec.md, Session 1 c-1-3; Session 1 cut-ui-weight-cell
- **Owner:** test-runner
- **The line:** c-1-3: "(e.g. ends with \"%\")"; cut hint: "to one decimal place (e.g. \"12.3%\")"
- **Reading one:** Any percent format (no specific decimal places) is acceptable.
- **Reading two:** Exactly one decimal place is required.
- **Why it matters:** A Builder showing "12%" vs "12.3%" can make an assertion pass or fail depending on what the test pins.
- **Suggested wording:** "Render with one decimal place (e.g. 12.3%)" or "Render as a percent with any rounding; test asserts only the trailing %".

### W5 - “Refetch the plan” vs POST-only API
- **Where:** spec.md, Session 4 cut-ui-apply-edits; spec.json Endpoints (only POST /api/trade-plan)
- **Owner:** test-runner
- **The line:** "refresh `planRefresh` by refetching the plan" alongside "POST /api/trade-plan with {budgetCents}"
- **Reading one:** The UI should POST again with the (possibly edited/persisted) budget.
- **Reading two:** There is a GET-able plan tied to settings; POST is only for ad-hoc budgets.
- **Why it matters:** The UI wiring and tests differ depending on whether the plan is tied to persisted settings or to a request body.
- **Suggested wording:** "Refetch by POSTing to /api/trade-plan with the current budget" or define a GET /api/trade-plan that reads settings.

### W6 - Weight-sum rounding rule
- **Where:** spec.md, Session 2, criterion c-2-5
- **Owner:** test-runner
- **The line:** "the sum of all currentWeight values across items equals 1.000 when rounded to three decimal places"
- **Reading one:** Sum raw weights then round the total to 3dp and compare to 1.000.
- **Reading two:** Round each item to 3dp, then sum the rounded values and compare to 1.000.
- **Why it matters:** Floating-point and rounding order can change the result; the test must pin one rule.
- **Suggested wording:** "Sum unrounded weights and assert that `round(total, 3) == 1.000`" (or state itemwise rounding explicitly).
