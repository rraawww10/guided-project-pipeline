import fs from 'node:fs'
import path from 'node:path'

import type { Bill } from './types'

/**
 * The store is read-only. Both functions read data/bills.json on every call and
 * neither writes.
 */

export function readAllBills(): Bill[] {
  let bills: Bill[] = []

  // TODO(cut-store-read-all): Read the bills JSON file from disk with node's fs module, building its path from the process working directory, and put every bill in the file into the bills array declared above, keeping the order the file stores them in.

  return bills
}

export function findBill(id: string): Bill | null {
  const bills = readAllBills()
  let bill: Bill | null = null

  // TODO(cut-store-find-one): Put the bill whose id matches the one asked for into the bill value declared above, leaving it null when the store holds no bill with that id.

  return bill
}
