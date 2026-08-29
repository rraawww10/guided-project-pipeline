import { NextResponse } from 'next/server'

import { allPuzzles } from '@/lib/puzzles'
import type { Puzzle } from '@/lib/puzzles'

// the clues are derived on every request rather than stored, so this handler is
// never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/puzzles -> Puzzle[], 200. All three puzzles in seed order, each with
 * id, title, size, rowClues and colClues and no other key. The solution is not
 * in the response, which is what stops the board grading itself in the browser.
 */
export async function GET(): Promise<Response> {
  const puzzles: Puzzle[] = allPuzzles()

  return NextResponse.json(puzzles)
}
