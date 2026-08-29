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

  // TODO(cut-runs-of): Fill `runs` with the length of each block of consecutive `filled` cells in `cells`, in the order the blocks appear, counting a block that ends at the last cell. A `crossed` cell and an `empty` cell both break a block. When `cells` holds no `filled` cell at all, `runs` must be the one-entry list `[0]`, which is the clue an empty line carries.

  return runs
}

/**
 * The columns of `grid`, as rows. `grid` is left as it was, so the caller can
 * read both axes off the same board.
 */
export function transpose<T>(grid: T[][]): T[][] {
  let out: T[][] = []

  // TODO(cut-transpose): Set `out` so that `out[c][r]` holds `grid[r][c]`: one entry per column of `grid`, each as long as `grid` has rows. Every row of `grid` has the same length, and `grid` itself is left unchanged.

  return out
}

/**
 * How one line stands against one clue. The rule never looks at the solution,
 * so a line can read `open` while being inconsistent with the only picture that
 * fits - it only reports what this line, on its own, has already ruled out.
 */
export function lineStatus(cells: Cell[], clue: number[]): LineStatus {
  let status: LineStatus = 'open'

  // TODO(cut-line-status): Set `status` to `satisfied` when `runsOf(cells)` holds the same numbers in the same order as `clue`. Otherwise set it to `violated` when any one of these three holds: `cells` has more blocks of consecutive `filled` cells than `clue` has numbers, or one of those blocks is longer than the largest number in `clue`, or no cell in `cells` is still `empty` while `runsOf(cells)` and `clue` differ. A `crossed` cell is not `empty`, so it does not hold that third condition off. A `[0]` clue, and a clue carrying no numbers at all, each count as no blocks and a largest of 0. In every other case leave `status` at `open`.

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

  // TODO(cut-board-solved): Set `solved` to true only when `lineStatus` answers `satisfied` for every row of `grid` against the matching entry of `rowClues` and for every column of `grid` against the matching entry of `colClues`. Reach the columns through `transpose`, and leave `solved` false when even one line on either axis is not satisfied - a grid whose every row is satisfied is still not solved while any column is not.

  return solved
}
