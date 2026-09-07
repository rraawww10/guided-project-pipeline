import { NextRequest } from 'next/server'
import { computeAllocation } from '../../../lib/allocation'

// Force dynamic so allocation reflects live DB state
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-allocation-body
  const rows = await computeAllocation()
  body = rows
  status = 200
  // <<< CUT cut-ep-allocation-body
  return Response.json(body, { status })
}
