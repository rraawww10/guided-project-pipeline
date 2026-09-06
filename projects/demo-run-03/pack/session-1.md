# Session 1 - Setup and SKU list

Time: 40 minutes
Students start from: A fresh build and start. Navigation renders; "/" shows an empty table. /api/skus returns 501.
Students end with: GET /api/skus returns 200 with 8 SKUs; "/" renders exactly 8 rows (data-testid="sku-row").

What they learn
- Prisma schema
- Migrations and seed
- Next.js API route basics
- Client fetch with useEffect
- Table rendering

Before you start
- In a terminal: cd projects/demo-run-03/app; npm ci; npm run build; npm start
- Open these files:
  - app/prisma/schema.prisma
  - app/prisma/seed.ts
  - app/app/api/skus/route.ts
  - app/app/page.tsx
- In a browser: http://localhost:3000 (SKUs tab)

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Frame the goal: list the 8 seeded SKUs. Show schema.prisma models and seed.ts to anchor the data. |
| 5-30 | Live code the two cuts in order. 1) API list: implement cut-ep-skus-list-query in app/app/api/skus/route.ts. 2) UI fetch: implement cut-ui-skus-fetch in app/app/page.tsx and render rows. Refresh and watch rows appear. |
| 30-38 | Students finish and you circulate. Check that /api/skus responds 200 with an array and the page renders 8 rows. |
| 38-40 | Recap: API first, then UI. Next session: computed suggestions on the server. |

Cut points in this session
### cut-ep-skus-list-query - app/api/skus/route.ts:6
- What students see: // TODO(cut-ep-skus-list-query): Put every SKU the store holds into `body` and set `status` to 200
- What they write: Query all SKUs with Prisma and assign the array to `body`; set `status` to 200.
- Teach it like this: Start with the data. Read from Prisma, then shape the HTTP response. Keep the return outside the cut so the function always returns a Response.
- Passes when: criterion c-1-1 goes green

### cut-ui-skus-fetch - app/page.tsx:10
- What students see: // TODO(cut-ui-skus-fetch): Fetch GET /api/skus and write the parsed array into `items`, then render one row per SKU
- What they write: In a useEffect with empty deps, fetch '/api/skus', parse JSON to Sku[], and call setItems(data).
- Teach it like this: Fetch on mount, set state, map over items to render <tr data-testid="sku-row">. Keep it client-side (note the "use client" pragma at the top).
- Passes when: criterion c-1-2 goes green

Where students get stuck
- "GET /api/skus 404 or 501" - They edited the wrong file or left the API TODO in place. Point them to app/app/api/skus/route.ts and the TODO line.
- "Table still empty" - They fetched but never set state, or the effect runs on every render. Use useEffect(..., []). Confirm network tab shows 200 and an array of length 8.
- "Type error: fetch result is any" - Add a type assertion on parsed JSON: (data: Sku[]).
- "@prisma/client not found" - They skipped npm ci or build (which runs prisma generate). Re-run npm ci; npm run build.

Check before moving on
- /api/skus returns a 200 JSON array of length 8; the SKUs page renders exactly 8 rows with data-testid="sku-row".
