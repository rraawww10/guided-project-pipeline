export type Code = [number, number, number, number]
export type Score = { black: number; white: number }

export function xorshift32Stream(seed: number): Generator<number, never, unknown> {
  let x = seed >>> 0
  return (function* () {
    while (true) {
      x ^= (x << 13) >>> 0
      x ^= x >>> 17
      x ^= (x << 5) >>> 0
      x >>>= 0
      yield x
    }
  })()
}

export function deriveSecret(seed: number): Code {
  const g = xorshift32Stream(seed)
  const out: number[] = []
  for (let i = 0; i < 4; i++) out.push((g.next().value as number) % 6)
  return out as Code
}

export function scoreGuess(secret: Code, guess: Code): Score {
  let black = 0
  let white = 0
  // TODO(cut-score-count-black): Count exact matches into `black` by comparing secret and guess at the same index for all 4 slots
  // TODO(cut-score-count-white): Count colour-only matches into `white` without double counting: for each colour 0..5, add the minimum of its frequency in secret and in guess, then subtract `black`
  return { black, white }
}
