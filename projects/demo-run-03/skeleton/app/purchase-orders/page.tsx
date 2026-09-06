"use client"

import { useEffect, useState } from 'react'

type Summary = { id: number; itemsCount: number; totalQty: number }

export default function PurchaseOrdersHistoryPage() {
  const [orders, setOrders] = useState<Summary[]>([])

  // TODO(cut-ui-po-history-fetch): Fetch GET /api/purchase-orders and write the parsed array into `orders`

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
