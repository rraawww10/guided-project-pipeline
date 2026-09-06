"use client"

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'

function CreatedInner() {
  type Summary = { itemsCount: number; totalQty: number }
  let summary: Summary = { itemsCount: 0, totalQty: 0 }
  // TODO(cut-ui-po-created-read): Read the items and total numbers from the page URL and write { itemsCount, totalQty } into `summary`

  return (
    <main>
      <h1>Purchase Order Created</h1>
      <p>Items: <span data-testid="po-created-items">{summary.itemsCount}</span></p>
      <p>Total qty: <span data-testid="po-created-total">{summary.totalQty}</span></p>
    </main>
  )
}

export default function PurchaseOrderCreatedPage() {
  return (
    <Suspense fallback={
      <main>
        <h1>Purchase Order Created</h1>
        <p>Items: <span data-testid="po-created-items">0</span></p>
        <p>Total qty: <span data-testid="po-created-total">0</span></p>
      </main>
    }>
      <CreatedInner />
    </Suspense>
  )
}
