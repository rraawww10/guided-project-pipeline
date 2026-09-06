# Session 1 - App boots and shows data

Time: 40 minutes
Students start from: Next dev server boots; the home page renders the header and static UI, APIs return 501 and lists are empty.
Students end with: GET /api/expenses returns 200 with the 4 seeded expenses, the page shows 4 expense rows and a 5-row totals-paid summary with exact amounts.

What they learn
- Fetch in the Next.js app router and basic error/loading handling
- Mapping arrays to a table
- Summing integer cents per payer for a simple summary

Before you start
- Run npm ci, then npm run dev from app/ and open http://localhost:3000
- Have these files open side by side: app/app/api/expenses/route.ts and app/app/page.tsx
- Show app/data/expenses.seed.json once so they see the shape they will return

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Set the goal: serve the seed via /api/expenses and render it. Show the seed file and the empty UI. |
| 5-12 | Live-code the API cut so /api/expenses returns 200 and the 4 items. Verify in the browser. |
| 12-22 | Live-code the client fetch and set state. Show 4 expense rows render with formatMoney. Keep existing error/loading as is. |
| 22-30 | Compute the per-person totals-paid summary. Explain integer cents and seeding all names to 0 so Eve renders as $0.00. |
| 30-38 | Students finish and you circulate. Run the UI checks for counts and exact amounts. |
| 38-40 | Recap: API returns the seed; UI shows 4 rows and a 5-row summary. Next: balances and naive transfers. |

Cut points in this session
### cut-api-expenses-list - app/api/expenses/route.ts:7
- What students see: // TODO(cut-api-expenses-list): Put every expense from the seed store into `body` and set `status` to 200
- What they write: Call the seed loader, assign the array to body, then set status to 200 before returning.
- Teach it like this: “Keep the typed fallback above; only assign into body and status so the return stays outside the markers.”
- Passes when: c-1-1 goes green.

### cut-ui-load-expenses - app/page.tsx:22
- What students see: // TODO(cut-ui-load-expenses): Fetch "/api/expenses" and write the parsed JSON array into `items`; keep the existing error and loading state handling unchanged
- What they write: Inside the try, fetch "/api/expenses", check resp.ok, await resp.json() into a local loaded array. Do not set state until finally.
- Teach it like this: “Fetch, guard on HTTP errors, parse JSON, and let the finally set state so loading clears even on error.”
- Passes when: c-1-2 goes green (4 expense rows render).

### cut-ui-compute-paid-totals - app/page.tsx:97
- What students see: // TODO(cut-ui-compute-paid-totals): Accumulate the sum of `amountCents` each payer contributed into `totals` keyed by person id using integer cents already present in `items`
- What they write: Seed every known person to 0, then for each expense add amountCents to the payer’s total using integer adds.
- Teach it like this: “Keep it integer from end to end. Seed names so people who paid nothing still render as $0.00.”
- Passes when: c-1-3 goes green (5 rows with exact amounts).

Where students get stuck
- “/api/expenses returns 501” — forgot to set status to 200 — Say: Set status after writing body; the return uses that status.
- “TypeError: resp.json is not a function” — missing await on fetch or using the response twice — Say: await fetch, then await resp.json() once.
- “Totals list misses Eve” — didn’t seed totals for all names — Say: initialise every known name to 0 before summing.
- “The table is empty but no error shows” — setState calls done inside try before loaded is filled — Say: fill local loaded, then setItems in finally.

Check before moving on
- The page shows 4 expense rows; totals-paid shows 5 rows with exact amounts; GET /api/expenses answers 200 with 4 items.
