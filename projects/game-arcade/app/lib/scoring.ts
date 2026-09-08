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
  // >>> CUT cut-score-count-black
  for (let i = 0; i < 4; i++) {
    if (secret[i] === guess[i]) black++
  }
  // <<< CUT cut-score-count-black
  // >>> CUT cut-score-count-white
  const cs = new Array(6).fill(0)
  const cg = new Array(6).fill(0)
  for (const v of secret) cs[v]++
  for (const v of guess) cg[v]++
  const overlap = cs.reduce((acc, _v, i) => acc + Math.min(cs[i], cg[i]), 0)
  white = overlap - black
  // <<< CUT cut-score-count-white
  return { black, white }
}
