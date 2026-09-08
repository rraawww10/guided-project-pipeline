import { prisma } from '@/lib/prisma'

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  let body: any = { ok: false }
  let status = 201
  const { id } = await ctx.params
  const { upto } = (await req.json()) as { upto: number }
  const src = await prisma.game.findUnique({ where: { id }, include: { guesses: { orderBy: { createdAt: 'asc' } } } })
  if (!src) return Response.json({ error: 'not found' }, { status: 404 })
  // >>> CUT cut-ep-games-branch
  const branched = await prisma.game.create({ data: { seed: src.seed } })
  const toCopy = src.guesses.slice(0, upto)
  for (const g of toCopy) {
    await prisma.guess.create({ data: { gameId: branched.id, code: g.code as any, black: g.black ?? null, white: g.white ?? null } })
  }
  body = { id: branched.id, seed: branched.seed }
  status = 201
  // <<< CUT cut-ep-games-branch
  return Response.json(body, { status })
}
