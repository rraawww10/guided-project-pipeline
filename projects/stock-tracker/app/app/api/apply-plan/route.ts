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
  // >>> CUT cut-ep-trade-record
  // Read persisted budget, generate the deterministic plan for this request,
  // and record one Trade per item. Assign the inserted count into `created`.
  const recBudgetSetting = await prisma.setting.findUnique({ where: { key: 'budgetCents' } })
  const recBudgetCents = recBudgetSetting ? parseInt(recBudgetSetting.value, 10) || 0 : 0
  const recordPlan = await generatePlan(recBudgetCents)
  if (recordPlan.length > 0) {
    const payload = recordPlan.map((it) => ({
      assetSymbol: it.symbol,
      shares: it.shares,
      priceCents: it.priceCents,
      createdNote: 'apply-plan'
    }))
    const res = await prisma.trade.createMany({ data: payload })
    created = (res as any).count ?? recordPlan.length
  }
  // <<< CUT cut-ep-trade-record

  let body: any = { error: 'Not implemented' }
  let status = 501
  // >>> CUT cut-ep-apply-plan
  // Compute the current plan independently, then apply it to holdings. If the
  // record step above inserted trades, we still report its `created` count in
  // the response so tests can assert `applied > 0`.
  const appBudgetSetting = await prisma.setting.findUnique({ where: { key: 'budgetCents' } })
  const appBudgetCents = appBudgetSetting ? parseInt(appBudgetSetting.value, 10) || 0 : 0
  plan = await generatePlan(appBudgetCents)
  const updatedHoldings = await applyTrades(plan)
  body = { applied: created, updatedHoldings }
  status = 200
  // <<< CUT cut-ep-apply-plan
  return Response.json(body, { status })
}
