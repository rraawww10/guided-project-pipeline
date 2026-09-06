# Session 1 - Setup and listing

Time: 40 minutes
Students start from: the skeleton boots with npm run dev; GET /api/transactions answers 500 and the page shows an error.
Students end with: GET /api/transactions returns the seeded array and the page renders one table row per transaction showing each memo.

## What they learn
- Next.js route handler that reads a local JSON file and returns JSON
- Fetching from a local API, React useEffect and state
- Rendering a repeated list with stable data-testid hooks

## Before you start
- From app/: run npm install, then npm run dev, open http://localhost:3000
- Open these files side by side:
  - app/api/transactions/route.ts
  - app/page.tsx
- Keep app/data/transactions.seed.json visible to point at the fixtures.

## The plan
| Minutes | What you do |
|---|---|
| 0-5   | Frame the goal. Show the empty table shape and the error on load. Point at the seed file and the /api/transactions endpoint you will build. |
| 5-18  | Live-code cut-api-transactions-list in app/api/transactions/route.ts. Read the seed file, JSON.parse, 200 on success. Refresh and show the JSON in the browser’s network tab. |
| 18-28 | Live-code cut-ui-fetch-transactions in app/page.tsx. Fetch /api/transactions on mount and set rows. Show loading then the table body filling. |
| 28-35 | Live-code cut-ui-render-rows in app/page.tsx. Map rows to <tr data-testid="tx-row"> and render <td data-testid="tx-memo">. Verify the count matches the seed. |
| 35-38 | Students finish typing, you circulate. Check the page renders one row per item and memos are visible. |
| 38-40 | Recap. What runs now: API 200 with a JSON array; page renders one row per transaction with its memo. Next: classify rows and build a summary. |

## Cut points in this session
### cut-api-transactions-list - skeleton/api/transactions/route.ts:13
- What students see: `// TODO(cut-api-transactions-list): Put every seeded transaction into \`body\` and set \`status\` to 200`
- What they write: read data/transactions.seed.json with fs.readFile, parse to Tx[], assign to body and set status = 200; on error fall back to [] and 500.
- Teach it like this: “Keep return outside the markers; assign body and status inside. Read from the app’s data/ folder at runtime, not at build time.”
- Passes when: criterion c-1-1 goes green.

### cut-ui-fetch-transactions - skeleton/page.tsx:44
- What students see: `// TODO(cut-ui-fetch-transactions): Fetch "/api/transactions" once on load and write the parsed list into \`rows\``
- What they write: inside the try block after await res.json(), set rows to the parsed array (respect the cancelled flag pattern already in the file).
- Teach it like this: “Fetch on mount, parse JSON, set state. Leave dependencies empty so it runs once, and guard setState with the cancelled flag.”
- Passes when: criterion c-1-2 goes green (rows render) and supports c-1-3.

### cut-ui-render-rows - skeleton/page.tsx:113
- What students see: `// TODO(cut-ui-render-rows): Build \`rowsView\` as one <tr data-testid="tx-row"> per item in \`rows\`, including a cell with data-testid="tx-memo" showing its memo`
- What they write: rows.map to <tr key={tx.id} data-testid="tx-row"> with a <td data-testid="tx-memo">{tx.memo}</td>.
- Teach it like this: “Render a stable repeated element. Keys from tx.id; use the exact data-testid hooks the tests read.”
- Passes when: criteria c-1-2 and c-1-3 go green.

## Where students get stuck
- “The page still shows Error: HTTP 500” – API still returns 500 or JSON parse failed – Show the try/catch; ensure status = 200 on success and the file path uses process.cwd()/data/transactions.seed.json.
- “Nothing renders after loading” – setRows was never called – Ensure they placed the setRows inside the cut and after res.json(), and did not early-return before it.
- “I see rows but no memos” – wrong cell markup – The tests read data-testid="tx-memo" inside each tx-row; ensure the attribute is exact and not a className.

## Check before moving on
- With npm run dev, the homepage renders one <tr data-testid="tx-row"> per seed row and each contains a <td data-testid="tx-memo"> with the memo. The API route returns 200 with an array of objects that include id, memo, merchant, amount.
