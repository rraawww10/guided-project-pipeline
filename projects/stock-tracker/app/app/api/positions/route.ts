import { NextRequest } from 'next/server'
import { getPositions } from '../../../lib/store'

// Positions change after applying a plan; serve dynamically
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-positions-body
  const positions = await getPositions()
  body = positions.map((p) => ({
    symbol: p.symbol,
    name: p.name,
    shares: p.shares,
    priceCents: p.priceCents,
    targetWeight: p.targetWeight
  }))
  status = 200
  // <<< CUT cut-ep-positions-body
  return Response.json(body, { status })
}
