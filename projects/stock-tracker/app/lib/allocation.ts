import { getPositions } from './store'

export type AllocationRow = {
  symbol: string
  valueCents: number
  currentWeight: number
  targetWeight: number
  driftPercent: number
}

export async function computeAllocation(): Promise<AllocationRow[]> {
  const positions = await getPositions()
  const total = positions.reduce((sum, p) => sum + p.shares * p.priceCents, 0)
  let weights: AllocationRow[] = []
  // >>> CUT cut-calc-weights
  weights = positions.map((p) => {
    const valueCents = p.shares * p.priceCents
    const currentWeight = total > 0 ? valueCents / total : 0
    const targetWeight = p.targetWeight
    const driftPercent = (currentWeight - targetWeight) * 100
    return { symbol: p.symbol, valueCents, currentWeight, targetWeight, driftPercent }
  })
  // <<< CUT cut-calc-weights
  return weights
}
