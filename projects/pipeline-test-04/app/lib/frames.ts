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
  // >>> CUT cut-frames-scan
  while (out.length < 9 && i < rolls.length) {
    if (rolls[i] === 10) {
      out.push([rolls[i]])
      i = i + 1
    } else {
      out.push([rolls[i], rolls[i + 1]])
      i = i + 2
    }
  }
  // <<< CUT cut-frames-scan
  // >>> CUT cut-frames-tenth
  if (i < rolls.length) {
    out.push(rolls.slice(i))
  }
  // <<< CUT cut-frames-tenth
  return out
}
