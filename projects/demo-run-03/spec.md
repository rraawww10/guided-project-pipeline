## Outcome
A Next.js + Prisma app that:
- Lists seeded SKUs from SQLite
- Computes reorder suggestions on the server (qty_to_order = max(0, reorder_point - on_hand)) and shows only positive rows
- Commits a selected set of suggestions to the database as a single purchase order with line items
- Shows a history view of prior purchase orders with item counts and total quantity, plus a detail page listing its lines

Data persists via Prisma migrations and a seed that run from a clean checkout. No external network and no clocks.

## Out of scope
- Receiving/closing POs, vendor catalogs, lead-time math, and stock mutations beyond recording suggested orders
- Auth, roles, file uploads, and drag-and-drop

## Data model
- SKU { id: number, name: string, on_hand: number, reorder_point: number }
- PurchaseOrder { id: number, created_label: string }
- PurchaseOrderItem { id: number, po_id: number, sku_id: number, qty: number }
- Suggestion (view model) { sku_id: number, name: string, on_hand: number, reorder_point: number, qty_to_order: number }
- PurchaseOrderSummary (view model) { id: number, itemsCount: number, totalQty: number }
- PurchaseOrderDetail (view model) { id: number, lines: { sku_id: number, name: string, qty: number }[], itemsCount: number, totalQty: number }

Seed: 8 SKUs of varied on_hand and reorder_point so at least 3 have qty_to_order > 0 and at least 2 have qty_to_order == 0.

## Endpoints
- ep-skus-list: GET /api/skus → 200 JSON SKU[]
- ep-reorder-suggestions: GET /api/reorder-suggestions → 200 JSON Suggestion[]
- ep-po-create: POST /api/purchase-orders (PurchaseOrderCreate) → 200 JSON PurchaseOrderCreated
- ep-po-list: GET /api/purchase-orders → 200 JSON PurchaseOrderSummary[]
- ep-po-detail: GET /api/purchase-orders/:id → 200 JSON PurchaseOrderDetail

## Screens
- sc-skus-list: route "/". Renders a table of SKUs, one row per SKU (data-testid="sku-row").
- sc-suggestions: route "/suggestions". Renders Suggestion rows (data-testid="suggestion-row"). Each row shows qty_to_order and includes a checkbox. A button "Create Purchase Order" submits the current selection.
- sc-po-created: route "/purchase-orders/created". Confirmation page that renders itemsCount and totalQty (data-testids: "po-created-items", "po-created-total").
- sc-po-history: route "/purchase-orders". Lists prior purchase orders, one row per PO (data-testid="po-row") showing itemsCount and totalQty.
- sc-po-detail: route "/purchase-orders/[id]". Shows the selected purchase order’s lines, one row per line with the SKU name and qty (data-testid="po-line").

## Sessions

### Session 1 - Setup and SKU list
Goal: Set up Prisma schema, run migration and seed, expose SKUs via an API route, and list them on the home page.

Teaches: ["Prisma schema", "migrations and seed", "Next.js API route basics", "client fetch", "table rendering"]

Builds: [ep-skus-list, sc-skus-list]

Acceptance criteria:
- c-1-1: GET /api/skus returns 200 with a JSON array of SKU with length 8
- c-1-2: sc-skus-list at "/" renders exactly 8 elements with data-testid="sku-row"

Cut points:
- cut-ep-skus-list-query (app/api/skus/route.ts) writes_into: body
  - Hint: Put every SKU the store holds into `body` and set `status` to 200.
- cut-ui-skus-fetch (app/page.tsx) writes_into: items
  - Hint: Fetch GET /api/skus and write the parsed array into `items`, then render one row per SKU.

### Session 2 - Reorder suggestions
Goal: Compute qty_to_order on the server and show only positive suggestions on the Suggestions page.

Teaches: ["shape a computed REST view", "array mapping", "client fetch", "conditional rendering/filter"]

Builds: [ep-reorder-suggestions, sc-suggestions, ep-po-create]

Acceptance criteria:
- c-2-1: GET /api/reorder-suggestions returns 200 with Suggestion[] where for every item qty_to_order == max(0, reorder_point - on_hand)
- c-2-2: sc-suggestions at "/suggestions" renders one element with data-testid="suggestion-row" per item where qty_to_order > 0, and none where qty_to_order == 0
- c-2-3: Each rendered suggestion row shows its qty_to_order in a cell with data-testid="qty-to-order"

Cut points:
- cut-ep-suggestions-calc (app/api/reorder-suggestions/route.ts) writes_into: body
  - Hint: Build `body` as an array of { sku_id, name, on_hand, reorder_point, qty_to_order } where qty_to_order is max(0, reorder_point - on_hand), and set `status` to 200.
- cut-ui-suggestions-fetch (app/suggestions/page.tsx) writes_into: suggestions
  - Hint: Fetch GET /api/reorder-suggestions and write the parsed array into `suggestions`.
- cut-ui-suggestions-filter (app/suggestions/page.tsx) writes_into: visible
  - Hint: Write into `visible` only the suggestions whose qty_to_order is greater than 0.

### Session 3 - Commit a suggested order
Goal: Let the user select suggestions, submit them to create a purchase order in one transaction, and show a confirmation.

Teaches: ["checkbox selection with Set", "POST to a JSON API", "Prisma transaction"]

Builds: [sc-po-created]

Acceptance criteria:
- c-3-1: POST /api/purchase-orders with lines [{sku_id, qty}] returns 200 with JSON { id: number, itemsCount: number, totalQty: number }
- c-3-2: sc-suggestions renders a button with data-testid="po-submit" whose text includes "(2)" after two rows are checked
- c-3-3: After selecting rows and clicking "Create Purchase Order", the app navigates to "/purchase-orders/created?items=<n>&total=<m>"
- c-3-4: sc-po-created renders the two numbers from the URL: data-testid="po-created-items" shows n and data-testid="po-created-total" shows m

Cut points:
- cut-ui-suggestions-select (app/suggestions/page.tsx) writes_into: selected
  - Hint: When a row’s checkbox is toggled, add or remove that sku_id in `selected` and leave all other ids unchanged.
- cut-ui-suggestions-submit (app/suggestions/page.tsx) writes_into: nav
  - Hint: Build a JSON body from the current `selected` using each line’s qty_to_order, POST it to /api/purchase-orders, and set `nav` to "/purchase-orders/created?items={itemsCount}&total={totalQty}" when it succeeds.
- cut-ep-po-create-transaction (app/api/purchase-orders/route.ts) writes_into: body
  - Hint: In one transaction, insert a new PurchaseOrder with a fixed created_label (e.g. "manual"), insert one PurchaseOrderItem per line, then set `body` to { id, itemsCount: number of lines, totalQty: sum of qty } and `status` to 200.
- cut-ui-po-created-read (app/purchase-orders/created/page.tsx) writes_into: summary
  - Hint: Read the items and total numbers from the page URL and write { itemsCount, totalQty } into `summary`.

### Session 4 - Purchase order history and detail
Goal: List prior POs with totals and show a detail page of its lines.

Teaches: ["aggregate queries with Prisma", "detail join query"]

Builds: [ep-po-list, ep-po-detail, sc-po-history, sc-po-detail]

Acceptance criteria:
- c-4-1: GET /api/purchase-orders returns 200 with an array of { id, itemsCount, totalQty }
- c-4-2: sc-po-history at "/purchase-orders" renders one element with data-testid="po-row" per order and shows both itemsCount and totalQty on each row
- c-4-3: GET /api/purchase-orders/:id returns 200 with { id, lines: [{ sku_id, name, qty }], itemsCount, totalQty }
- c-4-4: sc-po-detail at "/purchase-orders/[id]" renders one element with data-testid="po-line" per line, each showing the SKU name and qty

Cut points:
- cut-ui-po-history-fetch (app/purchase-orders/page.tsx) writes_into: orders
  - Hint: Fetch GET /api/purchase-orders and write the parsed array into `orders`.
- cut-ep-po-list-aggregate (app/api/purchase-orders/route.ts) writes_into: body
  - Hint: Query purchase orders with an aggregate to produce { id, itemsCount, totalQty } for each order, write the array into `body`, and set `status` to 200.
- cut-ep-po-detail-join (app/api/purchase-orders/[id]/route.ts) writes_into: body
  - Hint: Query a single purchase order’s lines joined to SKU names, compute itemsCount and totalQty, write { id, lines, itemsCount, totalQty } into `body`, and set `status` to 200.
- cut-ui-po-detail-fetch (app/purchase-orders/[id]/page.tsx) writes_into: po
  - Hint: Fetch GET /api/purchase-orders/:id for the current id and write the parsed object into `po`. 
