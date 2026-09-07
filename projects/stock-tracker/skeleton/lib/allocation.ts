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
  // TODO(cut-calc-weights): Build `weights` as an array of {symbol, valueCents, currentWeight, targetWeight, driftPercent} by dividing each position's value by the portfolio total and subtracting the target weight
  return weights
}
