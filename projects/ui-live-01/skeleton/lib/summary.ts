import type { ClassifiedTx, SummaryRow } from "./types"

export function summarizeByCategory(rows: ClassifiedTx[]): SummaryRow[] {
  let out: SummaryRow[] = []
  // TODO(cut-lib-summarize-by-category): Group the classified rows by category and write `out` as an array of { category, spent } where spent is -sum(amount) for that category, sorted by category name ascending
  return out
}
