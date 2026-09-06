# Session 3 - Commit a suggested order

Time: 40 minutes
Students start from: Session 2 done. "/suggestions" shows positive rows; checkboxes and submit do nothing; POST /api/purchase-orders returns 501; the Created page shows zeros.
Students end with: Check two rows → button text includes "(2)"; clicking "Create Purchase Order" POSTs, creates a PO, and navigates to /purchase-orders/created?items=<n>&total=<m> where the page shows both numbers.

What they learn
- Checkbox selection with Set
- POST to a JSON API
- Prisma transaction

Before you start
- Server running, Suggestions page open with at least two positive suggestions.
- Open these files:
  - app/app/suggestions/page.tsx
  - app/app/api/purchase-orders/route.ts
  - app/app/purchase-orders/created/page.tsx

The plan
| Minutes | What you do |
|---|---|
| 0-5 | Frame the goal: select suggestions, commit them atomically, show a confirmation. |
| 5-30 | Live code, in this order: 1) Selection: cut-ui-suggestions-select to toggle ids in a Set without mutating in place. 2) Submit: cut-ui-suggestions-submit to POST the current selection and navigate with ?items=&total=. 3) API transaction: cut-ep-po-create-transaction to write PO + lines in one transaction and return the summary. 4) Created page: cut-ui-po-created-read to read numbers from the URL. |
| 30-38 | Students finish and you circulate. Verify c-3-2..c-3-4 by checking the button count, clicking submit, and reading the numbers on the created page. |
| 38-40 | Bridge: next we’ll show history and detail using aggregate and join queries. |

Cut points in this session
### cut-ui-suggestions-select - app/suggestions/page.tsx:37
- What students see: // TODO(cut-ui-suggestions-select): When a row’s checkbox is toggled, add or remove that sku_id in `selected` and leave all other ids unchanged
- What they write: Implement toggle(id) with setSelected(prev => new Set(prev) then add/remove id, return the new Set).
- Teach it like this: Never mutate a Set in place; always create a new Set to trigger React state updates.
- Passes when: criteria c-3-2 and c-3-3 go green

### cut-ui-suggestions-submit - app/suggestions/page.tsx:51
- What students see: // TODO(cut-ui-suggestions-submit): Build a JSON body from the current `selected` using each line’s qty_to_order, POST it to /api/purchase-orders, and set `nav` to /purchase-orders/created?items={itemsCount}&total={totalQty} when it succeeds
- What they write: Build lines from visible where selected has the id, POST to '/api/purchase-orders', on ok setNav(`/purchase-orders/created?items=${itemsCount}&total=${totalQty}`).
- Teach it like this: Keep read and write shapes separate: Suggestion → { sku_id, qty }. Derive nav from the API’s response, not from client selection.
- Passes when: criterion c-3-3 goes green

### cut-ep-po-create-transaction - app/api/purchase-orders/route.ts:6
- What students see: // TODO(cut-ep-po-create-transaction): In one transaction, insert a new PurchaseOrder with a fixed created_label (e.g. 'manual'), insert one PurchaseOrderItem per line, then set `body` to { id, itemsCount: number of lines, totalQty: sum of qty } and `status` to 200
- What they write: Parse req.json safely; in prisma.$transaction: create PurchaseOrder, createMany lines, compute itemsCount and totalQty; set `body` and 200.
- Teach it like this: Transactions keep parent and children consistent. Even if an insert fails, nothing is half-written.
- Passes when: criterion c-3-1 goes green

### cut-ui-po-created-read - app/purchase-orders/created/page.tsx:9
- What students see: // TODO(cut-ui-po-created-read): Read the items and total numbers from the page URL and write { itemsCount, totalQty } into `summary`
- What they write: Use useSearchParams() to read 'items' and 'total', Number(...) them, and write into summary.
- Teach it like this: The Created page is a Client Component. Hooks only work here; keep the Suspense wrapper as-is.
- Passes when: criterion c-3-4 goes green

Where students get stuck
- "Button count doesn’t change" - They mutated the Set in place. Use setSelected(prev => { const next = new Set(prev); ...; return next }).
- "POST 400/500" - The body shape is wrong or not JSON. Ensure headers 'Content-Type': 'application/json' and body: JSON.stringify({ lines }).
- "@prisma/client not found" or "Can't find schema" - They didn’t build or generate. Re-run npm ci and npm run build.
- "Created page still shows 0 and 0" - They read params on the server. Keep useSearchParams() inside a Client Component and assign to summary.

Check before moving on
- Select two rows, see "Create Purchase Order (2)"; click submit: API returns { id, itemsCount, totalQty }, and the app navigates to /purchase-orders/created?items=<n>&total=<m> where both numbers render.
