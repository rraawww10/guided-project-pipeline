# Depot

**One line:** A parcel board where every status change goes through one
transition table, and an event a parcel cannot legally accept comes back refused,
naming the state it was in.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A parcel is `booked`, then `collected`, then `in_transit`, then
`out_for_delivery`, then `delivered` - or it goes `returned` and stops. Which
moves are legal is *data*: one table, read in two directions. Read forwards it
answers "where does this event take me"; read backwards it answers "which
buttons should this parcel even show". Students usually write those as two
unrelated pieces of code that drift apart, and this project is built so the
drift is visible on screen.

## Sessions

1. **Setup, the table, and current state.** Types, `data/parcels.json` with six
   parcels each holding an ordered event log (one still `booked` with an empty
   log, one `delivered`, one `returned`), the transition table as a plain
   `Record<State, Record<Event, State>>`, `currentState(events)` folding a log
   down to one state, `GET /api/parcels`, and `/` listing each parcel with its
   state badge and event count. **Runs:** six seeded logs render as six correct
   states, including the empty log.
2. **Guards, refusals, and the timeline.** `allowedEvents(state)` derived from
   the same table - not a second list - and `POST /api/parcels/[id]/events`,
   which returns `200` with the new state or `409` with
   `{ reason, from, event }`. `/parcels/[id]` shows the log as a timeline of
   `from -> to` rows plus one button per allowed event, and a terminal parcel
   shows no buttons at all. **Runs:** a legal click extends the timeline; an
   illegal event is refused by name; a delivered parcel offers nothing.

## What the student types

- `currentState` - the fold over the log, the `booked` default for an empty log,
  and what happens when the log contains an event the table does not allow.
- `applyEvent` - the two-level table lookup and the single branch that
  distinguishes "no such transition" from "no such event".
- `allowedEvents` - the keys of one table row, which is the whole point: the
  buttons and the guard are the same fact queried twice.

## What this teaches that the shipped projects do not

First project whose rules live in a data structure rather than in `if`
statements, and the first where the legal-move set is *derived* rather than
written down. ledger had a rejection path, but its input was malformed text;
here every request is well-formed and merely illegal, which is a different
lesson and a different HTTP status. habit-tracker's toggle was the only prior
mutation, and it could never be refused.

## Out of scope

- Creating or deleting parcels, and editing a log after the fact.
- Timestamps from the real clock. Events carry a sequence number and a seeded
  `YYYY-MM-DD` string, and nothing reads `new Date()`.
- Couriers, addresses, tracking numbers that mean anything, notifications.
- Undo, or rolling a parcel back to a previous state.

## Risks

A table graded by one illegal transition is satisfied by `if (event ===
'collect') refuse`, so the criteria need refusals from two different states plus
a terminal one, and at least one legal transition that is illegal *elsewhere*.
Second: the POST writes to the store, so the suite has to reseed between tests
or the criteria have to be order-independent - state that in the spec, not in
the test writer's head. Third: `allowedEvents` must be graded on a state whose
legal set has two entries, or a hardcoded array passes.
