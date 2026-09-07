import { prisma } from './prisma'
import type { PlanItem } from './plan'

export type Holding = { assetSymbol: string; shares: number }

export async function applyTrades(plan: PlanItem[]): Promise<Holding[]> {
  let updatedHoldings: Holding[] = []
  // >>> CUT cut-reconcile-holdings
  // Apply each trade's shares (BUY positive, SELL negative) to holdings
  for (const item of plan) {
    const sym = item.symbol
    const delta = item.shares
    const existing = await prisma.holding.findUnique({ where: { assetSymbol: sym } })
    const nextShares = Math.max(0, (existing?.shares ?? 0) + delta)
    await prisma.holding.upsert({
      where: { assetSymbol: sym },
      update: { shares: nextShares },
      create: { assetSymbol: sym, shares: nextShares }
    })
  }
  const all = await prisma.holding.findMany({ orderBy: { assetSymbol: 'asc' } })
  updatedHoldings = all.map((h) => ({ assetSymbol: h.assetSymbol, shares: h.shares }))
  // <<< CUT cut-reconcile-holdings
  return updatedHoldings
}
