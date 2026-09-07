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
  // TODO(cut-ui-weight-cell): Compute `weightText` for a row as the current weight percentage to one decimal place (e.g. '12.3%') and render it in the cell with data-testid `pos-weight-${symbol}`

  let rows: JSX.Element[] = []
  // TODO(cut-ui-positions-rows): Build `rows` so it renders one <tr> per position with data-testid `pos-row-${symbol}` and cells for symbol, shares, price and target weight

  // Allocation report + drift badges
  const [reportState, setReportState] = useState<Array<{ symbol: string; currentWeight: number; targetWeight: number; driftPercent: number }> | undefined>(undefined)
  let report: typeof reportState | undefined = reportState
  // TODO(cut-ui-fetch-allocation): Load the allocation report into `report` and render a visible 'Loading...' text while `report` is undefined

  const driftBadges = (reportState || []).map((row) => {
    let driftClass = ''
    let label = ''
    // TODO(cut-ui-drift-badge): Set `driftClass`/label on each row so overweight shows a badge with text 'OVER' and underweight shows 'UNDER' at data-testid `drift-${symbol}`
    return (
      <span key={row.symbol} data-testid={`drift-${row.symbol}`} className={driftClass} style={{ marginRight: 8 }}>
        {label}
      </span>
    )
  })

  // Targets editing and budget
  const [targetsState, setTargetsState] = useState<Record<string, number>>({})
  // TODO(cut-ui-target-inputs): Keep edited weights in `targetsState` per symbol and bind each to an input with data-testid `target-input-${symbol}`

  const [budgetInput, setBudgetInput] = useState<string>('100000') // cents as string

  // Plan table
  const [planState, setPlanState] = useState<Array<{ symbol: string; shares: number; side: 'BUY' | 'SELL'; priceCents: number; costCents: number }>>([])
  let planRows: JSX.Element[] = []
  // TODO(cut-ui-plan-rows): Map the computed plan into `planRows` with data-testid `plan-row-${symbol}` and cells for side, shares and cost

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
    // TODO(cut-ui-apply-edits): On save, send edited targets and budget, then refresh `planRefresh` by refetching the plan so the rows reflect the new values, and show a 'Saved' notice (data-testid 'applied')
  }

  // Apply button
  let afterState = ''
  async function onApply() {
    // TODO(cut-ui-apply-click): On click of the apply button, call the apply endpoint, refresh the positions/allocation, set `afterState` so the notice (data-testid 'applied') is visible, and re-render the tables
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
