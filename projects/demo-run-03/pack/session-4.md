# Session 4 - Purchase order history and detail

Time: 40 minutes
Students start from: At least one PO created in Session 3. "/purchase-orders" shows an empty list; both /api/purchase-orders and /api/purchase-orders/:id return 501; the detail page shows nothing.
Students end with: History lists one row per PO with itemsCount and totalQty; detail returns and renders joined lines with SKU names and qty.

What they learn
- Aggregate queries with Prisma
- Detail join query

Before you start
- Ensure you have at least one PO from Session 3 (or create one on Suggestions now).
- Open these files:
  - app/app/api/purchase-orders/route.ts (GET summaries)
  - app/app/purchase-orders/page.tsx (history screen)
  - app/app/api/purchase-orders/[id]/route.ts (GET detail)
  - app/app/purchase-orders/[id]/page.tsx (detail screen)
- In a browser: http://localhost:3000/purchase-orders

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Recap and set the target: show a history list and a detail page. |
| 5-30 | Live code, in this order: 1) API summaries: cut-ep-po-list-aggregate in app/app/api/purchase-orders/route.ts. 2) History fetch: cut-ui-po-history-fetch in app/app/purchase-orders/page.tsx. 3) API detail join: cut-ep-po-detail-join in app/app/api/purchase-orders/[id]/route.ts. 4) Detail fetch: cut-ui-po-detail-fetch in app/app/purchase-orders/[id]/page.tsx. Refresh and verify both screens. |
| 30-38 | Students finish and you circulate. Verify history shows itemsCount and totalQty, and detail shows one data-testid="po-line" per line with name and qty. |
| 38-40 | Close: what they built end-to-end. Invite a quick refactor or Q&A if time remains. |

Cut points in this session
### cut-ep-po-list-aggregate - app/api/purchase-orders/route.ts:27
- What students see: // TODO(cut-ep-po-list-aggregate): Query purchase orders with an aggregate to produce { id, itemsCount, totalQty } for each order, write the array into `body`, and set `status` to 200
- What they write: Read all orders, include items, then map to { id, itemsCount: items.length, totalQty: sum of qty }. Set 200.
- Teach it like this: Compute aggregates in code using include: { items: true }. It’s clear and matches our tests.
- Passes when: criteria c-4-1 and c-4-2 go green

### cut-ui-po-history-fetch - app/purchase-orders/page.tsx:10
- What students see: // TODO(cut-ui-po-history-fetch): Fetch GET /api/purchase-orders and write the parsed array into `orders`
- What they write: Fetch '/api/purchase-orders' in useEffect and setOrders(arr).
- Teach it like this: Same client fetch pattern again; the value is in repetition.
- Passes when: criterion c-4-2 goes green

### cut-ep-po-detail-join - app/api/purchase-orders/[id]/route.ts:6
- What students see: // TODO(cut-ep-po-detail-join): Query a single purchase order’s lines joined to SKU names, compute itemsCount and totalQty, write { id, lines, itemsCount, totalQty } into `body`, and set `status` to 200
- What they write: For id from params, findMany items include: { sku: true }, map to { sku_id, name, qty }, compute counts and totals, set 200.
- Teach it like this: Join to the SKU to avoid a second query; then count and sum from the lines you just built.
- Passes when: criteria c-4-3 and c-4-4 go green

### cut-ui-po-detail-fetch - app/purchase-orders/[id]/page.tsx:14
- What students see: // TODO(cut-ui-po-detail-fetch): Fetch GET /api/purchase-orders/:id for the current id and write the parsed object into `po`
- What they write: Read id from useParams(), fetch `/api/purchase-orders/${id}`, setPo(obj) inside an effect keyed on params.
- Teach it like this: Read the dynamic segment from Next’s useParams; gate the fetch until you have an id.
- Passes when: criterion c-4-4 goes green

Where students get stuck
- "History shows zeros" - They didn’t include items in the findMany, so items.length is always 0. Use include: { items: true }.
- "Detail shows ids but not names" - They didn’t join to sku. Use include: { sku: true } and map it.sku.name.
- "Detail never loads" - useParams() id was missing or they didn’t key the effect. Check dependency array and guard for a falsy id.
- "404 on /api/purchase-orders/1" - Wrong template literal or string concatenation. Verify the path and that a PO exists.

Check before moving on
- /purchase-orders lists one row per order with itemsCount and totalQty; navigating to /purchase-orders/<id> renders one data-testid="po-line" per line with the SKU name and qty. Both APIs return 200 with the expected shapes.
