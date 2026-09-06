"use client"

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

type Line = { sku_id: number; name: string; qty: number }

type Detail = { id: number; lines: Line[]; itemsCount: number; totalQty: number }

export default function PurchaseOrderDetailPage() {
  const params = useParams<{ id: string }>()
  const [po, setPo] = useState<Detail | null>(null)

  // TODO(cut-ui-po-detail-fetch): Fetch GET /api/purchase-orders/:id for the current id and write the parsed object into `po`

  return (
    <main>
      <h1>PO Detail</h1>
      <ul>
        {(po?.lines ?? []).map((l, i) => (
          <li key={i} data-testid="po-line">{l.name}: {l.qty}</li>
        ))}
      </ul>
    </main>
  )
}
