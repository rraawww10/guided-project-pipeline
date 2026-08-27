import fs from 'node:fs'
import path from 'node:path'

import type { Bill } from './types'

/**
 * The store is read-only. Both functions read data/bills.json on every call and
 * neither writes.
 */

export function readAllBills(): Bill[] {
  let bills: Bill[] = []

  // >>> CUT cut-store-read-all
  const filePath = path.join(process.cwd(), 'data', 'bills.json')
  const contents = fs.readFileSync(filePath, 'utf8')
  bills = JSON.parse(contents) as Bill[]
  // <<< CUT cut-store-read-all

  return bills
}

export function findBill(id: string): Bill | null {
  const bills = readAllBills()
  let bill: Bill | null = null

  // >>> CUT cut-store-find-one
  bill = bills.find((candidate) => candidate.id === id) ?? null
  // <<< CUT cut-store-find-one

  return bill
}
