import { NextResponse } from 'next/server'

import { findBoard } from '@/lib/boards'
import { revealFrom } from '@/lib/reveal'
import { gameStatus } from '@/lib/status'
import type { GameStatus } from '@/lib/status'

// folds a request body on every call, never prerendered
export const dynamic = 'force-dynamic'

type ReplayResponse = {
  revealed: number[]
  flagged: number[]
  status: GameStatus
}

/** An array of integers, every one of them a cell of this board. */
function isIndexList(value: unknown, cellCount: number): value is number[] {
  return (
    Array.isArray(value) &&
    value.every(
      (entry) =>
        typeof entry === 'number' &&
        Number.isInteger(entry) &&
        entry >= 0 &&
        entry < cellCount,
    )
  )
}

/** Ascending, with duplicates dropped. */
function sortedUnique(values: number[]): number[] {
  return Array.from(new Set(values)).sort((a, b) => a - b)
}

/**
 * POST /api/boards/[id]/replay -> { revealed, flagged, status }, 200; or
 * { error } at 400 or 404.
 *
 * The board id is resolved before the body is read, so an unknown board
 * answers 404 even when the body is malformed.
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params
  const board = findBoard(id)

  if (board === null) {
    return NextResponse.json(
      { error: `no board with the id ${id}` },
      { status: 404 },
    )
  }

  let parsed: unknown = null

  try {
    parsed = await request.json()
  } catch {
    return NextResponse.json(
      { error: 'the request body is not JSON' },
      { status: 400 },
    )
  }

  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    return NextResponse.json(
      { error: 'the request body must be a JSON object' },
      { status: 400 },
    )
  }

  const cellCount = board.width * board.height
  const body = parsed as { clicks?: unknown; flags?: unknown }

  if (!isIndexList(body.clicks, cellCount)) {
    return NextResponse.json(
      {
        error: `clicks must be an array of integers from 0 to ${cellCount - 1}`,
      },
      { status: 400 },
    )
  }

  const submittedFlags: unknown = body.flags === undefined ? [] : body.flags

  if (!isIndexList(submittedFlags, cellCount)) {
    return NextResponse.json(
      {
        error: `flags must be an array of integers from 0 to ${cellCount - 1}`,
      },
      { status: 400 },
    )
  }

  // fold the clicks left to right, taking the union at each step
  let revealed: number[] = []

  for (const click of body.clicks) {
    revealed = sortedUnique([...revealed, ...revealFrom(board, click)])
  }

  const payload: ReplayResponse = {
    revealed,
    flagged: sortedUnique(submittedFlags),
    status: gameStatus(board, revealed),
  }

  return NextResponse.json(payload, { status: 200 })
}
