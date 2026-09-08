import { prisma } from '@/lib/prisma'

export async function POST(req: Request): Promise<Response> {
  let body: any = { ok: false }
  let status = 501
  // >>> CUT cut-ep-games-create-save
  const { seed } = await req.json() as { seed: number }
  const game = await prisma.game.create({ data: { seed } })
  body = { id: game.id, seed: game.seed }
  status = 201
  // <<< CUT cut-ep-games-create-save
  return Response.json(body, { status })
}

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 200
  // >>> CUT cut-ep-games-list
  const games = await prisma.game.findMany({
    include: { _count: { select: { guesses: true } } },
    orderBy: { createdAt: 'asc' },
  })
  body = games.map((g) => ({ id: g.id, seed: g.seed, guessCount: (g as any)._count.guesses as number }))
  status = 200
  // <<< CUT cut-ep-games-list
  return Response.json(body, { status })
}
