import { NextRequest } from 'next/server'
import { generatePlan } from '../../../lib/plan'

export async function POST(req: NextRequest): Promise<Response> {
  let body: any = { error: 'Not implemented' }
  let status = 501
  // TODO(cut-ep-plan-body): Read `budgetCents` from the request, generate the plan, write it into `body` and set `status` to 200
  return Response.json(body, { status })
}
