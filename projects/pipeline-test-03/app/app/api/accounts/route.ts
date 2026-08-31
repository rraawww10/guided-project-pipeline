import { readFileSync } from "node:fs"
import path from "node:path"

import { accountTotals, type AccountTotal } from "@/lib/accounts"
import { parseLedger } from "@/lib/ledger"

export const dynamic = "force-dynamic"

/**
 * ep-accounts. One object per distinct account named by an accepted entry,
 * sorted by account ascending, always 200.
 */
export async function GET(): Promise<Response> {
  const text = readFileSync(path.join(process.cwd(), "data", "ledger.txt"), "utf8")
  const totals: AccountTotal[] = accountTotals(parseLedger(text).entries)
  return Response.json(totals)
}
