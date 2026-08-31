# Dispatch

**One line:** A parcel tracker whose current state is never stored - it is folded
out of an append-only event log through a transition table, and the table also
decides which buttons the screen is allowed to show.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Six states, seven events, and one table that owns every rule about which follows
which. Nothing in the seed file records where a parcel *is*; it records what
happened to it, in order, and the state is a fold over that list. The payoff is
that the same table drives three things at once - the derived state, the set of
buttons on screen, and the 409 the API returns when someone posts an event that
is not allowed - so a student changes one data structure and watches three
behaviours move together.

## Sessions

1. **Setup, the log, and the derived state.** Types, the `TRANSITIONS` table,
   `seed.json` with 5 parcels each carrying an event log (each event has a
   seeded timestamp string that is data, never `Date.now()`), `applyEvent(state,
   event)` returning the next state or `null`, `stateOf(log)` folding from
   `booked`, `GET /api/parcels`, and `/` listing every parcel with its derived
   state. **Runs:** five parcels showing five different states, none of which
   appears anywhere in the seed file.
2. **The timeline and the refusal.** `/parcels/[id]` renders the log as a
   timeline and offers exactly the events `allowedEvents(state)` permits - an
   empty set on `delivered` and `returned`, with a stated message. `POST
   /api/parcels/[id]/events` appends a legal event and returns the updated
   parcel, answers 409 with the offending state-and-event pair when the
   transition is illegal, and 404 on an unknown id. An illegal event must leave
   the log byte-identical. **Runs:** a parcel walks from `booked` to `delivered`
   by clicking, and a hand-posted illegal event is refused without changing
   anything.

## What the student types

- The `TRANSITIONS` table itself, as a typed record of state to event to state -
  the point being that it is data, not a `switch`.
- `stateOf` - the fold, including what it does when the log contains an event the
  table rejects (the seed contains one such parcel).
- `allowedEvents` - derived from the table, so the UI cannot drift from the API.
- The 409 branch, which must not write to disk before it decides.

## What this teaches that the shipped projects do not

habit-tracker's toggle is a two-value flip with no notion of a legal move.
Nothing shipped has a state machine, an append-only log, derived-rather-than-
stored state, or a request that is *correctly refused*. It is also the first
project where the UI's affordances are computed from the same rule the server
enforces, which is the honest way to teach "never trust the client".

## Out of scope

- Creating or deleting parcels, and any editing of a past event.
- Timestamps that come from the clock, elapsed-time displays, or SLA countdowns.
- Multi-parcel shipments, routing, addresses, maps, notifications.
- Undo. The log only grows; `return` is a state, not a rewind.

## Risks

The state set wants to grow. Cap it at six states and seven events in the spec or
session 2 will not fit. Second risk: session 2 carries the timeline, the button
derivation and the endpoint with its two error codes, which is one oversized cut
waiting to happen - it should be specified as at least three cuts, with the 409
branch separate from the append. Third: `stateOf` graded on one parcel is
indistinguishable from reading a stored field, so the criteria need two parcels
whose logs differ only in their last two events.
