"use client"

import { useEffect, useState } from 'react'

type Sku = { id: number; name: string; on_hand: number; reorder_point: number }

export default function HomePage() {
  const [items, setItems] = useState<Sku[]>([])

  // TODO(cut-ui-skus-fetch): Fetch GET /api/skus and write the parsed array into `items`, then render one row per SKU

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
