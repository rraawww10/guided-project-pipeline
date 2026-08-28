# Runoff

**One line:** A ranked-choice vote counter that shows an election round by round -
who was eliminated, where their votes went, and who finally crossed the majority
line.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 3 x 40 minutes.

## Theme

Instant-runoff counting is a small algorithm with a big output: you tally first
preferences, eliminate the last-placed candidate, redistribute their ballots to
each voter's next surviving choice, and repeat until someone holds a majority of
the ballots still in play. Students have usually heard of it and never seen it
computed. The screen is the teaching aid - one column per round, with arrows for
transfers - and the function underneath is a loop that produces a *sequence* of
states rather than one answer.

## Sessions

1. **Setup, ballots, and round one.** Types, a seed of three elections (a clean
   4-candidate one with ~15 ballots, one that needs three rounds and exhausts two
   ballots, one that ends in a two-way tie for elimination), `GET /api/elections`,
   and `/` listing each election. `tally(ballots, eliminated)` counts each ballot
   toward its highest-ranked surviving candidate. `/elections/[id]` shows the
   round-1 table, sorted by votes with the declared tie-break.
   **Runs:** a first-preference table per election.
2. **Elimination and transfer.** `runRound` picks the candidate to eliminate -
   lowest tally, alphabetical on a tie - and `countElection` loops until a
   candidate holds more than half of the non-exhausted ballots or one candidate
   remains, returning `Round[]`. A ballot with no surviving preference becomes
   exhausted and leaves the denominator. The page renders every round.
   **Runs:** the three-round election shows all three tables and its exhausted
   count rising.
3. **The result, and the transfer view.** `GET /api/elections/[id]/result` returns
   the rounds plus `{ winner, roundsUsed, exhausted }`. Each round gains a
   transfer breakdown: of the eliminated candidate's N ballots, how many went to
   each survivor and how many exhausted. The winner is announced with the round
   they won in. **Runs:** an endpoint and a page that agree, on all three seeds.

## What the student types

- `tally` - walk each ballot's preference list, skip eliminated names, count the
  first survivor, or mark the ballot exhausted.
- `countElection` - the loop: majority test against the *continuing* ballots, the
  elimination choice with its tie-break, the accumulating `Round[]`, and the
  termination guard.
- `transfersFor(round)` - group the eliminated candidate's ballots by where they
  landed next.

## What this teaches that the shipped projects do not

tip-split and recipe-box each compute one derived number; habit-tracker computes a
streak by walking backwards through a fixed list. This is the first iterative
algorithm in the track whose output is a history of its own steps, and the first
where a rule the spec must *choose* (majority of continuing ballots, not of all
ballots; alphabetical tie-break, not first-seen) visibly changes the answer.

## Out of scope

- Casting or editing ballots. The seed is the electorate.
- Multi-seat STV, quotas, surplus transfer. Single seat only.
- Charts. The rounds are tables; a bar per candidate is fine, a chart library is
  not.
- Voter identity, authentication, or anything preventing double voting.

## Risks

The definitions are the risk, not the code: majority denominator, tie-break, and
what happens when the last two candidates tie must be pinned in the spec or the
Builder and the Verifier will each pick a defensible answer and disagree. Second
risk, straight from `learning/lessons.md`: a pure function graded against one
election can be satisfied by a hardcoded array, so the seed needs at least two
elections with different round counts and one deliberate tie.
