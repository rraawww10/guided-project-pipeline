import { NextRequest } from 'next/server'
import { prisma } from '../../../lib/prisma'
import { generatePlan, type PlanItem } from '../../../lib/plan'
import { applyTrades } from '../../../lib/reconcile'

export async function POST(_req: NextRequest): Promise<Response> {
  let created = 0
  // `plan` is declared out here on purpose: cut-ep-apply-plan below assigns it,
  // and a cut must not hold a declaration that code outside it depends on.
  // With it inside, removing that cut would leave `plan` undeclared and the
  // mutant would not compile. Declared here with a safe default it always parses.
  let plan: PlanItem[] = []
  // TODO(cut-ep-trade-record): Insert one Trade per plan item and set `created` to the number inserted

  let body: any = { error: 'Not implemented' }
  let status = 501
  // TODO(cut-ep-apply-plan): Compute the current plan, apply it, write `{ applied, updatedHoldings }` into `body` and set `status` to 200
  return Response.json(body, { status })
}
