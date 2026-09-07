import { computeAllocation, AllocationRow } from './allocation'

export type PlanItem = {
  symbol: string
  shares: number // positive buy, negative sell
  side: 'BUY' | 'SELL'
  priceCents: number
  costCents: number
}

export async function generatePlan(budgetCents: number): Promise<PlanItem[]> {
  const alloc = await computeAllocation()
  const totalValue = alloc.reduce((s, r) => s + r.valueCents, 0)
  // Rank candidates: all overweight (positive drift) first by drift desc, then underweight by abs(drift) desc; tie-break by symbol ASC
  let ranked: AllocationRow[] = []
  // TODO(cut-plan-rank): Build `ranked` as symbols ordered by absolute drift descending, breaking ties by symbol ascending to be deterministic

  let plan: PlanItem[] = []
  // TODO(cut-plan-allocate): Build `plan` by allocating integer share quantities that reduce drift, not exceeding `budgetCents`, and computing costCents per item from priceCents
  return plan
}

async function getPriceCents(symbol: string): Promise<number> {
  // Avoid importing prisma here; get from allocation recompute
  const alloc = await computeAllocation()
  const row = alloc.find((r) => r.symbol === symbol)
  // valueCents = shares * price; cannot get shares here, so derive from store
  const { getPositions } = await import('./store')
  const pos = (await getPositions()).find((p) => p.symbol === symbol)
  return pos ? pos.priceCents : 0
}

async function computePricePerShare(_row: AllocationRow): Promise<{ denom: number }> {
  // Helper retained so the cut above can refer to a symbol; returns 1 for seed lot size
  return { denom: 1 }
}
