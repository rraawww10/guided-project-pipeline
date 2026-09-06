"use client"

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'

type Suggestion = { sku_id: number; name: string; on_hand: number; reorder_point: number; qty_to_order: number }

export default function SuggestionsPage() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [visible, setVisible] = useState<Suggestion[]>([])
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [nav, setNav] = useState<string | null>(null)
  const router = useRouter()

  // TODO(cut-ui-suggestions-fetch): Fetch GET /api/reorder-suggestions and write the parsed array into `suggestions`

  // TODO(cut-ui-suggestions-filter): Write into `visible` only the suggestions whose qty_to_order is greater than 0

  // Declared outside the markers on purpose: the JSX below calls toggle(), so a
  // cut that took the whole declaration left a reference to a name that no
  // longer existed, and the skeleton would not compile. Cut, this is a toggle
  // that does nothing - which is exactly what c-3-2 and c-3-3 should catch.
  let toggle: (id: number) => void = () => {}
  // TODO(cut-ui-suggestions-select): When a row’s checkbox is toggled, add or remove that sku_id in `selected` and leave all other ids unchanged

  // Same reason: the submit button below references this, so the binding has to
  // survive the cut even when its body does not.
  let submit: () => Promise<void> = async () => {}
  // TODO(cut-ui-suggestions-submit): Build a JSON body from the current `selected` using each line’s qty_to_order, POST it to /api/purchase-orders, and set `nav` to /purchase-orders/created?items={itemsCount}&total={totalQty} when it succeeds

  useEffect(() => {
    if (nav) router.push(nav)
  }, [nav, router])

  const count = useMemo(() => Array.from(selected).filter(id => visible.some(v => v.sku_id === id)).length, [selected, visible])

  return (
    <main>
      <h1>Reorder Suggestions</h1>
      <table>
        <thead>
          <tr><th></th><th>SKU</th><th>On hand</th><th>Reorder point</th><th>Qty to order</th></tr>
        </thead>
        <tbody>
          {visible.map(s => (
            <tr key={s.sku_id} data-testid="suggestion-row">
              <td>
                <input type="checkbox" onChange={() => toggle(s.sku_id)} />
              </td>
              <td>{s.name}</td>
              <td>{s.on_hand}</td>
              <td>{s.reorder_point}</td>
              <td data-testid="qty-to-order">{s.qty_to_order}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button data-testid="po-submit" onClick={submit}>Create Purchase Order ({count})</button>
    </main>
  )
}
