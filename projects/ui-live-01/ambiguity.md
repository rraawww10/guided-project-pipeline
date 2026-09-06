# Ambiguity report - ui-live-01

**Verdict:** 3 blocking, 4 worth a look

## Blocking
### A1 - "Matched rule label" is undefined and the quotes conflict
- **Where:** spec.md, Session 2, criterion c-2-2; spec.md, Default rules list; spec.json, Session 2, criterion c-2-2
- **Owner:** test-runner
- **The line:** "shows the matched rule label ... as \"memo contains 'uber'\"" (c-2-2) vs Default rule written as memo contains "uber" (double quotes)
- **Reading one:** The UI must render exactly memo contains 'uber' (single quotes around uber), per c-2-2.
- **Reading two:** The UI derives the label directly from the Default rules prose and renders memo contains "uber" (double quotes), or uses some other derivation (e.g., preserves the case from the memo, or shows the rule id).
- **Why it matters:** The criterion appears to assert an exact string. A Builder has to guess the label grammar and quote style; a different but reasonable choice will fail the test suite.
- **Suggested wording:** "Render the matched rule label exactly as: merchant == 'ACME'; memo contains 'uber' (case-insensitive); amount < 0; amount > 0; otherwise 'Other'. The tx-rule cell must contain the exact substring memo contains 'uber'."

### A2 - No contract for how the UI learns "which rule fired"
- **Where:** spec.json, Session 2, cut `cut-lib-apply-rules` (hint only sets category); spec.md, Data model (ClassifiedTx includes ruleId); spec.md, Session 2, c-2-2; spec.json, Session 2, cut `cut-ui-render-category-cell`
- **Owner:** test-runner
- **The line:** "Walk `rules` in order and set `out` to the first rule’s category ..." (cut-lib-apply-rules) vs "ClassifiedTx: ... { category; ruleId }" and "row includes ... tx-rule with the matched rule label".
- **Reading one:** `applyRules` returns only a Category (as its hint says); the UI cannot tell which rule matched without re-running rule evaluation or changing the library contract.
- **Reading two:** `applyRules` returns both the Category and the matched rule id (or label), despite the hint stating only Category, and the UI renders from that.
- **Why it matters:** Without a defined place to obtain the matched rule, a Builder must invent a shape or duplicate logic. Either choice can disagree with the tests’ expectations about data flow and DOM contents.
- **Suggested wording:** "Define `applyRules(tx, rules): { category: Category; ruleId: string }` and require the UI to render `tx-rule` from that `ruleId` using the label grammar defined in A1."

### A3 - Income and budget checks: include or exclude?
- **Where:** spec.md, Data model → Summary math ("Income ... not used in budget checks"); spec.md, Screens ("one input per category with data-testid=\"budget-<category>\""); spec.md, Session 3 (c-3-1..c-3-4) and cut `cut-lib-compute-delta`
- **Owner:** test-runner
- **The line:** "Income: [+10] → -10 (not used in budget checks)" vs "From session 3: one input per category ..." and "Join each summary row with its budget (default 0)".
- **Reading one:** Every category in the Summary (including Income) gets a budget input and delta/pct cells; "not used in budget checks" is narrative only.
- **Reading two:** Income is shown in the Summary but has no budget input and is excluded from delta/pct and from the over‑budget filter.
- **Why it matters:** The DOM shape (presence of `budget-Income`, delta/percent cells for Income, and filter behaviour) changes by reading. Tests will either fail looking for inputs that do not exist, or pass while students see inconsistent UI behaviour.
- **Suggested wording:** "Render an input for every category present in the summary, including Income, and compute/show delta and pct for all categories; the over‑budget filter includes only rows with delta > 0 (so Income typically hides)." (Or explicitly state that Income is excluded from inputs and delta/pct.)

## Worth a look
### W1 - Number formatting of totals is unspecified
- **Where:** spec.md, Session 2, c-2-3 and c-2-6 ("shows the total for Supplies as 25", "Transport total as 20"); spec.json mirrors
- **Owner:** test-runner
- **The line:** Totals are asserted as bare integers in prose while amounts are decimals in fixtures (e.g., -35.00, +15.00).
- **Reading one:** Display totals as plain numbers with no decimals ("20").
- **Reading two:** Display with fixed 2 decimals ("20.00") or localized formatting (currency, thousands separators).
- **Why it matters:** Tests that assert exact text can fail on formatting alone.
- **Suggested wording:** "Render summary totals as plain numbers with no thousands separators and no decimal part when it is .00 (e.g., 20)."

### W2 - Case sensitivity of merchantEquals is not stated
- **Where:** spec.md, Default rules ("merchant == \"ACME\"")
- **Owner:** test-runner
- **The line:** Only memoContains is explicitly case‑insensitive; merchant equality has no case rule.
- **Reading one:** Compare merchant case‑sensitively ("ACME" only).
- **Reading two:** Normalize case and compare case‑insensitively.
- **Why it matters:** Seeds or future tests with mixed‑case merchants could classify differently.
- **Suggested wording:** "merchantEquals comparisons are case‑sensitive (no normalization)." (Or the opposite.)

### W3 - Less/greater-than comparisons: strict or inclusive?
- **Where:** spec.md, Data model → Rule (amountLessThan / amountGreaterThan)
- **Owner:** test-runner
- **The line:** Operator semantics are not pinned.
- **Reading one:** Strict inequalities (< and >).
- **Reading two:** Inclusive (≤ and ≥).
- **Why it matters:** Edge values at the threshold will classify differently.
- **Suggested wording:** "amountLessThan is strict (<); amountGreaterThan is strict (>)."

### W4 - Which categories appear in the Summary when their total is zero
- **Where:** spec.md, Session 2, c-2-3 ("lists one row per category")
- **Owner:** test-runner
- **The line:** "one row per category" without stating whether this means "per category present in the data" or "all categories in the enum", and whether zero‑total categories are shown.
- **Reading one:** Show only categories that appear in the classified data (non‑empty after grouping).
- **Reading two:** Always show all Category values, including rows with 0.
- **Why it matters:** Changes the count of `summary-row` and the presence of inputs in session 3.
- **Suggested wording:** "Show only categories that have at least one classified transaction (omit zero‑row categories)."