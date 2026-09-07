import { NextRequest } from 'next/server'
import { generatePlan } from '../../../lib/plan'

export async function POST(req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-plan-body
  const json = await req.json().catch(() => ({}))
  const budgetCents = typeof json?.budgetCents === 'number' ? json.budgetCents : 0
  const plan = await generatePlan(budgetCents)
  body = plan
  status = 200
  // <<< CUT cut-ep-plan-body
  return Response.json(body, { status })
}
