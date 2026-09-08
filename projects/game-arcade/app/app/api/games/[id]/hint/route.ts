import { prisma } from '@/lib/prisma'
import { filterCandidates, nextCandidate } from '@/lib/candidates'

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  let body: any = { remaining: 0, suggestion: null }
  let status = 200
  const { id } = await ctx.params
  const game = await prisma.game.findUnique({ where: { id }, include: { guesses: { orderBy: { createdAt: 'asc' } } } })
  if (!game) return Response.json({ error: 'not found' }, { status: 404 })
  // >>> CUT cut-ep-hint-build
  const history = game.guesses.map((g) => ({ code: JSON.parse(g.code as any).map(Number), black: g.black ?? 0, white: g.white ?? 0 }))
  const candidates = filterCandidates(history)
  const suggestion = nextCandidate(history)
  body = { remaining: candidates.length, suggestion }
  status = 200
  // <<< CUT cut-ep-hint-build
  return Response.json(body, { status })
}
