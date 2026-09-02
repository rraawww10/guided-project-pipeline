# Slots

**One line:** A one-day room booking board: seeded bookings drawn as bars on a
timeline, the free gaps computed rather than stored, and a proposed booking
either accepted or refused by naming the booking it collides with.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Two bookings that touch at 11:00 do not clash; two that share a single minute
do. That one boundary decides the whole project, and it is the bug every
first-attempt overlap test has. Once intervals compare correctly, the free time
in a room is the complement of the merged busy blocks - a shape students
recognise the moment they see it drawn, and one they will meet again in every
calendar, scheduler and rate limiter they ever touch.

## Sessions

1. **Setup, the day, and the bars.** Types, `data/day.json` naming the tracked
   date and three rooms with nine bookings between them - two that touch exactly
   at 11:00, two that genuinely overlap, and one room with nothing booked -
   `toMinutes("09:30")` and `toLabel(570)`, `overlaps(a, b)` on half-open
   intervals, `GET /api/rooms`, and `/` drawing each room's day as bars
   positioned from minute offsets, each with a `data-testid`. **Runs:** three
   rooms render to scale, and the one real clash is flagged while the 11:00
   touch is not.
2. **Merged busy time and proposals.** `mergeBusy(bookings)` - sort by start,
   sweep, extend while the next starts at or before the current end - and
   `freeSlots(busy, dayStart, dayEnd, minMinutes)` returning the complement
   filtered to gaps of at least 30 minutes. `POST /api/rooms/[id]/propose`
   answers `{ ok: true }` or `{ ok: false, conflict: <booking id> }`.
   **Runs:** each room lists its real gaps; a proposal into a gap is accepted
   and one crossing a booking is refused by that booking's id.

## What the student types

- `toMinutes` - the split and the sixty-multiply, plus the rule that every time
  in the app is an integer minute from midnight and only the view formats it.
- `overlaps` - `a.start < b.end && b.start < a.end`, and the argument for `<`
  over `<=` that the 11:00 fixture settles on screen.
- `mergeBusy` / `freeSlots` - the sweep that extends a block, and the complement
  walk that starts at `dayStart`, emits the space before each block, and
  remembers the tail after the last one.

## What this teaches that the shipped projects do not

The first duration arithmetic in the track. habit-tracker had dates but never a
length, and nothing shipped has ever compared two ranges. The complement of a
merged set is a shape none of the shipped projects contain, and the touching-
boundary case is a rare thing in teaching: a genuine off-by-one whose right
answer is visible rather than argued.

## Out of scope

- Any day but the seeded one. No navigation, no recurrence, no "now" line, and
  nothing reads the real clock.
- Writing an accepted proposal into the store. Proposing is a pure check, which
  keeps the seed constant and the criteria order-independent.
- Attendees, room capacity, equipment, approval workflows, drag to create.
- Bookings that cross midnight. Every booking lies inside one day.

## Risks

Bar positioning is CSS with no grading value and it can eat ten minutes of a
40-minute session, so the layout must ship written with only the minute
arithmetic cut - a session whose named drop candidate is markup nobody types
recovers nothing. Second: the spec must state whether two touching bookings
merge into one busy block for the purpose of gaps (they do), or the Builder and
the Verifier will grade different free-slot lists. Third: `freeSlots` needs the
empty room and the fully-booked room as fixtures, or a version that forgets the
tail gap still passes.
