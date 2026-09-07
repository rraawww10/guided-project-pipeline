import { NextRequest } from 'next/server'
import { prisma } from '../../../lib/prisma'

// Force dynamic so the list reflects newly created trades
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // TODO(cut-ep-trades-list-body): Put every recorded Trade into `body` and set `status` to 200
  return Response.json(body, { status })
}
