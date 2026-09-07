import { NextRequest } from 'next/server'
import { getPositions } from '../../../lib/store'

// Positions change after applying a plan; serve dynamically
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // TODO(cut-ep-positions-body): Put every position with symbol, name, shares, priceCents and targetWeight into `body` and set `status` to 200
  return Response.json(body, { status })
}
