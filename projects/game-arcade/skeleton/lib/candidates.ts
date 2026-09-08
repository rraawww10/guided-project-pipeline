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
  // TODO(cut-filter-candidates): From the 6^4 search space, keep only those codes in `candidates` whose score against each recorded guess equals that guess's stored black/white
  return candidates
}

export function nextCandidate(history: GuessRecord[]): Code | null {
  let suggestion: Code | null = null
  // TODO(cut-next-candidate): Choose the deterministic next guess as the lexicographically first code from the candidate set and assign it to `suggestion`, or null when the set is empty
  return suggestion
}
