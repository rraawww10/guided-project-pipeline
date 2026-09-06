"use client"

import { useEffect, useState } from 'react'

type Sku = { id: number; name: string; on_hand: number; reorder_point: number }

export default function HomePage() {
  const [items, setItems] = useState<Sku[]>([])

  // >>> CUT cut-ui-skus-fetch
  useEffect(() => {
    let active = true
    fetch('/api/skus').then(r => r.json()).then((data: Sku[]) => {
      if (active) setItems(data)
    }).catch(() => { /* leave empty fallback */ })
    return () => { active = false }
  }, [])
  // <<< CUT cut-ui-skus-fetch

  return (
    <main>
      <h1>SKUs</h1>
      <table>
        <thead>
          <tr><th>Name</th><th>On hand</th><th>Reorder point</th></tr>
        </thead>
        <tbody>
          {items.map((s) => (
            <tr key={s.id} data-testid="sku-row">
              <td>{s.name}</td>
              <td>{s.on_hand}</td>
              <td>{s.reorder_point}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}
