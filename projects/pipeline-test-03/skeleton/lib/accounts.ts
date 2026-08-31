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
  // TODO(cut-account-totals): Fill `totals` with one object per distinct `account` in `entries`, its `paise` the sum of that account paise values, sorted by `account` ascending as plain string order. An account named on no accepted entry never appears, and an account whose values cancel to 0 still appears.
  return totals
}

export function accountRows(entries: Entry[], name: string): Entry[] {
  const rows: Entry[] = []
  // TODO(cut-account-rows): Fill `rows` with every object in `entries` whose account equals `name`, keeping them in ascending `lineNo` order, which is the order they sit in the file. Match the names exactly, so `Rent` does not match `rent`, and leave `rows` empty when no entry names that account.
  return rows
}

export function runningBalance(rows: Entry[]): number[] {
  const running: number[] = []
  // TODO(cut-running-balance): Fill `running` with one number per object in `rows`, in the same order: each one the sum of that object `paise` and of every earlier object `paise`. The first number is the first object own `paise`, the last equals the account total from `accountTotals`, and an empty `rows` gives an empty `running`.
  return running
}
