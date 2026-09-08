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
  // >>> CUT cut-ep-score-on-submit
  const secret = deriveSecret(game.seed)
  score = scoreGuess(secret, code as any)
  // <<< CUT cut-ep-score-on-submit
  // >>> CUT cut-ep-guesses-create-save
  const guess = await prisma.guess.create({ data: { gameId: id, code: JSON.stringify(code), black: score.black, white: score.white } })
  body = { id: guess.id, gameId: guess.gameId, code: JSON.parse(guess.code as any).map(Number), black: guess.black, white: guess.white }
  status = 201
  // <<< CUT cut-ep-guesses-create-save
  return Response.json(body, { status })
}
