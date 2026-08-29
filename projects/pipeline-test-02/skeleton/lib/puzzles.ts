/**
 * The three seeded puzzles.
 *
 * A puzzle is seeded as its solution and nothing else - one string per row, `#`
 * for a filled cell and `.` for a blank one. No clue is written down anywhere in
 * this file: both strips are derived from the solution by `runsOf`, applied to
 * the rows and then to the output of `transpose`. A seed therefore cannot
 * disagree with itself, and the solution never leaves the server.
 */
import type { Cell } from './nonogram'
import { runsOf, transpose } from './nonogram'

export type Puzzle = {
  id: string
  title: string
  size: number
  rowClues: number[][]
  colClues: number[][]
}

type Seed = {
  id: string
  title: string
  rows: string[]
}

const SEEDS: Seed[] = [
  {
    id: 'boat',
    title: 'Boat',
    rows: [
      '..#..',
      '.###.',
      '#####',
      '.#.#.',
      '.#.#.',
    ],
  },
  {
    id: 'blanks',
    title: 'Blanks',
    rows: [
      '.....',
      '#####',
      '#...#',
      '.###.',
      '#.#.#',
    ],
  },
  {
    id: 'house',
    title: 'House',
    rows: [
      '...##...',
      '..####..',
      '.######.',
      '########',
      '.#....#.',
      '.#.##.#.',
      '.#.##.#.',
      '.#....#.',
    ],
  },
]

/** The seeded solution strings for an id, or null when there is no such puzzle. */
export function solutionRows(id: string): string[] | null {
  const seed = SEEDS.find((entry) => entry.id === id)

  return seed === undefined ? null : seed.rows
}

/** One seeded row as cells: `#` is filled, every other character is empty. */
export function rowCells(row: string): Cell[] {
  return [...row].map((character) => (character === '#' ? 'filled' : 'empty'))
}

/**
 * The puzzle an id names, with both clue strips derived from its solution.
 * `size` is the length of a seeded row, so a board still has its true size
 * while the derivation is being written.
 */
export function puzzleFor(id: string): Puzzle | null {
  const seed = SEEDS.find((entry) => entry.id === id)

  if (seed === undefined) {
    return null
  }

  const rows = seed.rows
  const cells = rows.map(rowCells)

  return {
    id: seed.id,
    title: seed.title,
    size: rows.length === 0 ? 0 : rows[0].length,
    rowClues: cells.map(runsOf),
    colClues: transpose(cells).map(runsOf),
  }
}

/** All three puzzles, in seed order: boat, blanks, house. */
export function allPuzzles(): Puzzle[] {
  return SEEDS.map((seed) => puzzleFor(seed.id)).filter(
    (puzzle): puzzle is Puzzle => puzzle !== null,
  )
}
