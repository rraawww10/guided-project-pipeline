import { gameTotal, scoreGame } from "@/lib/score"

import type { FrameScore } from "@/lib/types"

export const dynamic = "force-dynamic"

/** The one 400 body this endpoint answers with. */
const ERROR_BODY = { error: "rolls must be an array of numbers" }

/**
 * `rolls` out of a parsed body, or `null` when it is absent or is not an array
 * of numbers. Nothing about the game itself is validated: the seed is legal and
 * the POST body is trusted once it is an array of numbers.
 */
function readRolls(body: unknown): number[] | null {
  if (typeof body !== "object" || body === null) return null
  const rolls = (body as { rolls?: unknown }).rolls
  if (!Array.isArray(rolls)) return null
  for (const roll of rolls) {
    if (typeof roll !== "number" || !Number.isFinite(roll)) return null
  }
  return rolls as number[]
}

/**
 * ep-games-score. Scores whatever roll list it is given - it does not read the
 * store. An absent, empty or unparseable body is treated as an absent `rolls`
 * and answered with the same 400, so no input reaches a 500. An empty `rolls`
 * is a legal game, not an error.
 */
export async function POST(request: Request): Promise<Response> {
  let body: unknown = null
  try {
    body = await request.json()
  } catch {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const rolls = readRolls(body)
  if (rolls === null) {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const scores: FrameScore[] = scoreGame(rolls)
  return Response.json({ frames: scores, total: gameTotal(scores) })
}
