import { NextRequest } from 'next/server'
import { prisma } from '../../../lib/prisma'

// Force dynamic so the list reflects newly created trades
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-trades-list-body
  const trades = await prisma.trade.findMany({ orderBy: { id: 'asc' } })
  body = trades.map((t) => ({ id: t.id, symbol: t.assetSymbol, shares: t.shares, priceCents: t.priceCents }))
  status = 200
  // <<< CUT cut-ep-trades-list-body
  return Response.json(body, { status })
}
