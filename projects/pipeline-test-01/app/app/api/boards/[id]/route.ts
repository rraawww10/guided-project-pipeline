import { NextResponse } from 'next/server'

import { neighbourCounts } from '@/lib/board'
import { findBoard } from '@/lib/boards'
import type { BoardView } from '@/lib/boards'

// answered from the seeded constant on every request, never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/boards/[id] -> BoardView, 200; or { error }, 404 when no seeded
 * board carries that id.
 */
export async function GET(
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

  const view: BoardView = {
    ...board,
    counts: neighbourCounts(board.width, board.height, board.mines),
  }

  return NextResponse.json(view, { status: 200 })
}
