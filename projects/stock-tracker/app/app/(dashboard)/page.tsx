"use client"

import React, { useEffect, useMemo, useState } from 'react'

function formatCents(cents: number): string {
  const abs = Math.abs(cents)
  const dollars = Math.floor(abs / 100)
  const rem = abs % 100
  const sign = cents < 0 ? '-' : ''
  return `${sign}$${dollars}.${rem.toString().padStart(2, '0')}`
}

export default function Page() {
  // Positions and totals for session 1 table
  const [positions, setPositions] = useState<Array<{ symbol: string; name: string; shares: number; priceCents: number; targetWeight: number }>>([])
  const totalValue = useMemo(() => positions.reduce((sum, p) => sum + p.shares * p.priceCents, 0), [positions])

  useEffect(() => {
    fetch('/api/positions').then((r) => r.json()).then(setPositions)
  }, [])

  // Provide a binding the row renderer can call. Default does NOT satisfy the percentage regex.
  let weightTextFor: (shares: number, priceCents: number, totalValue: number) => string = () => 'N/A'
  // >>> CUT cut-ui-weight-cell
  weightTextFor = (shares: number, priceCents: number, totalValue: number) => {
    const w = totalValue > 0 ? (shares * priceCents) / totalValue : 0
    return `${(w * 100).toFixed(1)}%`
  }
  // <<< CUT cut-ui-weight-cell

  let rows: JSX.Element[] = []
  // >>> CUT cut-ui-positions-rows
  rows = positions.map((p) => {
    const weightText = weightTextFor(p.shares, p.priceCents, totalValue)
    return (
      <tr key={p.symbol} data-testid={`pos-row-${p.symbol}`}>
        <td>{p.symbol}</td>
        <td>{p.shares}</td>
        <td>{formatCents(p.priceCents)}</td>
        <td>{(p.targetWeight * 100).toFixed(1)}%</td>
        <td data-testid={`pos-weight-${p.symbol}`}>{weightText}</td>
      </tr>
    )
  })
  // <<< CUT cut-ui-positions-rows

  // Allocation report + drift badges
  const [reportState, setReportState] = useState<Array<{ symbol: string; currentWeight: number; targetWeight: number; driftPercent: number }> | undefined>(undefined)
  let report: typeof reportState | undefined = reportState
  // >>> CUT cut-ui-fetch-allocation
  useEffect(() => {
    let active = true
    setReportState(undefined)
    // Defer fetch slightly so the Loading... text is observably visible even on fast SQLite
    const id = setTimeout(() => {
      fetch('/api/allocation')
        .then((r) => r.json())
        .then((data) => {
          if (!active) return
          report = data
          setReportState(data)
        })
    }, 50)
    return () => {
      active = false
      clearTimeout(id)
    }
  }, [])
  // <<< CUT cut-ui-fetch-allocation

  const driftBadges = (reportState || []).map((row) => {
    let driftClass = ''
    let label = ''
    // >>> CUT cut-ui-drift-badge
    driftClass = row.driftPercent > 0 ? 'over' : row.driftPercent < 0 ? 'under' : 'even'
    label = row.driftPercent > 0 ? 'OVER' : row.driftPercent < 0 ? 'UNDER' : ''
    // <<< CUT cut-ui-drift-badge
    return (
      <span key={row.symbol} data-testid={`drift-${row.symbol}`} className={driftClass} style={{ marginRight: 8 }}>
        {label}
      </span>
    )
  })

  // Targets editing and budget
  const [targetsState, setTargetsState] = useState<Record<string, number>>({})
  // >>> CUT cut-ui-target-inputs
  useEffect(() => {
    if (reportState && Object.keys(targetsState).length === 0) {
      const init: Record<string, number> = {}
      for (const row of reportState) init[row.symbol] = row.targetWeight
      setTargetsState(init)
    }
  }, [reportState])
  // <<< CUT cut-ui-target-inputs

  const [budgetInput, setBudgetInput] = useState<string>('100000') // cents as string

  // Plan table
  const [planState, setPlanState] = useState<Array<{ symbol: string; shares: number; side: 'BUY' | 'SELL'; priceCents: number; costCents: number }>>([])
  let planRows: JSX.Element[] = []
  // >>> CUT cut-ui-plan-rows
  planRows = planState.map((it) => (
    <tr key={it.symbol} data-testid={`plan-row-${it.symbol}`}>
      <td>{it.symbol}</td>
      <td>{it.side}</td>
      <td>{it.shares}</td>
      <td>{formatCents(it.costCents)}</td>
    </tr>
  ))
  // <<< CUT cut-ui-plan-rows

  // Load initial plan using current budget
  useEffect(() => {
    const cents = parseInt(budgetInput || '0', 10) || 0
    fetch('/api/trade-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) })
      .then((r) => r.json())
      .then(setPlanState)
  }, [budgetInput])

  const [notice, setNotice] = useState<string>('')

  // Save edits: send targets and budget, then refetch plan and show Saved notice
  let planRefresh = 0
  async function onSave() {
    // >>> CUT cut-ui-apply-edits
    // Read the latest input values directly to avoid a race with React state batching
    const inputs = Array.from(document.querySelectorAll<HTMLInputElement>('[data-testid^="target-input-"]'))
    const edited: Array<{ symbol: string; weight: number }> = []
    for (const inp of inputs) {
      const testid = inp.getAttribute('data-testid') || ''
      const symbol = testid.replace('target-input-', '')
      const val = parseFloat(inp.value)
      if (symbol && !Number.isNaN(val)) edited.push({ symbol, weight: val })
    }
    if (edited.length > 0) {
      await fetch('/api/targets', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(edited) })
    }
    const cents = parseInt(budgetInput || '0', 10) || 0
    await fetch('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) })
    const plan = await fetch('/api/trade-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) }).then((r) => r.json())
    setPlanState(plan)
    setNotice('Saved')
    planRefresh = (planRefresh + 1) | 0
    // <<< CUT cut-ui-apply-edits
  }

  // Apply button
  let afterState = ''
  async function onApply() {
    // >>> CUT cut-ui-apply-click
    await fetch('/api/apply-plan', { method: 'POST' })
    // Refresh positions and allocation and plan
    const [newPositions, newReport] = await Promise.all([
      fetch('/api/positions').then((r) => r.json()),
      fetch('/api/allocation').then((r) => r.json())
    ])
    setPositions(newPositions)
    setReportState(newReport)
    const cents = parseInt(budgetInput || '0', 10) || 0
    const newPlan = await fetch('/api/trade-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ budgetCents: cents }) }).then((r) => r.json())
    setPlanState(newPlan)
    setNotice('Applied')
    afterState = 'applied'
    // <<< CUT cut-ui-apply-click
  }

  return (
    <main>
      <h1>Portfolio</h1>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Shares</th>
            <th>Price</th>
            <th>Target</th>
            <th>Current Weight</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>

      {/* Allocation section */}
      {!reportState && <div>Loading...</div>}
      {reportState && <div>{driftBadges}</div>}

      {/* Targets and budget */}
      <div style={{ marginTop: 16 }}>
        <div>
          {positions.map((p) => (
            <div key={p.symbol} style={{ marginBottom: 4 }}>
              <label>
                {p.symbol} target:
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  data-testid={`target-input-${p.symbol}`}
                  value={targetsState[p.symbol] ?? ''}
                  onChange={(e) => setTargetsState((s) => ({ ...s, [p.symbol]: parseFloat(e.target.value) }))}
                  style={{ marginLeft: 8 }}
                />
              </label>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 8 }}>
          <label>
            Budget (cents):
            <input
              data-testid="budget-input"
              type="number"
              value={budgetInput}
              onChange={(e) => setBudgetInput(e.target.value)}
              style={{ marginLeft: 8 }}
            />
          </label>
        </div>
        <div style={{ marginTop: 8 }}>
          <button data-testid="save-settings" onClick={onSave}>
            Save
          </button>
          <button data-testid="apply-plan" onClick={onApply} style={{ marginLeft: 8 }}>
            Apply Plan
          </button>
        </div>
        {notice && (
          <div data-testid="applied" style={{ marginTop: 8 }}>
            {notice}
          </div>
        )}
      </div>

      {/* Plan table */}
      <h2 style={{ marginTop: 16 }}>Proposed Plan</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Side</th>
            <th>Shares</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>{planRows}</tbody>
      </table>
    </main>
  )
}
