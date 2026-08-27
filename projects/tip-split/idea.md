# Tip Split

**Track:** fullstack
**Sessions:** 2
**Stack:** Next.js 15 (App Router), React 19, TypeScript
**Source material:** none

## Theme

A place to keep the bills you have already split. Students build a small list of
saved restaurant bills they can browse, then open one and re-split it across a
different number of people. The re-split is the payoff: it is the first time the
number on the screen is computed from state rather than read from the server, and
because it is money, a student can see immediately whether the arithmetic is right.

## Scope

- A JSON file on disk as the store, read and written through route handlers.
- List every saved bill: the place, the date, the total, and how many people it
  was originally split between.
- Open one bill: its total, its tip percentage, and the resulting amount per person.
- On the open bill, change the number of people and see the amount per person
  recompute. Nothing is saved - it is a view of the same bill.
- Seed data ships with the project: six bills, so the list has something real in
  it from session one.

## Out of scope

- Adding, editing or deleting bills. The list is read-only.
- Accounts, sign-in, anything per-user.
- Itemised bills. A bill is one total, not a list of dishes.
- Currency other than rupees, and any currency conversion.
- A database. The JSON file is the store, and that is deliberate.

## Constraints

- Runs offline. No external API, no network call the student has to configure.
- No state library. React state only.
- No CSS framework. Plain CSS modules, so the styling is not the lesson.
- Money is handled in whole paise as integers, never floating point. The per-person
  shares must add back up to the bill total exactly - when the split does not divide
  evenly, the leftover paise go to the first people in the list, one each.
- The number of people is at least 1 and at most 20.
