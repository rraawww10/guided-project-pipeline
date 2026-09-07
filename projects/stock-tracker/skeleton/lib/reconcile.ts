import { prisma } from './prisma'
import type { PlanItem } from './plan'

export type Holding = { assetSymbol: string; shares: number }

export async function applyTrades(plan: PlanItem[]): Promise<Holding[]> {
  let updatedHoldings: Holding[] = []
  // TODO(cut-reconcile-holdings): Build `updatedHoldings` by applying each TradeItem's integer shares to the corresponding Holding and persisting the new share counts
  return updatedHoldings
}
