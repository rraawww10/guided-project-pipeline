import { prisma } from '@/lib/prisma'

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  let body: any = { ok: false }
  let status = 200
  const { id } = await ctx.params
  const game = await prisma.game.findUnique({ where: { id }, include: { guesses: { orderBy: { createdAt: 'asc' } } } })
  if (!game) return Response.json({ error: 'not found' }, { status: 404 })
  body = { id: game.id, seed: game.seed, guesses: game.guesses.map((g) => ({
    id: g.id,
    gameId: g.gameId,
    code: JSON.parse(g.code as any).map(Number),
    black: g.black,
    white: g.white,
  })) }
  return Response.json(body, { status })
}
