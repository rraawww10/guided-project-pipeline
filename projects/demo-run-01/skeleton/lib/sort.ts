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
// TODO(cut-sort-cmp): Implement `cmp` so that it compares a and b by unrounded score DESC; when the 'tag' token is active and one candidate has the preferred tag and the other does not, place the tagged candidate first; next break ties by years DESC; finally by name ASC using ASCII codepoint order
