# Bracket

**One line:** An eight-entrant knockout tournament stored as a flat array, where
recording a result promotes the winner up the tree - and changing an early result
wipes every round that depended on it.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A knockout bracket is a binary tree pretending to be a list: match 0 is the
final, and match `i`'s feeders are `2i+1` and `2i+2`. That encoding is worth
meeting once, because it makes parent-and-child arithmetic instead of pointers.
The real lesson is in session 2 - a result is not just written, it *invalidates*
the results downstream of it. Fixing a quarter-final that was entered wrong has
to erase the semi and the final, and a student who forgets that ships a bracket
where a knocked-out entrant is still the champion.

## Sessions

1. **Setup, the tree, and the rounds view.** Types, `seed.json` with one bracket
   of 8 entrants and 7 matches (4 played, 3 not), `roundsOf(matches)` grouping
   the flat array into columns by depth, `slotLabel(match, side)` reading either
   an entrant name or `Winner of M5` when the feeding match is unplayed, and
   `GET /api/brackets/[id]` plus `/brackets/[id]` rendering three columns.
   **Runs:** a bracket on screen with real names on the left and placeholders on
   the right.
2. **Promotion and invalidation.** `winnerOf(match)`, `promote(matches, id)`
   writing the winner into the parent's correct side, and
   `clearDownstream(matches, id)` erasing every already-recorded result that
   descends from the changed match. `POST /api/brackets/[id]/matches/[m]` takes
   two scores, rejects a draw with 400 and an unknown match with 404, records,
   promotes, invalidates, and returns the whole bracket. **Runs:** record the
   last quarter-final and a name appears in the semi; change it and the semi and
   the final go blank again.

## What the student types

- `roundsOf` - the index arithmetic that turns 7 flat matches into 4 / 2 / 1.
- `promote` - which side of the parent a winner lands on, which is `(id - 1) % 2`
  and is exactly the sort of thing that looks right on the first match tried.
- `clearDownstream` - the walk from a match toward the final, clearing as it
  goes, and stopping at the first already-empty result.

## What this teaches that the shipped projects do not

pipeline-test-01 traverses a grid; this traverses a tree by index, in both
directions, which is a different mental model with no neighbours and no visited
set. Nothing shipped has cascade invalidation - a write whose main job is to
*unwrite* things elsewhere - and that is the idea's whole reason to exist. It is
also the first project with a derived placeholder ("Winner of M5"), which forces
the unstated-empty-case question into session 1.

## Out of scope

- Creating brackets, seeding entrants, byes, or any size other than 8.
- Double elimination, group stages, third-place playoffs, tie-breaks.
- Scores that mean anything beyond deciding a winner. No aggregate, no goal
  difference, no standings table.
- Draws. A draw is a 400, not a state to model.

## Risks

Invalidation is only visible two rounds deep, so the seed must have a played
final, and a criterion must change a quarter-final and assert that *both* the
semi and the final cleared - a one-level test passes on a version that clears
only the parent. Second risk: session 2 is promotion plus invalidation plus two
error codes in one endpoint, which is the oversized-cut shape that has overrun
four projects; it needs promotion and invalidation cut separately. Third: an
8-entrant bracket with names like "A" and "B" makes a wrong-side promotion
invisible - the fixtures should make each side's expected occupant distinctive.
