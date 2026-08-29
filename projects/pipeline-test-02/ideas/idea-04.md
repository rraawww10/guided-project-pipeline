# Table

**One line:** A league table folded out of a fixed list of match results and
ordered by the competition's real tie-break rules - including the head-to-head
mini-league that separates two teams who are level on everything else.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Everybody can read a league table and almost nobody can say how the middle of it
is ordered. Behind it is a fold - fifteen match records producing six rows, each
match touching two of them in opposite directions - and then a comparator chain
that has to be *chosen* rather than discovered. The seed is engineered so two
teams finish level on points and goal difference, which forces the interesting
rule: rebuild a table from only the matches those teams played against each
other, and rank them inside it.

## Sessions

1. **Setup, results, and the raw table.** Types, a seed of one completed
   competition - six teams, all fifteen matches, scores chosen so one pair ends
   level on points and goal difference and another pair level on points alone.
   `GET /api/matches`, and `/` listing every result. The work is
   `tableFrom(matches)`: the fold producing played, won, drawn, lost, goals for,
   goals against, goal difference and points per team, sorted by points only.
   **Runs:** a table whose numbers add up - every column totals correctly across
   the six rows.
2. **The tie-break, and the team page.** `rankTeams(rows, matches)` applies the
   declared order: points, then goal difference, then goals scored, then a
   head-to-head mini-league among exactly the tied group, then alphabetical.
   `headToHead(tiedTeams, matches)` filters the fixture list and calls
   `tableFrom` again on the subset. `GET /api/table` returns the ranked rows with
   a `separatedBy` field naming the rule that broke each tie. `/teams/[code]`
   shows that team's five matches in round order with a `WWDLW` form string.
   **Runs:** the level pair is separated, and the table says by what.

## What the student types

- `tableFrom` - the fold, including the draw case and the fact that one match
  record updates two rows with mirrored goals for and against.
- `rankTeams` - the comparator chain, written so each rule is a named step rather
  than one unreadable `sort` callback.
- `headToHead` - calling `tableFrom` on a filtered slice of its own input, which
  is the first time in the track a function is reused against a subset of the
  data that produced it.

## What this teaches that the shipped projects do not

recipe-box filters a flat list one item at a time and tip-split reads a single
record. This is an aggregation: one output row is built from many inputs, and
each input contributes to two outputs in opposite directions - the classic place
where a fold goes subtly wrong and still looks plausible. It is also the first
multi-key ordering in the track with a tie-break the spec has to declare, and the
first function invoked on a subset of its own result.

## Out of scope

- Fixtures not yet played, live scores, or a partially complete season.
- Points deductions, bonus points, and any sport whose scoring is not
  three-one-nil.
- Promotion and relegation zones, badges, colours - the table is a table.
- Editing results, adding matches, or a second season.

## Risks

A comparator with five steps and a seed that only ever exercises two of them
leaves three steps ungraded, which is exactly the dead-code case
`learning/lessons.md` warns about - the seed has to force each rule at least
once, and the spec should say which pair of teams proves which rule. Second, the
head-to-head rule needs a stated answer for a three-way tie, or the Builder
invents one. Third, the `separatedBy` string must be an exact enumerated value,
not free prose, or no criterion can read it.
