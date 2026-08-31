import { readFileSync } from "node:fs"
import path from "node:path"

import { parseLedger, type Ledger } from "@/lib/ledger"

export const dynamic = "force-dynamic"

/**
 * ep-ledger. A pure read of a file that ships with the project: entries in
 * ascending lineNo order, diagnostics in ascending lineNo order, always 200.
 */
export async function GET(): Promise<Response> {
  const text = readFileSync(path.join(process.cwd(), "data", "ledger.txt"), "utf8")
  const ledger: Ledger = parseLedger(text)
  return Response.json(ledger)
}
