/**
 * Scoring. Session 2's three cut points live in this file.
 *
 * There is no frame splitting here: `scoreGame` calls `frames(rolls)` from
 * `lib/frames.ts`, holds the result as `frameList`, and carries a parallel
 * index `i` into `rolls` which it advances by the length of each frame, so `i`
 * is always the index of the current frame's first roll. Every lookahead
 * indexes into `rolls` at `i`.
 *
 * The two jobs are kept apart on purpose. `pendingFrame` is the only place the
 * end of `rolls` is checked; the arithmetic in `scoreGame` applies its rules
 * unconditionally and `scoreGame` pushes `null` for a frame reported pending.
 */
import { frames } from "./frames"

import type { Frame, FrameScore } from "./types"

/**
 * Whether the rolls this frame needs are still missing from `rolls`. `i` is the
 * index of the frame's first roll.
 */
export function pendingFrame(rolls: number[], i: number, frame: Frame): boolean {
  let pending = false
  // TODO(cut-pending-frame): Set `pending` to true while the rolls this frame needs are still missing from `rolls`: a frame that opens with a 10 needs the two entries after it, a frame whose two rolls add to 10 needs the one entry after them, and an open frame needs nothing beyond its own two rolls.
  return pending
}

/** The cumulative score per frame, `null` from the first pending frame onwards. */
export function scoreGame(rolls: number[]): FrameScore[] {
  const frameList: number[][] = frames(rolls)
  const scores: FrameScore[] = []
  let running = 0
  let i = 0

  for (const frame of frameList) {
    const pending = pendingFrame(rolls, i, frame)
    let frameScore: number | null = null
    // TODO(cut-score-lookahead): Set `frameScore` to what this frame is worth: 10 plus the next two entries of `rolls` for a frame that opens with a 10, 10 plus the single entry after the pair for a frame whose two rolls add to 10, and the frame's own two rolls added together for anything else. Index into `rolls` at `i`, never into `frameList`.

    if (pending || frameScore === null) {
      scores.push(null)
    } else {
      running = running + frameScore
      scores.push(running)
    }
    i = i + frame.length
  }

  return scores
}

/** The score of the last frame that has one. */
export function gameTotal(frameScores: FrameScore[]): number {
  let total = -1
  // TODO(cut-game-total): Set `total` to the score of the last frame that has one: the final entry of `frameScores` that is not null, and 0 for a game where not one frame has a score yet.
  return total
}
