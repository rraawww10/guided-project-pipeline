import { NextRequest } from 'next/server'
import { prisma } from '../../../lib/prisma'

export async function PUT(req: NextRequest): Promise<Response> {
  let body: any = { ok: false }
  let status = 501
  // >>> CUT cut-ep-settings-update
  const json = await req.json().catch(() => ({}))
  const budgetCents = typeof json?.budgetCents === 'number' ? json.budgetCents : undefined
  if (typeof budgetCents === 'number') {
    await prisma.setting.upsert({
      where: { key: 'budgetCents' },
      update: { value: String(Math.floor(budgetCents)) },
      create: { key: 'budgetCents', value: String(Math.floor(budgetCents)) }
    })
  }
  body = { ok: true }
  status = 200
  // <<< CUT cut-ep-settings-update
  return Response.json(body, { status })
}
