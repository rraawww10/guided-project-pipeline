import { NextRequest } from 'next/server'
import { computeAllocation } from '../../../lib/allocation'

// Force dynamic so allocation reflects live DB state
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // TODO(cut-ep-allocation-body): Put every allocation row computed from the store into `body` and set `status` to 200
  return Response.json(body, { status })
}
