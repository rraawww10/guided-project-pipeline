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

  // >>> CUT cut-ui-suggestions-fetch
  useEffect(() => {
    let active = true
    fetch('/api/reorder-suggestions').then(r => r.json()).then((arr: Suggestion[]) => {
      if (!active) return
      setSuggestions(arr)
    }).catch(() => {})
    return () => { active = false }
  }, [])
  // <<< CUT cut-ui-suggestions-fetch

  // >>> CUT cut-ui-suggestions-filter
  useEffect(() => {
    setVisible(suggestions.filter(s => s.qty_to_order > 0))
  }, [suggestions])
  // <<< CUT cut-ui-suggestions-filter

  // Declared outside the markers on purpose: the JSX below calls toggle(), so a
  // cut that took the whole declaration left a reference to a name that no
  // longer existed, and the skeleton would not compile. Cut, this is a toggle
  // that does nothing - which is exactly what c-3-2 and c-3-3 should catch.
  let toggle: (id: number) => void = () => {}
  // >>> CUT cut-ui-suggestions-select
  toggle = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }
  // <<< CUT cut-ui-suggestions-select

  // Same reason: the submit button below references this, so the binding has to
  // survive the cut even when its body does not.
  let submit: () => Promise<void> = async () => {}
  // >>> CUT cut-ui-suggestions-submit
  submit = async () => {
    const lines = visible.filter(v => selected.has(v.sku_id)).map(v => ({ sku_id: v.sku_id, qty: v.qty_to_order }))
    const resp = await fetch('/api/purchase-orders', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ lines })
    })
    if (resp.ok) {
      const data = await resp.json() as { itemsCount: number; totalQty: number }
      setNav(`/purchase-orders/created?items=${data.itemsCount}&total=${data.totalQty}`)
    }
  }
  // <<< CUT cut-ui-suggestions-submit

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
