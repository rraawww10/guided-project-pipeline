# Session 3 - Budgets, delta, sort and filter

Time: 40 minutes
Students start from: rows render with category and rule; the Summary section shows Category and Total columns only, no budgets or delta/percent.
Students end with: one input per category controls its budget; Delta and Percent columns render; Sort by delta orders rows descending; Over budget only filters to rows with delta > 0.

## What they learn
- Controlled inputs and updating derived state from them
- Simple numeric transforms and formatted display
- Sorting and predicate filtering on derived lists

## Before you start
- Keep app/page.tsx open. You will only touch this file in this session.
- Point out that lib/budgets.ts already computes budget joins (done last session).

## The plan
| Minutes | What you do |
|---|---|
| 0-5   | Recap: summary shows grouped totals. Today we add budgets, delta/percent, and two controls. |
| 5-12  | Live-code cut-ui-budgets-state. Keep budgets in component state; update on change. |
| 12-22 | Live-code cut-ui-render-delta. Add the controls, headers, cells, and inputs into the existing Summary section. Verify Transport delta changes when you type a budget. |
| 22-28 | Live-code cut-ui-sort-by-delta. Click the button and show rows reorder by delta descending. |
| 28-32 | Live-code cut-ui-toggle-overbudget. Toggle and show non‑over‑budget rows disappear; Transport should hide after setting its budget to 30 in the demo. |
| 32-38 | Students finish and you circulate. |
| 38-40 | What runs now: inputs, delta/percent columns, sort and filter work together. Wrap and point to extension ideas. |

## Cut points in this session
### cut-ui-budgets-state - skeleton/page.tsx:84
- What students see: `// TODO(cut-ui-budgets-state): Maintain an in-memory \`budgets\` map from category to number and update \`budgets\` when a budget input changes (do not write to the server)`
- What they write: setBudgets((prev) => ({ ...prev, [cat]: value })) inside onBudgetChange.
- Teach it like this: “This is a controlled input: update local state only, never the server.”
- Passes when: supports c-3-1..c-3-4; together with render-delta it makes c-3-5 visible.

### cut-ui-render-delta - skeleton/page.tsx:130
- What students see: `// TODO(cut-ui-render-delta): Extend \`summaryView\` to include Delta (data-testid="summary-delta") and Percent (data-testid="summary-pct") columns and render their values for each row, plus a visible "Delta" header`
- What they write: render the Sort/Over‑budget controls, add Delta and Percent headers, render summary-delta and summary-pct cells, and budget inputs with data-testid="budget-<Category>".
- Teach it like this: “Extend the existing summary section; don’t replace it. Percent shows one decimal place with toFixed(1).”
- Passes when: c-3-1, c-3-4 and c-3-5 go green.

### cut-ui-sort-by-delta - skeleton/page.tsx:96
- What students see: `// TODO(cut-ui-sort-by-delta): When the Sort by delta button is clicked, order the displayed summary rows by descending \`delta\` and write the result into \`sorted\``
- What they write: when sortByDelta is true, set sorted = [...withDelta].sort((a, b) => b.delta - a.delta).
- Teach it like this: “Sort a copy, not the original array, to avoid mutating derived data in place.”
- Passes when: c-3-2 goes green.

### cut-ui-toggle-overbudget - skeleton/page.tsx:104
- What students see: `// TODO(cut-ui-toggle-overbudget): When the Over budget only checkbox is checked, set \`showOver\` and filter the displayed summary rows to those with \`delta\` > 0`
- What they write: if (showOver) filter rows where delta > 0.
- Teach it like this: “Filter strictly greater than 0; rows with delta ≤ 0 disappear. Wire the checkbox to setShowOver.”
- Passes when: c-3-3 goes green.

## Where students get stuck
- “Typing 30 doesn’t change the number” – budgets stored as strings – Convert e.target.value to Number before updating; otherwise math concatenates strings.
- “The first row after sorting didn’t change” – sorted the original array – Don’t mutate; spread into a new array before sort.
- “Transport still shows after toggling Over budget” – wrong predicate – Use delta > 0 (strict), not ≥ 0.
- “Percent shows many decimals” – missing formatting – Render with row.pct.toFixed(1) + "%".
- “My Summary heading disappeared” – replaced the whole summary block – Extend the existing section; do not assign a second independent block that overwrites it.

## Check before moving on
- After setting Transport budget to 30, the Transport summary row shows data-testid="summary-delta" as -10 and data-testid="summary-pct" as 66.7%. Clicking Sort by delta orders rows by descending delta (Expense first). Toggling Over budget only hides Transport and leaves Expense visible. c-3-1..c-3-5 are green.
