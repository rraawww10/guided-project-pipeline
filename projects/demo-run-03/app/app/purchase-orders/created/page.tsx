"use client"

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'

function CreatedInner() {
  type Summary = { itemsCount: number; totalQty: number }
  let summary: Summary = { itemsCount: 0, totalQty: 0 }
  // >>> CUT cut-ui-po-created-read
  const params = useSearchParams()
  const items = Number(params.get('items') || '0')
  const total = Number(params.get('total') || '0')
  summary = { itemsCount: items, totalQty: total }
  // <<< CUT cut-ui-po-created-read

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
