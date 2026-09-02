/**
 * The three types the whole project is written against. Shipped written: no cut
 * lives in this file.
 */

/** One seeded game, exactly as `data/games.json` holds it. */
export type Game = {
  id: string
  name: string
  rolls: number[]
}

/** One frame: 1, 2 or 3 rolls. */
export type Frame = number[]

/** A frame's cumulative score, or `null` when its bonus rolls do not exist yet. */
export type FrameScore = number | null
