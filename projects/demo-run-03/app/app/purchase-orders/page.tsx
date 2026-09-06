"use client"

import { useEffect, useState } from 'react'

type Summary = { id: number; itemsCount: number; totalQty: number }

export default function PurchaseOrdersHistoryPage() {
  const [orders, setOrders] = useState<Summary[]>([])

  // >>> CUT cut-ui-po-history-fetch
  useEffect(() => {
    let active = true
    fetch('/api/purchase-orders').then(r => r.json()).then((arr: Summary[]) => {
      if (active) setOrders(arr)
    }).catch(() => {})
    return () => { active = false }
  }, [])
  // <<< CUT cut-ui-po-history-fetch

  return (
    <main>
      <h1>Purchase Orders</h1>
      <ul>
        {orders.map(o => (
          <li key={o.id} data-testid="po-row">PO #{o.id}: items {o.itemsCount}, total {o.totalQty}</li>
        ))}
      </ul>
    </main>
  )
}
