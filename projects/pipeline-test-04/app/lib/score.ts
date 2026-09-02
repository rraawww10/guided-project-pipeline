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
  // >>> CUT cut-pending-frame
  if (frame[0] === 10) {
    pending = rolls.length < i + 3
  } else if (frame[0] + frame[1] === 10) {
    pending = rolls.length < i + 3
  } else {
    pending = rolls.length < i + 2
  }
  // <<< CUT cut-pending-frame
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
    // >>> CUT cut-score-lookahead
    if (rolls[i] === 10) {
      frameScore = 10 + rolls[i + 1] + rolls[i + 2]
    } else if (rolls[i] + rolls[i + 1] === 10) {
      frameScore = 10 + rolls[i + 2]
    } else {
      frameScore = rolls[i] + rolls[i + 1]
    }
    // <<< CUT cut-score-lookahead

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
  // >>> CUT cut-game-total
  total = 0
  for (const score of frameScores) {
    if (score !== null) {
      total = score
    }
  }
  // <<< CUT cut-game-total
  return total
}
