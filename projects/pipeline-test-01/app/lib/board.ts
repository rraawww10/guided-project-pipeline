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

  // >>> CUT cut-neighbour-counts
  const mined = new Set(mines)

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let touching = 0

      for (const [dx, dy] of OFFSETS) {
        const nx = x + dx
        const ny = y + dy

        // a neighbour off any edge is not a neighbour
        if (nx < 0 || nx >= width || ny < 0 || ny >= height) {
          continue
        }

        if (mined.has(ny * width + nx)) {
          touching += 1
        }
      }

      counts[y * width + x] = touching
    }
  }
  // <<< CUT cut-neighbour-counts

  return counts
}
