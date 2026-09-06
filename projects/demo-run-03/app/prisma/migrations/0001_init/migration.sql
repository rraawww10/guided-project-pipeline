-- CreateTable
CREATE TABLE "Sku" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" TEXT NOT NULL,
  "on_hand" INTEGER NOT NULL,
  "reorder_point" INTEGER NOT NULL
);

-- CreateTable
CREATE TABLE "PurchaseOrder" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "created_label" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "PurchaseOrderItem" (
  "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  "po_id" INTEGER NOT NULL,
  "sku_id" INTEGER NOT NULL,
  "qty" INTEGER NOT NULL,
  CONSTRAINT "PurchaseOrderItem_po_id_fkey" FOREIGN KEY ("po_id") REFERENCES "PurchaseOrder" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT "PurchaseOrderItem_sku_id_fkey" FOREIGN KEY ("sku_id") REFERENCES "Sku" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Indexes
CREATE INDEX "PurchaseOrderItem_po_id_idx" ON "PurchaseOrderItem" ("po_id");
CREATE INDEX "PurchaseOrderItem_sku_id_idx" ON "PurchaseOrderItem" ("sku_id");
