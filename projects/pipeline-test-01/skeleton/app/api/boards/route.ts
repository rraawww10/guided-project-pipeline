import { NextResponse } from 'next/server'

import { BOARDS } from '@/lib/boards'
import type { BoardSummary } from '@/lib/boards'

// answered from the seeded constant on every request, never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/boards -> BoardSummary[], 200. One entry per seeded board, in the
 * seed order intro, field, corner.
 */
export async function GET(): Promise<Response> {
  const summaries: BoardSummary[] = BOARDS.map((board) => ({
    id: board.id,
    name: board.name,
    width: board.width,
    height: board.height,
    mineCount: board.mines.length,
  }))

  return NextResponse.json(summaries, { status: 200 })
}
