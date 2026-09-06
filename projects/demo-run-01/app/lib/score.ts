import { Candidate, RankItem, RankWorking, ToggleToken } from "./types"
import { PREFERRED_TAG } from "./store"

export interface ScoreResult {
  unrounded: number
  rounded: number
  reasons: string[]
  hasPreferredTag: boolean
}

export function hasPreferredTag(tags: string[]): boolean {
  return tags.includes(PREFERRED_TAG)
}

export function maxYears(cands: Candidate[]): number {
  return cands.reduce((m, c) => (c.years > m ? c.years : m), 0)
}

export function scoreApplicant(
  c: Candidate,
  active: Set<ToggleToken>,
  maxY: number
): ScoreResult {
  let out: ScoreResult = { unrounded: 0, rounded: 0, reasons: [], hasPreferredTag: false }
  const wantYears = active.has("years")
  const wantTag = active.has("tag")

  const pref = hasPreferredTag(c.tags)
  // >>> CUT cut-score-apply
  let unrounded = 0
  const reasons: string[] = []
  if (wantYears) {
    const base = maxY > 0 ? c.years / maxY : 0
    unrounded += base
    reasons.push(`years +${base.toFixed(2)}`)
  }
  if (wantTag) {
    if (pref) {
      unrounded += 1.0
      reasons.push("preferred tag +1")
    } else {
      reasons.push("preferred tag +0")
    }
  }
  const rounded = Math.round(unrounded * 100) / 100
  out = { unrounded, rounded, reasons, hasPreferredTag: pref }
  // <<< CUT cut-score-apply
  return out
}

export function toWorking(
  c: Candidate,
  active: Set<ToggleToken>,
  maxY: number
): RankWorking {
  const r = scoreApplicant(c, active, maxY)
  const item: RankWorking = {
    id: c.id,
    name: c.name,
    years: c.years,
    hasPreferredTag: r.hasPreferredTag,
    score: r.rounded,
    reasons: r.reasons,
    unrounded: r.unrounded
  }
  return item
}

export function toPublic(items: RankWorking[]): RankItem[] {
  return items.map(({ id, name, score, reasons }) => ({ id, name, score, reasons }))
}
