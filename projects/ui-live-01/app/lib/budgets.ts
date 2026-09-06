import type { Category, SummaryRow, WithDelta } from "./types"

export function computeDelta(summary: SummaryRow[], budgets: Record<Category, number>): WithDelta[] {
  let out: WithDelta[] = []
  // >>> CUT cut-lib-compute-delta
  out = summary.map((row) => {
    const budget = budgets[row.category] ?? 0
    const delta = row.spent - budget
    const pct = budget > 0 ? (row.spent / budget) * 100 : 0
    return { ...row, budget, delta, pct }
  })
  // <<< CUT cut-lib-compute-delta
  return out
}
