Troubleshooting

These are the errors students actually hit and how to resolve them quickly at the desk.

App won’t start / Next not found
- Symptom: "'next' is not recognized" or "next: command not found".
- Cause: npm ci did not run or failed; an empty node_modules exists.
- Fix: From projects/demo-run-03/app: rm -rf node_modules (if needed); npm ci; npm run build; npm start.

Prisma client not found
- Symptom: Error: Cannot find module '@prisma/client' when the API route runs.
- Cause: prisma generate didn’t run (postinstall skipped) or install failed.
- Fix: npm ci; npm run build (build runs prisma migrate deploy && prisma db seed and triggers generate).

Database table not found / query fails
- Symptom: SQLite error: no such table: Sku (or PurchaseOrder/Item) on first API call.
- Cause: Migrations weren’t applied to prisma/dev.db yet.
- Fix: npm run build (runs prisma migrate deploy). If dev.db is corrupt, delete app/prisma/dev.db and rebuild.

Seed didn’t run / SKUs array is empty
- Symptom: /api/skus returns an empty array.
- Cause: The seed only runs when the Sku table is empty.
- Fix: Delete app/prisma/dev.db and run npm run build again to re-seed.

Suggestions show zeros or include non-positive rows
- Symptom: Qty cell is 0 or rows with qty_to_order == 0 appear.
- Cause: Formula is wrong or the UI didn’t filter by qty_to_order > 0.
- Fix: Server formula should be max(0, reorder_point - on_hand). In the UI, setVisible(suggestions.filter(s => s.qty_to_order > 0)).

Button count never increases
- Symptom: "Create Purchase Order (0)" even after checking boxes.
- Cause: Mutating a Set in place (selected.add(...)) and returning the same object.
- Fix: setSelected(prev => { const next = new Set(prev); next.add(id) or delete; return next }).

POST /api/purchase-orders fails
- Symptom: 400/500 or the created page never navigates.
- Causes:
  - Not sending JSON: missing Content-Type header or body not stringified.
  - Wrong body shape (lines missing sku_id or qty).
  - The server didn’t wrap writes in a transaction and threw.
- Fix: Build body as { lines: [{ sku_id, qty }] }, set headers to application/json. On the server, use prisma.$transaction and return { id, itemsCount, totalQty }.

Created page still shows 0 and 0
- Symptom: data-testids show zeros after navigation.
- Cause: Not reading URL search params, or using a server-only hook.
- Fix: In a Client Component, useSearchParams(), Number(params.get('items') || '0'), same for total, write into summary.

History page always renders 0 items and totals
- Symptom: Every PO row shows items 0, total 0.
- Cause: Summaries query didn’t include items, so items.length is 0 and reduce sums nothing.
- Fix: Include items in the query (include: { items: true }) and map counts/totals from that array.

PO detail lacks names or never loads
- Symptom: Lines show ids with no names, or the list never appears.
- Cause: Missing join to sku, or fetch effect doesn’t wait for id.
- Fix: In API detail, include: { sku: true } and map it.sku.name. In UI, key useEffect on params and guard until id exists.

404s from fetch()
- Symptom: 404 on /api/... endpoints.
- Cause: Path typos (e.g., '/api/reorder-suggestion' vs '/api/reorder-suggestions').
- Fix: Verify exact paths:
  - /api/skus
  - /api/reorder-suggestions
  - /api/purchase-orders
  - /api/purchase-orders/:id

State update after unmount warning
- Symptom: React warns about setting state on an unmounted component.
- Cause: Effect cleanup removed or no active flag.
- Fix: Keep the active flag pattern and cleanup return in useEffect, as in the shipped code.

SQLite database is locked
- Symptom: SQLITE_BUSY: database is locked.
- Cause: Two processes have prisma/dev.db open (another dev server or DB viewer).
- Fix: Stop the other process; if needed, close viewers and restart the dev server.
