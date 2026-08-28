/**
 * The eight-way neighbour scan.
 *
 * A grid treated as a graph: each cell has up to eight neighbours, and the
 * count at a cell is how many of them hold a mine. The interesting part is the
 * bounds test - a corner cell weighs 3 neighbours and an edge cell 5, and a
 * missing test wraps a row or reads off the end of the array.
 */

/** The eight neighbour offsets as [dx, dy], clockwise from the top left. */
const OFFSETS: ReadonlyArray<readonly [number, number]> = [
  [-1, -1],
  [0, -1],
  [1, -1],
  [-1, 0],
  [1, 0],
  [-1, 1],
  [0, 1],
  [1, 1],
]

/**
 * One number per cell of a `width` x `height` grid, in index order, where the
 * number at `y * width + x` is how many of that cell's eight neighbours appear
 * in `mines`. A cell that is itself a mine still gets its own neighbour count.
 */
export function neighbourCounts(
  width: number,
  height: number,
  mines: number[],
): number[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles and every criterion that reads a count is red
  const counts: number[] = []

  // TODO(cut-neighbour-counts): Fill `counts` with one number per cell of the board, in index order, where the number at index `y * width + x` is how many of that cell's 8 neighbours appear in `mines`. A cell that is itself a mine still gets its own neighbour count. Skip any neighbour that falls off the edge, so a corner cell weighs 3 neighbours and an edge cell 5, and `counts` ends up exactly `width * height` long.

  return counts
}
