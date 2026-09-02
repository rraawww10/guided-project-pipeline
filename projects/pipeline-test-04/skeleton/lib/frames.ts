/**
 * The one frame-splitting scan in this project. `lib/score.ts` calls `frames`
 * and walks what it returns; it never chunks a roll list itself.
 *
 * `out` is the accumulator and `i` is the scan index into `rolls`. Both are
 * declared here, both cut blocks below append to `out` and advance `i`, and
 * `return out` sits below both so the file still compiles with either block
 * unwritten.
 */

/** Split a flat roll list into frames. */
export function frames(rolls: number[]): number[][] {
  const out: number[][] = []
  let i = 0
  // TODO(cut-frames-scan): Walk `rolls` from the start and append the first nine frames to `out`, advancing `i` by two rolls per frame unless the first of them is 10, in which case the frame holds that one roll and `i` advances by one. Stop as soon as `rolls` runs out, so a 10-roll game leaves `out` with 6 entries.
  // TODO(cut-frames-tenth): Append one last entry to `out` holding every roll still left in `rolls` from `i` onwards - two rolls for an open tenth frame and three for a tenth that earned bonus rolls - and append nothing at all for a game whose rolls ran out earlier.
  return out
}
