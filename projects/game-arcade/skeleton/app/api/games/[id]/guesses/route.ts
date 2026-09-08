import { prisma } from '@/lib/prisma'
import { deriveSecret, scoreGuess } from '@/lib/scoring'

export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  let status = 201
  let body: any = { ok: false }
  let score: { black: number; white: number } = { black: 0, white: 0 }
  // Robustly extract the id: prefer the URL path segment, fall back to ctx.params
  let id = ''
  try {
    const url = new URL(req.url)
    const parts = url.pathname.split('/').filter(Boolean)
    const i = parts.findIndex((p) => p === 'games')
    if (i >= 0 && parts[i + 1]) id = parts[i + 1]
  } catch {
    // ignore, fall back to ctx
  }
  if (!id) {
    try {
      const p = await ctx.params
      id = p?.id || ''
    } catch {
      id = ''
    }
  }

  const { code } = (await req.json()) as { code: number[] }
  const game = await prisma.game.findUnique({ where: { id } })
  if (!game) return Response.json({ error: 'not found' }, { status: 404 })
  // TODO(cut-ep-score-on-submit): After loading the Game's secret from its seed, compute the guess's black/white using the scoring function, assign the result to `score`, and include those numbers when saving and in the response
  // TODO(cut-ep-guesses-create-save): Persist a Guess row for the game id from the path using the request's 4-number `code`, leaving its black/white null, then place the saved guess into `body` and set `status` to 201
  return Response.json(body, { status })
}
