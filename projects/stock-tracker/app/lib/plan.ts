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
  // >>> CUT cut-plan-rank
  ranked = [...alloc].sort((a, b) => {
    const ap = a.driftPercent
    const bp = b.driftPercent
    // Positive drifts (overweight) before negatives (underweight)
    if ((ap > 0) !== (bp > 0)) return ap > 0 ? -1 : 1
    // Within the same sign, sort by absolute magnitude desc
    const da = Math.abs(ap)
    const db = Math.abs(bp)
    if (db !== da) return db - da
    return a.symbol.localeCompare(b.symbol)
  })
  // <<< CUT cut-plan-rank

  let plan: PlanItem[] = []
  // >>> CUT cut-plan-allocate
  let remaining = Math.max(0, Math.floor(budgetCents))
  for (const row of ranked) {
    const p = await getPriceCents(row.symbol)
    // Compute desired value change to move towards target
    const driftFraction = (row.driftPercent || 0) / 100 // +ve overweight, -ve underweight
    if (driftFraction > 0) {
      // Overweight -> target value reduction
      const desiredValueChange = driftFraction * totalValue
      // Convert to integer shares to sell (at least 1 if still overweight)
      const sharesToSell = Math.max(1, Math.floor(desiredValueChange / Math.max(1, p)))
      const item: PlanItem = {
        symbol: row.symbol,
        shares: -sharesToSell,
        side: 'SELL',
        priceCents: p,
        costCents: sharesToSell * p
      }
      plan.push(item)
    } else if (driftFraction < 0) {
      // Underweight -> target value increase
      const desiredValueChange = Math.abs(driftFraction) * totalValue
      const maxByDeficit = Math.floor(desiredValueChange / Math.max(1, p))
      const maxByBudget = Math.floor(remaining / Math.max(1, p))
      const sharesToBuy = Math.max(0, Math.min(maxByDeficit, maxByBudget))
      if (sharesToBuy > 0) {
        const item: PlanItem = {
          symbol: row.symbol,
          shares: sharesToBuy,
          side: 'BUY',
          priceCents: p,
          costCents: sharesToBuy * p
        }
        plan.push(item)
        remaining -= item.costCents
      }
    }
  }
  // <<< CUT cut-plan-allocate
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
