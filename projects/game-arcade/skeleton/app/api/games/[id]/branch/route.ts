import { prisma } from '@/lib/prisma'

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  let body: any = { ok: false }
  let status = 201
  const { id } = await ctx.params
  const { upto } = (await req.json()) as { upto: number }
  const src = await prisma.game.findUnique({ where: { id }, include: { guesses: { orderBy: { createdAt: 'asc' } } } })
  if (!src) return Response.json({ error: 'not found' }, { status: 404 })
  // TODO(cut-ep-games-branch): Create a new Game with the same seed as the source, copy the first `upto` guesses into it (including black/white), place the new { id, seed } into `body` and set `status` to 201
  return Response.json(body, { status })
}
