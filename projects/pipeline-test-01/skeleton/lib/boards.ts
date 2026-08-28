/**
 * The seed data and the shapes every other module speaks in.
 *
 * A board is a flat array of cells addressed by one integer, row-major: the
 * cell at column `x`, row `y` has index `y * width + x`. Every index in every
 * request body, every response body and every `data-index` attribute is that
 * number.
 *
 * Nothing here is random and nothing here is written to disk. The three boards
 * are a `const`, so the same click always opens the same squares.
 */

/** A seeded board. `mines` is sorted ascending and holds no duplicates. */
export type Board = {
  id: string
  name: string
  width: number
  height: number
  mines: number[]
}

/** One entry of the board index at GET /api/boards. */
export type BoardSummary = {
  id: string
  name: string
  width: number
  height: number
  mineCount: number
}

/**
 * One board at GET /api/boards/[id]. `counts` has exactly `width * height`
 * entries and `counts[i]` is how many of the eight cells touching `i` are
 * mines - including when `i` is itself a mine, which is why `counts[63]` on
 * the `field` board is 0 even though index 63 holds a mine.
 */
export type BoardView = {
  id: string
  name: string
  width: number
  height: number
  mines: number[]
  counts: number[]
}

/**
 * The whole catalogue, in seed order: intro, field, corner.
 *
 * - `intro` has two disjoint zero regions, so one click never opens the board.
 * - `field` is the flood fill's headline case: one click on index 0 opens 14
 *   cells under the right boundary rule and 54 under the wrong one.
 * - `corner` clusters its mines, so one click on index 0 opens all 13 safe
 *   cells and wins the game outright.
 */
export const BOARDS: Board[] = [
  { id: 'intro', name: 'Intro', width: 5, height: 5, mines: [9, 11, 18, 23] },
  {
    id: 'field',
    name: 'Field',
    width: 8,
    height: 8,
    mines: [15, 17, 20, 42, 44, 46, 47, 49, 56, 63],
  },
  { id: 'corner', name: 'Corner', width: 4, height: 4, mines: [11, 14, 15] },
]

/** The board with that id, or null on a miss. */
export function findBoard(id: string): Board | null {
  return BOARDS.find((board) => board.id === id) ?? null
}
