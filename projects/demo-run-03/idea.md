# Stockroom Reorder Advisor

**One line:** A small Next.js app that calculates which SKUs need reordering and persists suggested purchase orders in SQLite via Prisma.

## Theme
A deterministic, offline-friendly calculation that turns simple inventory facts into concrete reorder quantities. It fits the given stack: Next + React + TypeScript front end, Prisma + SQLite for data, migrations and a seed that run from a clean checkout. No clocks, no vendors, no external APIs.

## Sessions
1. Project and data setup — a table that lists seeded SKUs.
   - Prisma schema for SKU(id, name, on_hand, reorder_point).
   - Migration + seed with ~8 SKUs of varied stock/thresholds.
   - GET /api/skus and a simple React table that renders them.
2. Reorder suggestions — an endpoint that computes qty_to_order.
   - GET /api/reorder-suggestions returns [{sku_id, name, on_hand, reorder_point, qty_to_order}].
   - UI "Suggestions" view lists only rows where qty_to_order > 0.
3. Commit a suggested order — write a PO and its lines atomically.
   - Tables: PurchaseOrder(id, created_label), PurchaseOrderItem(po_id, sku_id, qty).
   - POST /api/purchase-orders accepts selected suggestions and inserts PO + lines in one transaction; confirmation screen lists what was saved.
4. History view with simple totals.
   - GET /api/purchase-orders returns POs with item counts and total qty via a join/aggregate query.
   - UI lists prior POs; selecting one shows its lines.

## What the student types
- The qty_to_order calculation: max(0, reorder_point - on_hand) with a clear guard; shaped server-side and exposed as JSON.
- A Prisma transaction that inserts a parent PurchaseOrder and its child rows safely.
- A join-and-aggregate query to summarize POs (count items, sum qty) for the history list.

## What this teaches that the shipped projects do not
- Deterministic business math that feeds a write path (suggest -> commit) using Prisma transactions, not just display logic.
- Shaping a computed view model at the API layer (not a vanilla list), plus a second screen that queries aggregates.
- End-to-end persistence constraints: migrations + seed from a clean checkout; no runtime network.

## Out of scope
- Receiving/closing POs, vendor catalogs, lead-time math, and stock mutations beyond recording suggested orders.
- Auth, roles, file uploads, and drag-and-drop.

## Risks
- Letting schema scope creep (vendors, receiving) could overload the 4 sessions. Keep the core to thresholds -> suggestions -> commit -> summarize. Seed data must avoid already-sorted orders to keep ordering tests meaningful.