"use client"

import { useEffect, useMemo, useState } from "react"
import type { Tx, Rule, Category, ClassifiedTx, SummaryRow, WithDelta } from "./lib/types"
import { applyRules, ruleLabel, ruleMatches } from "./lib/rules"
import { summarizeByCategory } from "./lib/summary"
import { computeDelta } from "./lib/budgets"

const defaultRules: Rule[] = [
  { id: "r1", when: { merchantEquals: "ACME" }, category: "Supplies" },
  { id: "r2", when: { memoContains: "uber" }, category: "Transport" },
  { id: "r3", when: { amountLessThan: 0 }, category: "Expense" },
  { id: "r4", when: { amountGreaterThan: 0 }, category: "Income" },
]

function buildCategoryCell(tx: Tx): JSX.Element | null {
  let categoryCell: JSX.Element | null = null
  // >>> CUT cut-ui-render-category-cell
  const matched = defaultRules.find((r) => ruleMatches(tx, r))
  const cat = applyRules(tx, defaultRules)
  const label = matched ? ruleLabel(matched) : ""
  categoryCell = (
    <>
      <td data-testid="tx-category">{cat}</td>
      <td data-testid="tx-rule">{label}</td>
    </>
  )
  // <<< CUT cut-ui-render-category-cell
  return categoryCell
}

export default function Page() {
  const [rows, setRows] = useState<Tx[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const res = await fetch("/api/transactions")
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data: Tx[] = await res.json()
        // >>> CUT cut-ui-fetch-transactions
        if (!cancelled) {
          setRows(data)
        }
        // <<< CUT cut-ui-fetch-transactions
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? "Failed to load")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const classified: ClassifiedTx[] = useMemo(() => {
    return rows.map((tx) => {
      // find matching rule id to display; applyRules gives category
      const match = defaultRules.find((r) => ruleMatches(tx, r))
      const category = applyRules(tx, defaultRules)
      return { ...tx, category, ruleId: match ? match.id : "" }
    })
  }, [rows])

  // Budgets state and controls (session 3)
  const [budgets, setBudgets] = useState<Record<Category, number>>({} as Record<Category, number>)
  // initialize budgets to 0 for categories present
  useEffect(() => {
    const cats = new Set<Category>(classified.map((c) => c.category))
    const next: Record<Category, number> = { ...(budgets as any) }
    cats.forEach((c) => {
      if (next[c] === undefined) next[c] = 0
    })
    setBudgets(next)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [classified.length])

  function onBudgetChange(cat: Category, value: number) {
    // >>> CUT cut-ui-budgets-state
    setBudgets((prev) => ({ ...prev, [cat]: value }))
    // <<< CUT cut-ui-budgets-state
  }

  const summary: SummaryRow[] = useMemo(() => summarizeByCategory(classified), [classified])
  const withDelta: WithDelta[] = useMemo(() => computeDelta(summary, budgets), [summary, budgets])

  const [sortByDelta, setSortByDelta] = useState(false)
  const [showOver, setShowOver] = useState(false)

  let sorted: WithDelta[] = withDelta
  // >>> CUT cut-ui-sort-by-delta
  if (sortByDelta) {
    sorted = [...withDelta].sort((a, b) => b.delta - a.delta)
  }
  // <<< CUT cut-ui-sort-by-delta

  const visible: WithDelta[] = useMemo(() => {
    let out = sorted
    // >>> CUT cut-ui-toggle-overbudget
    if (showOver) {
      out = out.filter((r) => r.delta > 0)
    }
    // <<< CUT cut-ui-toggle-overbudget
    return out
  }, [sorted, showOver])

  let rowsView: JSX.Element[] = []
  // >>> CUT cut-ui-render-rows
  rowsView = rows.map((tx) => (
    <tr key={tx.id} data-testid="tx-row">
      <td data-testid="tx-memo">{tx.memo}</td>
      {buildCategoryCell(tx)}
    </tr>
  ))
  // <<< CUT cut-ui-render-rows

  // Session 3 adds its columns and controls to the session 2 summary instead of
  // rebuilding it. Two blocks that each assign summaryView leave the first one
  // dead - the app renders only the second - and a cut whose code never runs
  // grades nothing, whatever the criteria that name it say.
  let deltaControls: JSX.Element | null = null
  let deltaHeaders: JSX.Element | null = null
  let budgetInputs: JSX.Element | null = null
  let deltaCells: (row: WithDelta) => JSX.Element | null = () => null
  // >>> CUT cut-ui-render-delta
  deltaControls = (
    <div style={{ margin: "0.5rem 0" }}>
      <button data-testid="sort-delta" onClick={() => setSortByDelta(true)}>Sort by delta</button>
      <label style={{ marginLeft: "1rem" }}>
        <input
          type="checkbox"
          data-testid="toggle-over"
          checked={showOver}
          onChange={(e) => setShowOver(e.target.checked)}
        />
        Over budget only
      </label>
    </div>
  )
  deltaHeaders = (
    <>
      <th>Delta</th>
      <th>Percent</th>
    </>
  )
  deltaCells = (row) => (
    <>
      <td data-testid="summary-delta">{row.delta}</td>
      <td data-testid="summary-pct">{row.pct.toFixed(1)}%</td>
    </>
  )
  budgetInputs = (
    <div style={{ marginTop: "0.5rem" }}>
      {Object.keys(budgets).map((c) => (
        <label key={c} style={{ marginRight: "1rem" }}>
          {c}
          <input
            type="number"
            step="1"
            data-testid={`budget-${c}`}
            value={budgets[c as Category] ?? 0}
            onChange={(e) => onBudgetChange(c as Category, Number(e.target.value))}
            style={{ marginLeft: "0.5rem", width: 80 }}
          />
        </label>
      ))}
    </div>
  )
  // <<< CUT cut-ui-render-delta

  let summaryView: JSX.Element | null = null
  // >>> CUT cut-ui-render-summary
  summaryView = (
    <section data-testid="summary">
      <h2>Summary by category</h2>
      {deltaControls}
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Total</th>
            {deltaHeaders}
          </tr>
        </thead>
        <tbody>
          {visible.map((row) => (
            <tr key={row.category} data-testid="summary-row">
              <td data-testid="summary-cat">{row.category}</td>
              <td data-testid="summary-total">{row.spent}</td>
              {deltaCells(row)}
            </tr>
          ))}
        </tbody>
      </table>
      {budgetInputs}
    </section>
  )
  // <<< CUT cut-ui-render-summary

  if (loading) return <div>Loading…</div>
  if (error) return <div role="alert">Error: {error}</div>

  return (
    <main style={{ padding: 16 }}>
      <h1>Transactions</h1>
      <table>
        <thead>
          <tr>
            <th>Memo</th>
            <th>Category</th>
            <th>Rule</th>
          </tr>
        </thead>
        <tbody>{rowsView}</tbody>
      </table>

      {summaryView}
    </main>
  )
}
