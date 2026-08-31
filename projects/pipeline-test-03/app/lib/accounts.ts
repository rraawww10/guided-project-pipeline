/**
 * The three folds session 2 builds: one total per account, the rows of a
 * single account in file order, and the running balance beside them.
 *
 * Nothing here reads the filesystem either - every function takes the accepted
 * entries `parseLedger` already produced.
 */
import type { Entry } from "./ledger"

export type AccountTotal = {
  account: string
  paise: number
}

export function accountTotals(entries: Entry[]): AccountTotal[] {
  const totals: AccountTotal[] = []
  // >>> CUT cut-account-totals
  const summed = new Map<string, number>()
  for (const entry of entries) {
    summed.set(entry.account, (summed.get(entry.account) ?? 0) + entry.paise)
  }
  for (const account of [...summed.keys()].sort()) {
    totals.push({ account, paise: summed.get(account) ?? 0 })
  }
  // <<< CUT cut-account-totals
  return totals
}

export function accountRows(entries: Entry[], name: string): Entry[] {
  const rows: Entry[] = []
  // >>> CUT cut-account-rows
  for (const entry of entries) {
    if (entry.account === name) rows.push(entry)
  }
  rows.sort((a, b) => a.lineNo - b.lineNo)
  // <<< CUT cut-account-rows
  return rows
}

export function runningBalance(rows: Entry[]): number[] {
  const running: number[] = []
  // >>> CUT cut-running-balance
  let carried = 0
  for (const row of rows) {
    carried += row.paise
    running.push(carried)
  }
  // <<< CUT cut-running-balance
  return running
}
