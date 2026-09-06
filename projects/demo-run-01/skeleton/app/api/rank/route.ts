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
  // TODO(cut-api-rank-parse-query): Parse the 'active' query by splitting on commas after merging repeated keys, drop empty tokens, validate each token against {years, tag}, and write the valid set into `activeTokens`; answer 400 for any unknown

  // build full ranking
  // TODO(cut-api-rank-build): Map every Candidate to a RankItem using the pure scorer, set each RankItem.score as a number already rounded to two decimals, and fill `body` with all RankItem rows; in Session 2 you may sort by unrounded score in descending order, and in the final app always sort using `cmp` from lib/sort.ts; set `status` to 200 when successful

  // optional min filter applies to ROUNDED score
  // TODO(cut-api-rank-apply-min): If the 'min' query parameter is present, remove from `body` any RankItem whose ROUNDED two‑decimal score is strictly less than that threshold before responding

  return NextResponse.json(body, { status })
}
