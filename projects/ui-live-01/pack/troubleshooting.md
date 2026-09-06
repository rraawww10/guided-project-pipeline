Troubleshooting - Rule-Based Budget Allocator

Real issues students actually hit, with causes and fixes you can say in one line.

API and data
- Error: "Error: HTTP 500" on load – GET /api/transactions still returns 500. Cause: status not set to 200 after reading the file, or JSON parse failed. Fix: set status = 200 when fs.readFile/JSON.parse succeed; keep the try/catch and return [].
- Error: "Edge Runtime does not support Node.js 'fs' module" – Route is running in edge. Cause: missing Node runtime export. Fix: route.ts includes `export const runtime = "nodejs"; export const dynamic = "force-dynamic"` already; don’t remove it.
- Empty table after fixing the API – rows state never updated. Cause: setRows not called. Fix: setRows(data) inside the TODO block after `const data: Tx[] = await res.json()` and behind the cancelled guard.

Rendering and hooks
- Rows render but tests still fail – wrong test id. Cause: used className or a misspelled data-testid. Fix: use exactly data-testid="tx-row" and data-testid="tx-memo" in each row.
- Category or Rule cell missing – categoryCell not assigned. Cause: left categoryCell null. Fix: assign categoryCell to a fragment with both <td> as shown in app/page.tsx.

Rules and labels
- Uber refund shows Income – wrong rule order. Cause: amountGreaterThan before memoContains "uber". Fix: first‑match wins; place the Uber rule before amountGreaterThan.
- Label text disagrees with test – built your own string. Cause: mismatched quotes/case. Fix: use ruleLabel(rule) which yields e.g., memo contains 'uber'.

Grouping and numbers
- Supplies total is -25 – summed signs directly. Cause: forgot spent = -sum(amount). Fix: accumulate with `prev - r.amount`.
- Percent has many decimals – no formatting. Cause: rendered raw ratio. Fix: `row.pct.toFixed(1) + "%"`.
- Delta stays unchanged when typing – budgets are strings. Cause: `e.target.value` not coerced. Fix: `Number(e.target.value)`.

Sort and filter
- Sort appears to do nothing – mutated original data. Cause: in-place sort. Fix: copy before sort: `[...withDelta].sort(...)`.
- Over budget hides everything – used ≥ 0. Cause: wrong predicate. Fix: strictly `delta > 0`.

TypeScript and imports
- TS error: Type '"transport"' is not assignable to type 'Category' – hard‑coded wrong casing. Cause: returned lowercase or a misspelled category. Fix: return one of the union: "Transport" | "Supplies" | "Expense" | "Income" | "Other".
- Module not found for data path – tried to import the JSON at build time. Cause: using import instead of fs.readFile at runtime. Fix: read from `path.join(process.cwd(), "data", "transactions.seed.json")` in the route.

UI state
- Inputs don’t reflect new categories – budgets map never initialized. Cause: missing effect to seed 0s for seen categories. Fix: keep the provided effect that syncs budgets when classified categories change.
