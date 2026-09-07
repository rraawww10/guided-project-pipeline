import { prisma } from './prisma'

export type Position = {
  symbol: string
  name: string
  shares: number
  priceCents: number
  targetWeight: number
}

export async function getPositions(): Promise<Position[]> {
  const assets = await prisma.asset.findMany({
    include: { holding: true, price: true, target: true },
    orderBy: { symbol: 'asc' }
  })
  return assets
    .filter((a) => a.holding && a.price && a.target)
    .map((a) => ({
      symbol: a.symbol,
      name: a.name,
      shares: a.holding!.shares,
      priceCents: a.price!.priceCents,
      targetWeight: a.target!.weight
    }))
}
