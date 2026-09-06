import type { Category, SummaryRow, WithDelta } from "./types"

export function computeDelta(summary: SummaryRow[], budgets: Record<Category, number>): WithDelta[] {
  let out: WithDelta[] = []
  // TODO(cut-lib-compute-delta): Join each summary row with its budget (default 0) and write `out` as { category, spent, budget, delta: spent - budget, pct: budget > 0 ? (spent / budget) * 100 : 0 }
  return out
}
