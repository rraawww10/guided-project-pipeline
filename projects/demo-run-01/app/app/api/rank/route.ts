import { NextRequest, NextResponse } from "next/server"
import { allCandidates, PREFERRED_TAG } from "../../../lib/store"
import { RankItem, RankWorking, ToggleToken } from "../../../lib/types"
import { cmp } from "../../../lib/sort"
import { maxYears, toPublic, toWorking } from "../../../lib/score"

function parseActive(req: NextRequest): { ok: true; active: Set<ToggleToken> } | { ok: false; message: string } {
  const url = new URL(req.url)
  const sp = url.searchParams
  // Merge repeated keys by joining with commas in arrival order
  const parts: string[] = sp.getAll("active")
  const merged = parts.join(",")
  const tokens = merged.split(",").map((s) => s.trim()).filter((s) => s.length > 0)
  const out = new Set<ToggleToken>()
  const valid: ToggleToken[] = ["years", "tag"]
  for (const t of tokens) {
    if (!valid.includes(t as ToggleToken)) {
      return { ok: false, message: `unknown token: ${t}` }
    }
    out.add(t as ToggleToken)
  }
  return { ok: true, active: out }
}

export async function GET(req: NextRequest): Promise<Response> {
  let status = 501
  let body: RankItem[] = []

  // parse active tokens
  let activeTokens: Set<ToggleToken> = new Set()
  // >>> CUT cut-api-rank-parse-query
  const parsed = parseActive(req)
  if (!parsed.ok) {
    return NextResponse.json({ error: parsed.message }, { status: 400 })
  }
  activeTokens = parsed.active
  status = 200
  // <<< CUT cut-api-rank-parse-query

  // build full ranking
  // >>> CUT cut-api-rank-build
  const cands = allCandidates()
  const maxY = maxYears(cands)
  let working: RankWorking[] = cands.map((c) => toWorking(c, activeTokens, maxY))
  // In the final app always sort using cmp
  working.sort((a, b) => cmp(a, b, activeTokens))
  body = toPublic(working)
  status = 200
  // <<< CUT cut-api-rank-build

  // optional min filter applies to ROUNDED score
  // >>> CUT cut-api-rank-apply-min
  const url = new URL(req.url)
  const minRaw = url.searchParams.get("min")
  if (minRaw !== null) {
    const threshold = Number(minRaw)
    if (!Number.isNaN(threshold)) {
      body = body.filter((it) => it.score >= threshold)
    }
  }
  // <<< CUT cut-api-rank-apply-min

  return NextResponse.json(body, { status })
}
