# Ambiguity report - demo-run-03

**Verdict:** 2 blocking, 3 worth a look

## Blocking
### A1 - POST body shape and field names are not pinned
- **Where:** spec.md, Session 3, criterion c-3-1; spec.json, endpoints[ep-po-create]
- **Owner:** test-runner
- **The line:** "c-3-1: POST /api/purchase-orders with lines [{sku_id, qty}] returns 200 with JSON { id: number, itemsCount: number, totalQty: number }" and in spec.json: `"request": "PurchaseOrderCreate"`
- **Reading one:** The request body is an object `{ lines: [{ sku_id, qty }] }`, where `qty` is derived from each suggestion's `qty_to_order`.
- **Reading two:** The request body is the bare array `[{ sku_id, qty_to_order }]` (or `[{ sku_id, qty }]`) with no `lines` envelope. The presence of `PurchaseOrderCreate` in spec.json suggests a named shape but it is not defined anywhere.
- **Why it matters:** The UI submit cut and the API create cut can be implemented to different, incompatible shapes; the suite will go red at step 6 and the Builder/test loop will have to rework one side. Until fixed, progress stalls on a guess.
- **Suggested wording:** "POST /api/purchase-orders accepts a JSON body of the form `{ lines: [{ sku_id: number, qty: number }] }` (where `qty` is the row's `qty_to_order`) and returns 200 with `{ id, itemsCount, totalQty }`."

### A2 - "Show only positive suggestions" can be read as server filter or client filter
- **Where:** spec.md, Session 2, Goal; spec.md, Session 2, criterion c-2-2
- **Owner:** mutation
- **The line:** "Goal: Compute qty_to_order on the server and show only positive suggestions on the Suggestions page." and "c-2-2: sc-suggestions at \"/suggestions\" renders one element with data-testid=\"suggestion-row\" per item where qty_to_order > 0, and none where qty_to_order == 0"
- **Reading one:** The endpoint `/api/reorder-suggestions` returns all SKUs (including zeros) and the UI cut `cut-ui-suggestions-filter` filters client-side to hide zeroes.
- **Reading two:** The endpoint already filters to only positive rows, so the UI filter cut is a no-op and the screen simply renders what it is given.
- **Why it matters:** If the server filters, `cut-ui-suggestions-filter` becomes toothless: removing it still leaves c-2-2 green. `skeleton-check` cannot see this; only the mutation run can prove the cut grades something. Grading integrity depends on pinning where the filter lives.
- **Suggested wording:** "The `/api/reorder-suggestions` endpoint returns all SKUs with `qty_to_order` (including zeros); the Suggestions page must filter client-side to display only rows with `qty_to_order > 0`."

## Worth a look
### W1 - Create/Created types are referenced but not defined
- **Where:** spec.json, endpoints[ep-po-create] `"request": "PurchaseOrderCreate"`, `"response": "PurchaseOrderCreated"`; spec.md has no corresponding type entries
- **Owner:** nothing
- **The line:** `"request": "PurchaseOrderCreate"`, `"response": "PurchaseOrderCreated"`
- **Reading one:** These are formal named shapes defined elsewhere in the spec and used consistently.
- **Reading two:** They are placeholders; the real shapes are only described informally in c-3-1 and in hints.
- **Why it matters:** The reader has to chase between files to infer the shapes; a future change risks drift. Not a build-stopper, but it weakens the contract the Test Writer keys off.
- **Suggested wording:** Add both to the Data model section, e.g. `PurchaseOrderCreate { lines: { sku_id: number, qty: number }[] }` and `PurchaseOrderCreated { id: number, itemsCount: number, totalQty: number }`.

### W2 - itemsCount semantics on the list endpoint are implied, not stated
- **Where:** spec.md, Session 4, criterion c-4-1; spec.md, Session 3, cut-ep-po-create-transaction hint
- **Owner:** test-runner
- **The line:** "c-4-1: GET /api/purchase-orders returns 200 with an array of { id, itemsCount, totalQty }"
- **Reading one:** `itemsCount` means "number of lines in that purchase order", matching the Session 3 hint for the create response.
- **Reading two:** `itemsCount` could be interpreted as "number of SKUs with qty > 0" or another tally derived at read time.
- **Why it matters:** Tests that derive expected values from seeded data need the precise definition to assert the right number; otherwise two reasonable implementations can disagree.
- **Suggested wording:** "Each element is `{ id, itemsCount: number of lines in the order, totalQty: sum of all line qty }`."

### W3 - Row order is unspecified for history and detail
- **Where:** spec.md, Session 4, criteria c-4-2 and c-4-4
- **Owner:** test-runner
- **The line:** "sc-po-history ... renders one element with data-testid=\"po-row\" per order" and "sc-po-detail ... renders one element with data-testid=\"po-line\" per line"
- **Reading one:** Any stable order (e.g. id ASC) is acceptable; tests only assert counts and contents.
- **Reading two:** A particular order (e.g. newest first, or by SKU name) is intended.
- **Why it matters:** If a test ever asserts a position, the lack of a declared order can produce flaky failures across equally reasonable implementations.
- **Suggested wording:** "Rows may appear in any order; tests assert presence and counts only" or specify the intended sort (e.g. "newest first by id").
