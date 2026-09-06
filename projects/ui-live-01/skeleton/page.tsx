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
  // TODO(cut-ui-render-category-cell): Build `categoryCell` so the row includes a <td data-testid="tx-category"> with the transaction's category and a <td data-testid="tx-rule"> with the matched rule label
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
        // TODO(cut-ui-fetch-transactions): Fetch "/api/transactions" once on load and write the parsed list into `rows`
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
    // TODO(cut-ui-budgets-state): Maintain an in-memory `budgets` map from category to number and update `budgets` when a budget input changes (do not write to the server)
  }

  const summary: SummaryRow[] = useMemo(() => summarizeByCategory(classified), [classified])
  const withDelta: WithDelta[] = useMemo(() => computeDelta(summary, budgets), [summary, budgets])

  const [sortByDelta, setSortByDelta] = useState(false)
  const [showOver, setShowOver] = useState(false)

  let sorted: WithDelta[] = withDelta
  // TODO(cut-ui-sort-by-delta): When the Sort by delta button is clicked, order the displayed summary rows by descending `delta` and write the result into `sorted`

  const visible: WithDelta[] = useMemo(() => {
    let out = sorted
    // TODO(cut-ui-toggle-overbudget): When the Over budget only checkbox is checked, set `showOver` and filter the displayed summary rows to those with `delta` > 0
    return out
  }, [sorted, showOver])

  let rowsView: JSX.Element[] = []
  // TODO(cut-ui-render-rows): Build `rowsView` as one <tr data-testid="tx-row"> per item in `rows`, including a cell with data-testid="tx-memo" showing its memo

  // Session 3 adds its columns and controls to the session 2 summary instead of
  // rebuilding it. Two blocks that each assign summaryView leave the first one
  // dead - the app renders only the second - and a cut whose code never runs
  // grades nothing, whatever the criteria that name it say.
  let deltaControls: JSX.Element | null = null
  let deltaHeaders: JSX.Element | null = null
  let budgetInputs: JSX.Element | null = null
  let deltaCells: (row: WithDelta) => JSX.Element | null = () => null
  // TODO(cut-ui-render-delta): Extend `summaryView` to include Delta (data-testid="summary-delta") and Percent (data-testid="summary-pct") columns and render their values for each row, plus a visible "Delta" header

  let summaryView: JSX.Element | null = null
  // TODO(cut-ui-render-summary): Render a section titled "Summary by category" into `summaryView` with one <tr data-testid="summary-row"> per summary row, each showing data-testid="summary-cat" and data-testid="summary-total"

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
