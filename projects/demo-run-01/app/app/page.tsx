"use client"

import React from "react"
import { Candidate, RankItem, ToggleToken } from "../lib/types"

function isRankItem(x: Candidate | RankItem): x is RankItem {
  return (x as any).score !== undefined && (x as any).reasons !== undefined
}

export default function Page() {
  const [items, setItems] = React.useState<Array<Candidate | RankItem>>([])

  // active toggle tokens
  const [active, setActive] = React.useState<Set<ToggleToken>>(() => {
    // A deliberately WRONG default, outside the markers. It was `new Set()`,
    // identical to what the block inside assigns - so cutting the block changed
    // nothing and no test could ever grade the task. The skeleton now starts
    // with a toggle switched on, and the student's job is to correct it.
    let init: Set<ToggleToken> = new Set<ToggleToken>(["years"])
    // >>> CUT cut-ui-toggle-init
    init = new Set<ToggleToken>()
    // <<< CUT cut-ui-toggle-init
    return init
  })

  // initial load of candidates
  React.useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const resp = await fetch("/api/candidates")
        if (!resp.ok) return
        const data = await resp.json()
        // >>> CUT cut-ui-load-candidates
        if (!cancelled) setItems(data)
        // <<< CUT cut-ui-load-candidates
      } catch (e) {
        // ignore in demo
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  // fetch ranking when active tokens change
  React.useEffect(() => {
    const tokens = Array.from(active)
    if (tokens.length === 0) return
    let cancelled = false
    async function loadRank() {
      try {
        const qs = new URLSearchParams({ active: tokens.join(",") })
        const resp = await fetch(`/api/rank?${qs.toString()}`)
        if (!resp.ok) return
        const data = await resp.json()
        // >>> CUT cut-ui-rank-fetch
        if (!cancelled) setItems(data)
        // <<< CUT cut-ui-rank-fetch
      } catch (e) {
        // ignore in demo
      }
    }
    loadRank()
    return () => {
      cancelled = true
    }
  }, [active])

  const onToggle = (token: ToggleToken) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setActive((prev) => {
      const next = new Set(prev)
      if (e.target.checked) next.add(token)
      else next.delete(token)
      return next
    })
  }

  return (
    <main>
      <section style={{ marginBottom: 16 }}>
        <label style={{ marginRight: 12 }}>
          <input type="checkbox" data-testid="toggle-years" checked={active.has("years")} onChange={onToggle("years")} /> years
        </label>
        <label>
          <input type="checkbox" data-testid="toggle-tag" checked={active.has("tag")} onChange={onToggle("tag")} /> tag
        </label>
      </section>

      <section>
        {items.map((it) => (
          <div key={(it as any).id} data-testid="card" style={{ padding: 8, border: "1px solid #ddd", marginBottom: 8 }}>
            <div><strong>{(it as any).name}</strong></div>
            {isRankItem(it) ? (
              <>
                <div data-testid="score">{Number(it.score).toFixed(2)}</div>
                <div data-testid="reasons">{it.reasons.join(", ")}</div>
              </>
            ) : null}
          </div>
        ))}
      </section>
    </main>
  )
}
