import { NextRequest } from 'next/server'
import { prisma } from '../../../lib/prisma'

export async function PUT(req: NextRequest): Promise<Response> {
  let body: any = { ok: false }
  let status = 501
  // >>> CUT cut-ep-targets-update
  const updates: Array<{ symbol: string; weight: number }> = await req.json().catch(() => [])
  for (const u of updates) {
    if (!u || typeof u.symbol !== 'string' || typeof u.weight !== 'number') continue
    await prisma.target.upsert({
      where: { assetSymbol: u.symbol },
      update: { weight: u.weight },
      create: { assetSymbol: u.symbol, weight: u.weight }
    })
  }
  body = { ok: true }
  status = 200
  // <<< CUT cut-ep-targets-update
  return Response.json(body, { status })
}
