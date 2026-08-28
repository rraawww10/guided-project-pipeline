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

  // TODO(cut-reveal-from): Fill `opened` with every index that a single click on `index` opens. A mine cell, or a cell whose entry in `counts` is above 0, opens only itself. A cell whose count is 0 opens itself, every zero-count cell reachable from it through the 8 neighbour offsets, and every cell bordering that region - but a cell whose count is above 0 is added and never walked out of, which is the rule that stops the fill at the numbers. Keep a visited set so the walk ends. Traversal order is free: the code below the markers sorts `opened` ascending and drops duplicates.

  return Array.from(new Set(opened)).sort((a, b) => a - b)
}
