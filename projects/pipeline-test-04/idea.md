# Tenpin

**One line:** A ten-pin bowling scorecard: four seeded games render as frame
grids, then the running total appears, with every strike and spare reaching
forward into the rolls that come after it.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Bowling is the smallest well-known calculation in which an item's value depends
on items that come *later*. A frame is not worth what it knocked down; a strike
is worth ten plus whatever the next two rolls do, and until those rolls exist
the frame has no score at all - not zero, not null, simply not yet. Every
student's first attempt sums each frame independently and is wrong by the second
frame of the seed.

## Sessions

1. **Setup, the games, and the frames.** Types, `data/games.json` with four
   games given as flat roll lists (all gutters, a perfect game, a spare-heavy
   mixed game, and one stopped after six frames), `frames(rolls)` splitting a
   flat list into ten frames - two rolls unless the first is a strike, and up to
   three in the tenth - `GET /api/games`, and `/games/[id]` rendering the ten
   frame boxes with rolls shown as `X`, `/`, `-` or a digit, each box carrying a
   `data-testid`. **Runs:** four games render as correctly divided grids, with
   no totals yet.
2. **Scoring and the running total.** `scoreGame(rolls)` returning a cumulative
   total per frame: ten plus the next two rolls for a strike, ten plus the next
   one for a spare, the plain sum otherwise, and `null` for a frame whose bonus
   rolls have not been rolled. `POST /api/games/score` takes a roll list in the
   body and returns the per-frame array plus the game total. **Runs:** the
   perfect game reads 300, the gutter game reads 0, and the unfinished game
   leaves exactly its last two frames blank.

## What the student types

- `frames` - the advance-by-one-or-two scan, and the tenth frame, which is the
  only frame that can hold three rolls.
- `scoreGame` - the lookahead into the *roll* list rather than the frame list,
  which is the reframing that makes the bonus rules one line each instead of a
  nest of special cases.
- `pendingFrame` - the test for "the rolls this frame needs do not exist yet",
  which is what lets an in-progress game render at all.

## What this teaches that the shipped projects do not

The first calculation where one item's value depends on later items. recipe-box
scaled each ingredient independently, tip-split divided a single total, and
ledger's running balance only ever looked backwards. It is also the first
"not computable yet" value in the track, deliberately distinct from zero - a
distinction TypeScript will make the student spell out in the return type.

## Out of scope

- Entering rolls by clicking pins. Rolls arrive from the seed or the POST body.
- Validating impossible games (twelve pins in a frame). The seed is legal.
- More than one player, handicaps, leagues, no-tap or other variants.
- Saving a scored game back to the store. Scoring is a pure read.

## Risks

The perfect game and the gutter game are both satisfied by wrong code -
`3 * frame` and `0` respectively - so the mixed game is the load-bearing
fixture, and criteria must pin the whole cumulative array, not the final total,
or two errors that cancel go green. Second: the tenth frame is where this
overruns. It is three rules in one place, and five consecutive projects have run
long on exactly that shape, so the tenth-frame handling should be its own cut
inside session 2 with the frame-box styling shipped rather than cut.
