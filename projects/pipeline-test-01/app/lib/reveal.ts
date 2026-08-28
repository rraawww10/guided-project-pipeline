/**
 * The flood fill.
 *
 * One click on a zero opens the whole connected region of zeros plus the
 * numbered cells fringing it. The boundary rule is the whole lesson: a numbered
 * cell is opened but never walked out of. A fill that walks through numbers
 * opens 54 cells on `field` where the right answer is 14.
 */
import { neighbourCounts } from './board'
import type { Board } from './boards'

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
 * Every index that a single click on `index` opens, sorted ascending with
 * duplicates dropped - so no caller can depend on a traversal order.
 */
export function revealFrom(board: Board, index: number): number[] {
  const { width, height, mines } = board
  const counts = neighbourCounts(width, height, mines)

  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles and a click opens nothing
  const opened: number[] = []

  // >>> CUT cut-reveal-from
  const mined = new Set(mines)

  if (mined.has(index) || counts[index] > 0) {
    // a mine, or a numbered cell, opens only itself
    opened.push(index)
  } else {
    // a breadth-first walk with an explicit queue and a visited set
    const visited = new Set<number>([index])
    const queue: number[] = [index]
    let head = 0

    while (head < queue.length) {
      const current = queue[head]
      head += 1
      opened.push(current)

      // the boundary rule: a numbered cell is opened and never walked out of
      if (counts[current] > 0) {
        continue
      }

      const x = current % width
      const y = Math.floor(current / width)

      for (const [dx, dy] of OFFSETS) {
        const nx = x + dx
        const ny = y + dy

        if (nx < 0 || nx >= width || ny < 0 || ny >= height) {
          continue
        }

        const neighbour = ny * width + nx

        if (!visited.has(neighbour)) {
          visited.add(neighbour)
          queue.push(neighbour)
        }
      }
    }
  }
  // <<< CUT cut-reveal-from

  return Array.from(new Set(opened)).sort((a, b) => a - b)
}
