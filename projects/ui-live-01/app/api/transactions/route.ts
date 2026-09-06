import { NextResponse } from "next/server"
import { promises as fs } from "fs"
import path from "path"
import type { Tx } from "../../lib/types"

// Ensure Node.js runtime for fs access
export const runtime = "nodejs"
export const dynamic = "force-dynamic"

export async function GET() {
  let body: Tx[] = []
  let status = 500
  // >>> CUT cut-api-transactions-list
  try {
    const file = path.join(process.cwd(), "data", "transactions.seed.json")
    const raw = await fs.readFile(file, "utf-8")
    const parsed: Tx[] = JSON.parse(raw)
    body = parsed
    status = 200
  } catch (err) {
    body = []
    status = 500
  }
  // <<< CUT cut-api-transactions-list
  return NextResponse.json(body, { status })
}

export async function HEAD() {
  // Mirror GET's allowed status for simple health checks
  return NextResponse.json(null, { status: 200 })
}
