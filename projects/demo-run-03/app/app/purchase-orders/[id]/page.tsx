"use client"

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

type Line = { sku_id: number; name: string; qty: number }

type Detail = { id: number; lines: Line[]; itemsCount: number; totalQty: number }

export default function PurchaseOrderDetailPage() {
  const params = useParams<{ id: string }>()
  const [po, setPo] = useState<Detail | null>(null)

  // >>> CUT cut-ui-po-detail-fetch
  useEffect(() => {
    const id = params?.id as string
    if (!id) return
    let active = true
    fetch(`/api/purchase-orders/${id}`).then(r => r.json()).then((obj: Detail) => {
      if (active) setPo(obj)
    }).catch(() => {})
    return () => { active = false }
  }, [params])
  // <<< CUT cut-ui-po-detail-fetch

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
