# Next Bus

**One line:** A departure board for three seeded bus routes that answers "what
leaves next, and how long do I wait" for a time given in the URL - including the
last bus of the night, which wraps to tomorrow morning.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

The current time is a query parameter, not a clock read. That single decision is
the lesson: injecting the moment makes the whole app a pure function of its
inputs, so a student can type `?at=23:52` and see the 05:40 first bus of the next
day appear with a 348-minute wait. Underneath it is minutes-since-midnight
arithmetic - parse, sort, search, wrap - which is the smallest honest piece of
modular arithmetic in the track.

## Sessions

1. **Setup, the timetable, and time as a number.** Types, `seed.json` with 3
   routes each holding a weekday and a weekend list of `HH:MM` departures,
   `toMinutes` / `fromMinutes` with a validated round trip, `GET /api/routes`,
   and `/` listing each route with its first departure, its last departure and
   how many services it runs on each day kind. **Runs:** three routes summarised
   from raw time strings, with nothing hardcoded.
2. **The next three, and the wrap.** `nextDepartures(times, atMinutes, n)`
   returning up to three upcoming departures with their wait in minutes, and
   wrapping past the last bus to the first departure of the next service day at
   `1440 - at + t`. `/routes/[id]?at=HH:MM&day=weekday` renders the board, and
   `GET /api/routes/[id]/next?at=...&day=...` answers 400 on a malformed time and
   404 on an unknown route. **Runs:** edit `at` in the address bar and the board
   recomputes, including after the last bus.

## What the student types

- `toMinutes` / `fromMinutes` - the parse, the two-digit pad on the way back, and
  the rejection of `24:00`, `7:5` and `abc`.
- `nextDepartures` - the search for the first departure at or after `at`, the
  "at exactly the departure minute counts as now, wait 0" rule, and the
  wrap-around branch when fewer than three remain today.
- The query-parameter read and validation in the route handler, which is where a
  400 gets decided.

## What this teaches that the shipped projects do not

habit-tracker banned the clock; this one makes the injected moment the visible
subject of the project rather than a constraint hidden in the seed file. Nothing
shipped does modular arithmetic, a wrap across a boundary, or a "next N after X"
search, and nothing shipped validates a query parameter and answers 400 - every
error path so far has been a 404 on an id.

## Out of scope

- Real GTFS data, live positions, any network call. Three hand-written routes.
- Journey planning, changes between routes, stops along a route. A route has one
  departure list, not a shape on a map.
- Holidays, per-date exceptions, and any day kind beyond weekday and weekend.
- A time picker widget. The input is the URL, deliberately.

## Risks

The wrap is one line and every fixture at midday passes without it, so the
criteria must include a `23:52` case and a "route whose last bus already went"
case, or the whole of session 2 is gradeable by a naive filter. Second risk:
session 1 reads thin next to session 2 - the day-kind summary and the round-trip
validation have to be real cuts, and session 2's cut should be split into the
search and the wrap so neither is oversized. Third: the board must carry a stable
`data-testid` per departure row, because the criteria count rows and read waits.
