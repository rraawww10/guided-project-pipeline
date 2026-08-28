# Parcel Desk

**One line:** An operations console for parcels whose status is never stored - it
is folded out of an append-only event log, and the buttons on screen are whatever
the transition table says is legal from here.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 3 x 40 minutes.

## Theme

Most small apps keep a `status` column and hope nothing ever writes the wrong
value into it. This one keeps events - `booked`, `picked_up`, `out_for_delivery`,
`delivered`, `failed`, `cancelled` - and derives the status by folding them. Two
ideas land at once: state as a fold over history, and a transition table as data
rather than a pile of `if`s. Illegal moves are refused with a reason, and the
refusal is a test the student can see go green.

## Sessions

1. **Setup, the log, and the derived list.** Types, a seed log of ~24 events
   across 5 parcels, `GET /api/parcels`, and `/` listing each parcel with its
   derived status and event count. The logic is `deriveState(events)`: sort by
   sequence number, fold, and produce `{ status, attempts, lastEventAt }`.
   **Runs:** a list whose statuses exist nowhere in the seed file.
2. **The timeline and legal moves.** `/parcels/[id]` shows the event history in
   order and a row of action buttons produced by `allowedActions(state)`, read
   from a transition table keyed by current status. Unknown id gives 404.
   **Runs:** a delivered parcel shows no buttons; a picked-up one shows exactly
   two.
3. **Appending, and refusing.** `POST /api/parcels/[id]/events` validates the move
   against the same table, applies the guards (a `failed` parcel may be retried
   only while `attempts < 3`; nothing may be `cancelled` once picked up), appends
   with the next sequence number, and returns the new derived state. Illegal moves
   return 409 with a machine-readable `reason` and append nothing.
   **Runs:** clicking an action advances the parcel; a hand-posted illegal move
   is refused and the log is unchanged.

## What the student types

- `deriveState` - the fold, including the attempt counter and the rule that an
  out-of-order sequence number is sorted, not trusted.
- The transition table itself, plus `allowedActions` reading it - the same table
  feeds the UI and the API, which is the point.
- The guard check in the POST handler, and the 409-vs-201 branch with the
  append-nothing-on-refusal ordering.

## What this teaches that the shipped projects do not

recipe-box and tip-split are read-only; habit-tracker writes, but its one mutation
is a boolean flip that is always legal. Nothing shipped has a write that can be
*refused*, a 409, or state derived rather than stored. It is also the first time
the same data structure drives both what the screen offers and what the server
accepts.

## Out of scope

- Creating or deleting parcels. The seed defines the five.
- Users, couriers, permissions - any notion of who performed an event.
- Undo, event editing, or compensating events. The log only grows.
- Notifications, addresses, maps, tracking numbers from any real carrier.

## Risks

Timestamps. If an appended event stamps itself from the real clock, the test suite
stops being repeatable and the project cannot go through this pipeline - the
request body must carry the event's `at`, or the event must carry only its
sequence number. Second risk: the tests write to the log file, so the spec has to
say how the store is reset between tests, and the seed must be restored rather
than mutated in place.
