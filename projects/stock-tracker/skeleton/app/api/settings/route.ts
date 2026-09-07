import { NextRequest } from 'next/server'
import { prisma } from '../../../lib/prisma'

export async function PUT(req: NextRequest): Promise<Response> {
  let body: any = { ok: false }
  let status = 501
  // TODO(cut-ep-settings-update): Persist the incoming `budgetCents` setting and set `status` to 200
  return Response.json(body, { status })
}
