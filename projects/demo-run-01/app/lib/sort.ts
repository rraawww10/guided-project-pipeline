import { RankWorking, ToggleToken } from "./types"

export type Cmp = (a: RankWorking, b: RankWorking, active: Set<ToggleToken>) => number

// The placeholder sits OUTSIDE the markers on purpose. Every `return` in the
// comparator is inside them, and cutting a function's only return leaves a
// `=> number` that returns nothing, which does not compile - CLAUDE.md names
// this as the one thing never to do with a cut pair. Putting the whole function
// expression inside instead means the cut takes the signature and the returns
// away together, so the skeleton still builds and the student is left with a
// comparator that calls everything equal until they write the real one.
export let cmp: Cmp = () => 0
// >>> CUT cut-sort-cmp
cmp = (a, b, active) => {
  // primary: unrounded score DESC
  if (a.unrounded !== b.unrounded) {
    return a.unrounded > b.unrounded ? -1 : 1
  }
  // tie-break 1: when 'tag' is active, prefer hasPreferredTag over not
  if (active.has("tag") && a.hasPreferredTag !== b.hasPreferredTag) {
    return a.hasPreferredTag ? -1 : 1
  }
  // Special case: with no active tokens, overall order is by name ASC
  if (active.size === 0) {
    if (a.name < b.name) return -1
    if (a.name > b.name) return 1
    return 0
  }
  // tie-break 2: years DESC
  if (a.years !== b.years) {
    return a.years > b.years ? -1 : 1
  }
  // tie-break 3: name ASC (ASCII codepoint order)
  if (a.name < b.name) return -1
  if (a.name > b.name) return 1
  return 0
}
// <<< CUT cut-sort-cmp
