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
  // TODO(cut-api-transactions-list): Put every seeded transaction into `body` and set `status` to 200
  return NextResponse.json(body, { status })
}

export async function HEAD() {
  // Mirror GET's allowed status for simple health checks
  return NextResponse.json(null, { status: 200 })
}
