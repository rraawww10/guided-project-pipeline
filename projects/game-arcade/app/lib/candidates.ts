import type { Code } from './scoring'
import { scoreGuess } from './scoring'

export type GuessRecord = { code: number[]; black: number; white: number }

export function allCodes(): Code[] {
  const out: Code[] = []
  for (let a = 0; a < 6; a++)
    for (let b = 0; b < 6; b++)
      for (let c = 0; c < 6; c++)
        for (let d = 0; d < 6; d++) out.push([a, b, c, d])
  return out
}

export function filterCandidates(history: GuessRecord[]): Code[] {
  let candidates: Code[] = []
  // >>> CUT cut-filter-candidates
  const space = allCodes()
  candidates = space.filter((code) =>
    history.every((g) => {
      const s = scoreGuess(code as any, g.code as any)
      return s.black === g.black && s.white === g.white
    })
  )
  // <<< CUT cut-filter-candidates
  return candidates
}

export function nextCandidate(history: GuessRecord[]): Code | null {
  let suggestion: Code | null = null
  // >>> CUT cut-next-candidate
  const cands = filterCandidates(history)
  // Lexicographic first
  cands.sort((a, b) => {
    for (let i = 0; i < 4; i++) if (a[i] !== b[i]) return a[i] - b[i]
    return 0
  })
  suggestion = cands[0] ?? null
  // <<< CUT cut-next-candidate
  return suggestion
}
