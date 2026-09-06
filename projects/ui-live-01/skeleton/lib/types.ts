export type Tx = {
  id: string
  memo: string
  merchant: string
  amount: number // negative for spend, positive for refunds/income
}

export type Category = "Transport" | "Supplies" | "Expense" | "Income" | "Other"

export type Rule = {
  id: string
  when: {
    memoContains?: string
    merchantEquals?: string
    amountLessThan?: number
    amountGreaterThan?: number
  }
  category: Category
}

export type ClassifiedTx = Tx & { category: Category; ruleId: string }

export type SummaryRow = { category: Category; spent: number }

export type WithDelta = SummaryRow & { budget: number; delta: number; pct: number }
