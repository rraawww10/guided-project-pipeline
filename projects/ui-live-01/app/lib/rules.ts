import type { Tx, Rule, Category } from "./types"

export function ruleMatches(tx: Tx, rule: Rule): boolean {
  const { when } = rule
  if (when.memoContains) {
    const needle = when.memoContains.toLowerCase()
    if (!tx.memo.toLowerCase().includes(needle)) return false
  }
  if (when.merchantEquals) {
    if (tx.merchant !== when.merchantEquals) return false
  }
  if (when.amountLessThan !== undefined) {
    if (!(tx.amount < when.amountLessThan)) return false
  }
  if (when.amountGreaterThan !== undefined) {
    if (!(tx.amount > when.amountGreaterThan)) return false
  }
  return true
}

export function ruleLabel(rule: Rule): string {
  const { when } = rule
  if (when.memoContains !== undefined) return `memo contains '${when.memoContains}'`
  if (when.merchantEquals !== undefined) return `merchant == '${when.merchantEquals}'`
  if (when.amountLessThan !== undefined) return `amount < ${when.amountLessThan}`
  if (when.amountGreaterThan !== undefined) return `amount > ${when.amountGreaterThan}`
  return "otherwise"
}

export function applyRules(tx: Tx, rules: Rule[]): Category {
  let out: Category = "Other"
  // >>> CUT cut-lib-apply-rules
  for (const rule of rules) {
    if (ruleMatches(tx, rule)) {
      out = rule.category
      break
    }
  }
  // <<< CUT cut-lib-apply-rules
  return out
}
