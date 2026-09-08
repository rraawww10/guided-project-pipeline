import { prisma } from '@/lib/prisma'
import { filterCandidates, nextCandidate } from '@/lib/candidates'

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  let body: any = { remaining: 0, suggestion: null }
  let status = 200
  const { id } = await ctx.params
  const game = await prisma.game.findUnique({ where: { id }, include: { guesses: { orderBy: { createdAt: 'asc' } } } })
  if (!game) return Response.json({ error: 'not found' }, { status: 404 })
  // TODO(cut-ep-hint-build): Load the game's guesses, compute the remaining candidate set and a deterministic next guess, and place { remaining, suggestion } into `body` with status 200
  return Response.json(body, { status })
}
