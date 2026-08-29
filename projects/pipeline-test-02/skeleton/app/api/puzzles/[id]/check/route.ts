import { NextResponse } from 'next/server'

import { boardSolved, lineStatus, transpose } from '@/lib/nonogram'
import type { Cell, CheckResult } from '@/lib/nonogram'
import { puzzleFor } from '@/lib/puzzles'
import type { Puzzle } from '@/lib/puzzles'

// the grid arrives on the request and the clues are re-derived per call, so
// this handler is never prerendered
export const dynamic = 'force-dynamic'

const CELL_STATES: Cell[] = ['empty', 'filled', 'crossed']

/**
 * The posted grid, or a message saying why it is not a grid for this puzzle.
 * A grid is exactly `size` rows of exactly `size` cells, and every cell is one
 * of the three strings.
 */
function readGrid(payload: unknown, size: number): Cell[][] | string {
  if (payload === null || typeof payload !== 'object') {
    return 'the request body must be a JSON object carrying a grid'
  }

  const grid = (payload as { grid?: unknown }).grid

  if (!Array.isArray(grid) || grid.length !== size) {
    return `grid must be an array of ${size} rows`
  }

  for (const row of grid) {
    if (!Array.isArray(row) || row.length !== size) {
      return `every row of grid must hold ${size} cells`
    }

    for (const cell of row) {
      if (typeof cell !== 'string' || !CELL_STATES.includes(cell as Cell)) {
        return 'every cell must be empty, filled or crossed'
      }
    }
  }

  return grid as Cell[][]
}

/**
 * POST /api/puzzles/[id]/check, body { grid } -> CheckResult, 200; or { error }
 * with 404 when no puzzle has that id, or 400 when the body is not a grid of the
 * puzzle's size. The id is resolved first, so an unknown id answers 404 whatever
 * the body holds.
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params
  const puzzle: Puzzle | null = puzzleFor(id)

  if (puzzle === null) {
    return NextResponse.json({ error: `no puzzle with the id ${id}` }, { status: 404 })
  }

  const payload = await request.json().catch(() => null)
  const grid = readGrid(payload, puzzle.size)

  if (!Array.isArray(grid)) {
    return NextResponse.json({ error: grid }, { status: 400 })
  }

  const result: CheckResult = {
    rows: grid.map((row, r) => lineStatus(row, puzzle.rowClues[r] ?? [])),
    cols: transpose(grid).map((col, c) => lineStatus(col, puzzle.colClues[c] ?? [])),
    solved: boardSolved(grid, puzzle.rowClues, puzzle.colClues),
  }

  return NextResponse.json(result)
}
