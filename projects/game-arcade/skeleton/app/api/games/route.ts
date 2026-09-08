import { prisma } from '@/lib/prisma'

export async function POST(req: Request): Promise<Response> {
  let body: any = { ok: false }
  let status = 501
  // TODO(cut-ep-games-create-save): Insert a new Game with the provided numeric `seed`, set `body` to the created { id, seed }, and set `status` to 201
  return Response.json(body, { status })
}

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 200
  // TODO(cut-ep-games-list): Read all games with their guess counts and assign an array of { id, seed, guessCount } to `body` with status 200
  return Response.json(body, { status })
}
