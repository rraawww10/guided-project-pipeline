import type { ClassifiedTx, SummaryRow } from "./types"

export function summarizeByCategory(rows: ClassifiedTx[]): SummaryRow[] {
  let out: SummaryRow[] = []
  // >>> CUT cut-lib-summarize-by-category
  const map = new Map<string, number>()
  for (const r of rows) {
    const prev = map.get(r.category) ?? 0
    map.set(r.category, prev - r.amount) // spent = -sum(amount)
  }
  out = Array.from(map.entries())
    .map(([category, spent]) => ({ category: category as SummaryRow["category"], spent }))
    .sort((a, b) => (a.category < b.category ? -1 : a.category > b.category ? 1 : 0))
  // <<< CUT cut-lib-summarize-by-category
  return out
}
