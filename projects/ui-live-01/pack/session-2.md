# Session 2 - Allocation engine and summary

Time: 40 minutes
Students start from: a table that renders one row per transaction with each memo; no category/rule cells and no summary section.
Students end with: each row shows its category and the matched rule label; the Summary section renders with a heading and one row per category with correct totals (e.g., Transport 20, Supplies 25).

## What they learn
- Deterministic rule precedence (first‑match wins) in a pure function
- How to surface “which rule fired” for traceability
- Grouping and stable ordering (derived data rendered as a second view)

## Before you start
- Keep app/page.tsx open next to app/lib/rules.ts and app/lib/summary.ts (and app/lib/budgets.ts, implemented in this session for use in session 3)
- Call out the defaultRules array in app/page.tsx and the stable data-testid hooks you will render into

## The plan
| Minutes | What you do |
|---|---|
| 0-5   | Recap the rule list and the goal: first match wins. Show where types live in app/lib/types.ts. |
| 5-12  | Live-code cut-lib-apply-rules in lib/rules.ts. Implement the ordered walk and early break on match. |
| 12-18 | Live-code cut-ui-render-category-cell in page.tsx. For each row, render tx-category and tx-rule using applyRules and ruleMatches/ruleLabel. Refresh and show “Uber trip downtown” as Transport with label memo contains 'uber'. |
| 18-25 | Live-code cut-lib-summarize-by-category in lib/summary.ts. Group by category, spent = -sum(amount), sort by category ascending. Verify numbers from the fixtures (Supplies 25, Transport 20). |
| 25-32 | Live-code cut-ui-render-summary in page.tsx. Render the Summary section with its heading and rows (summary-cat, summary-total). |
| 32-36 | Live-code cut-lib-compute-delta in lib/budgets.ts (not yet shown on screen, used in session 3). Keep it pure and shaped per spec. |
| 36-38 | Students finish typing, you circulate. |
| 38-40 | What runs now: category/rule cells per row; Summary by category with correct totals. Next: budgets, delta/percent, sort and filter. |

## Cut points in this session
### cut-lib-apply-rules - skeleton/lib/rules.ts:32
- What students see: `// TODO(cut-lib-apply-rules): Walk \`rules\` in order and set \`out\` to the first rule's category whose conditions match \`tx\` (memoContains, merchantEquals, amountLessThan/GreaterThan); if none match, set \`out\` to "Other"`
- What they write: loop rules in order, if ruleMatches(tx, rule) assign out = rule.category and break; default remains "Other".
- Teach it like this: “Order is the contract. First match wins, then stop. Keep it a pure function.”
- Passes when: criteria c-2-1 and c-2-4 go green.

### cut-ui-render-category-cell - skeleton/page.tsx:18
- What students see: `// TODO(cut-ui-render-category-cell): Build \`categoryCell\` so the row includes a <td data-testid="tx-category"> with the transaction's category and a <td data-testid="tx-rule"> with the matched rule label`
- What they write: find the matched rule (to label), call applyRules for the category, render two <td> with the exact data-testid values.
- Teach it like this: “Compute both: category from applyRules; label from the matched rule via ruleLabel. Render both cells every row.”
- Passes when: criteria c-2-1 and c-2-2 go green.

### cut-lib-summarize-by-category - skeleton/lib/summary.ts:5
- What students see: `// TODO(cut-lib-summarize-by-category): Group the classified rows by category and write \`out\` as an array of { category, spent } where spent is -sum(amount) for that category, sorted by category name ascending`
- What they write: build a Map<Category, number>, accumulate spent as previous - amount, then map to an array and sort by category string.
- Teach it like this: “Spent is -sum(amount): negatives (spend) increase spent; positives (refunds) reduce it. Sort for a stable UI.”
- Passes when: criteria c-2-3 and c-2-6 go green.

### cut-ui-render-summary - skeleton/page.tsx:177
- What students see: `// TODO(cut-ui-render-summary): Render a section titled "Summary by category" into \`summaryView\` with one <tr data-testid="summary-row"> per summary row, each showing data-testid="summary-cat" and data-testid="summary-total"`
- What they write: section with h2 "Summary by category" and a table whose body maps visible rows to summary-row, with summary-cat and summary-total cells.
- Teach it like this: “Render exactly one visible heading with this text; one summary row per grouped category with those data-testid hooks.”
- Passes when: criterion c-2-5 goes green; together with summarize/applyRules it enables c-2-3 and c-2-6.

### cut-lib-compute-delta - skeleton/lib/budgets.ts:5
- What students see: `// TODO(cut-lib-compute-delta): Join each summary row with its budget (default 0) and write \`out\` as { category, spent, budget, delta: spent - budget, pct: budget > 0 ? (spent / budget) * 100 : 0 }`
- What they write: map summary to WithDelta, look up budgets[row.category] || 0, compute delta and pct as specified.
- Teach it like this: “Pure transform. Do not read time or global state. Return shaped rows for the UI to render next session.”
- Passes when: supports session‑3 criteria; nothing in session 2 asserts it directly.

## Where students get stuck
- “Uber refund shows Income, not Transport” – rule order wrong – First match wins; place the memoContains "uber" rule before amountGreaterThan.
- “Supplies total is negative” – wrong sign on grouping – Spent is -sum(amount). A -25 expense produces +25 spent; a +15 refund reduces spent to 10.
- “The label doesn’t match the test” – inconsistent label grammar – Use ruleLabel and render memo contains 'uber' with single quotes, exactly as written.
- “Summary rows appear in a random order” – missing sort – Sort by category ascending for a stable UI and testable order.

## Check before moving on
- The table shows a Category and a Rule cell for every row. The Summary section renders once with heading "Summary by category" and rows whose totals match the fixtures (e.g., Supplies 25; Transport 20). Tests c-2-1..c-2-6 are green.
