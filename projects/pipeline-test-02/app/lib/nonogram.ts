/**
 * The nonogram rules, as pure functions over cells and clues.
 *
 * One function reads a line - `runsOf` - and the whole project is built out of
 * reading every row with it and then every column of `transpose(grid)` with the
 * same function. Nothing here reads a puzzle, a request or the clock.
 */

export type Cell = 'empty' | 'filled' | 'crossed'

export type LineStatus = 'satisfied' | 'open' | 'violated'

export type CheckResult = {
  rows: LineStatus[]
  cols: LineStatus[]
  solved: boolean
}

/**
 * The run-length clue a line of cells carries: the length of each block of
 * consecutive `filled` cells, in order. A line holding no `filled` cell at all
 * carries the one-entry clue `[0]`.
 */
export function runsOf(cells: Cell[]): number[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let runs: number[] = []

  // >>> CUT cut-runs-of
  let block = 0

  for (const cell of cells) {
    if (cell === 'filled') {
      block += 1
    } else if (block > 0) {
      runs.push(block)
      block = 0
    }
  }

  if (block > 0) {
    runs.push(block)
  }

  if (runs.length === 0) {
    runs = [0]
  }
  // <<< CUT cut-runs-of

  return runs
}

/**
 * The columns of `grid`, as rows. `grid` is left as it was, so the caller can
 * read both axes off the same board.
 */
export function transpose<T>(grid: T[][]): T[][] {
  let out: T[][] = []

  // >>> CUT cut-transpose
  const width = grid.length === 0 ? 0 : grid[0].length

  for (let c = 0; c < width; c += 1) {
    const column: T[] = []

    for (let r = 0; r < grid.length; r += 1) {
      column.push(grid[r][c])
    }

    out.push(column)
  }
  // <<< CUT cut-transpose

  return out
}

/**
 * How one line stands against one clue. The rule never looks at the solution,
 * so a line can read `open` while being inconsistent with the only picture that
 * fits - it only reports what this line, on its own, has already ruled out.
 */
export function lineStatus(cells: Cell[], clue: number[]): LineStatus {
  let status: LineStatus = 'open'

  // >>> CUT cut-line-status
  const runs = runsOf(cells)
  // `[0]` and `[]` both mean no blocks and a largest of 0, on either side
  const blocks = runs.filter((n) => n > 0)
  const wanted = clue.filter((n) => n > 0)
  const largest = wanted.length === 0 ? 0 : Math.max(...wanted)

  const matches =
    runs.length === clue.length && runs.every((n, i) => n === clue[i])

  if (matches) {
    status = 'satisfied'
  } else if (
    blocks.length > wanted.length ||
    blocks.some((n) => n > largest) ||
    cells.every((cell) => cell !== 'empty')
  ) {
    status = 'violated'
  }
  // <<< CUT cut-line-status

  return status
}

/**
 * Whether the whole board is done: every row satisfied against its clue and
 * every column satisfied against its own. Computed from the grid rather than
 * from a pair of status lists, so it is graded on its own.
 */
export function boardSolved(
  grid: Cell[][],
  rowClues: number[][],
  colClues: number[][],
): boolean {
  let solved = false

  // >>> CUT cut-board-solved
  const rowsDone = grid.every(
    (row, r) => lineStatus(row, rowClues[r] ?? []) === 'satisfied',
  )
  const colsDone = transpose(grid).every(
    (col, c) => lineStatus(col, colClues[c] ?? []) === 'satisfied',
  )

  solved = rowsDone && colsDone
  // <<< CUT cut-board-solved

  return solved
}
