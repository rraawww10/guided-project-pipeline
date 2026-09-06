Stockroom Reorder Advisor

What it is
- A Next.js + React + TypeScript app with Prisma + SQLite.
- Lists SKUs, computes reorder suggestions, commits a purchase order, and shows history and detail.
- Data lives in prisma/dev.db. Migrations and seed run from a clean checkout.

How to run it (from a clean clone)
1) Open a terminal at projects/demo-run-03/app
2) Install and build:
   - npm ci
   - npm run build
     • build script (from package.json): "prisma migrate deploy && prisma db seed && next build"
3) Start the app:
   - npm start
4) Visit http://localhost:3000
   - Top nav links (from app/app/layout.tsx): SKUs, Suggestions, PO History

Resetting the database
- The seed only runs when the Sku table is empty (see prisma/seed.ts). To reset to the seeded state:
  - Stop the app
  - Delete app/prisma/dev.db
  - Run npm run build again (this re-applies the migration and re-seeds)
  - npm start

Directories you’ll point at while teaching
- API routes: app/app/api/*
- Screens: app/app/*.tsx under /, /suggestions, /purchase-orders, /purchase-orders/[id], /purchase-orders/created
- Prisma: app/prisma/schema.prisma, app/prisma/seed.ts
- Prisma helper: app/lib/prisma.ts

What must work end-to-end by session
- Session 1: GET /api/skus returns 8; "/" renders 8 rows (data-testid="sku-row").
- Session 2: GET /api/reorder-suggestions shapes qty_to_order = max(0, reorder_point - on_hand); "/suggestions" renders only rows with qty_to_order > 0 and shows the number in each row (data-testid="qty-to-order").
- Session 3: Selecting rows increments the button count; POST /api/purchase-orders creates a PO; navigation to /purchase-orders/created?items=<n>&total=<m> shows both numbers.
- Session 4: GET /api/purchase-orders returns { id, itemsCount, totalQty } per PO and the history page renders them; GET /api/purchase-orders/:id returns { id, lines, itemsCount, totalQty } and the detail page renders lines.

Notes for instructors
- All code snippets in this guide are copied from the shipped app under app/.
- When you show the TODO the student sees, quote it from the skeleton (projects/demo-run-03/skeleton/..).
- Keep Prisma running against the same dev.db during live coding so history screens have data by Session 4.
