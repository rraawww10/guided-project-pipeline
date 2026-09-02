# Table

**One line:** A six-team league where seeded results fold into a standings
table, the order is settled by a stated chain of tie-breaks including
head-to-head, and the matches still to play are generated rather than stored.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A league table is one fold and one comparator, and both are where beginners go
wrong in a recognisable way: the fold has to update two teams from a single
result, and the comparator has to apply four keys in order rather than sorting
four times. The tie-break chain also has one step that a comparator cannot
answer on its own - head-to-head needs the results list, not the two rows - so
the student meets a comparator with a closure around extra data. Nothing is
stored that can be derived: the fixtures still to play are the unordered pairs
minus the pairs already played.

## Sessions

1. **Setup, results, and the fold.** Types, `data/league.json` with six teams
   and ten played results chosen so that two teams tie on points, and another
   two tie on points *and* goal difference; `standings(teams, results)`
   producing played, won, drawn, lost, for, against, difference and points;
   `GET /api/standings`; and `/` rendering the table sorted by points alone,
   one `data-testid` per row. **Runs:** the table renders with counts that add
   up - every result has contributed to exactly two rows - and the tied teams
   sit together in an unspecified order.
2. **Tie-breaks and the fixtures nobody stored.** `compareRows(a, b, results)`
   applying points, then goal difference, then goals for, then the head-to-head
   result between the two tied teams, then name; the table now has one true
   order, and the row shows which rule separated it from the row above.
   `remainingFixtures(teams, results)` enumerating unordered pairs and removing
   those already played, plus `GET /api/fixtures` and a page listing them.
   **Runs:** the GD tie separates, the head-to-head tie separates, and the
   fixtures page lists exactly the five matches left.

## What the student types

- `standings` - the fold that writes two records per result, and the draw case
  that increments a different pair of columns.
- `compareRows` - the chain, returning only on a non-zero difference, and the
  head-to-head step that filters `results` for the meeting between these two
  teams and states what happens when they have not met or drew.
- `remainingFixtures` - the `i < j` pair enumeration and an order-independent
  key so that "A played B" also matches the stored "B played A".

## What this teaches that the shipped projects do not

Every shipped project sorts by at most one key - ledger sorted accounts by name -
so this is the first ordered tie-break chain, and the first comparator that
needs data beyond the two things it is comparing. It is also the first
derivation of things that are *not in the data at all*: the unplayed pairs exist
nowhere in the seed. The fold that updates two records from one input is new
too; habit-tracker's toggle touched one.

## Out of scope

- Entering or editing results, live scores, and any POST.
- Kick-off dates or times. A result carries a round number, and nothing reads
  the clock.
- More than one division or season, promotion and relegation, form guides,
  goal scorers, expected goals.
- Making points-per-win configurable. Three and one, fixed.

## Risks

Head-to-head is the fiddly rule: two teams may not have met, or may have drawn,
and the spec must state the fallback and the seed must contain both cases or the
Builder and the Verifier grade different orders. Second: a final order graded as
one list is satisfied by a hardcoded array of six ids, so the criteria need a
second results set - the cleanest fix is an endpoint that accepts results in the
body. Third: session 2 carries two substantial pieces against a 40-minute cap
and five consecutive projects have overrun; the fixture generator is the honest
drop candidate because the student types it, whereas the comparator is the
session.
