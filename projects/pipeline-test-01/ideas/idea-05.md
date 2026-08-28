# Change At

**One line:** An offline timetable search: pick two stations and an earliest
departure, and get the direct trains plus the one-change journeys, with the
interchange rule enforced.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 3 x 40 minutes.

## Theme

A timetable is a list of services, and each service is an ordered list of calls -
station, arrival, departure. Every interesting question about it is a join with an
ordering constraint: a service takes you from A to B only if it calls at A *and
then later* at B. Add a change and it becomes a self-join with a wait-time
predicate. This is the shape behind most real query work, and here it is small
enough to hold in your head and seed by hand.

## Sessions

1. **Setup, the timetable, and a departure board.** Types, a seed of ~8 services
   over ~9 stations, `GET /api/stations`, and `/stations/[code]` showing every
   call at that station sorted by time, each with its service and destination.
   The work is the flatten-and-sort: services are stored as call lists, and the
   board is a different slice of the same data. **Runs:** a departure board per
   station.
2. **Direct journeys.** `findDirect(from, to, after)` - a service qualifies when
   its call list contains `from` at index i and `to` at index j with j > i, and
   its departure from `from` is at or after `after`. Results carry departure,
   arrival and a duration from `minutesBetween`. `/search` writes `from`, `to` and
   `after` into the query string so a search is a shareable link.
   **Runs:** a search form returning ranked direct trains, and an honest "no
   direct service" when there is none.
3. **One change.** `findWithChange` joins a leg arriving at station X with a leg
   departing X at least `MIN_INTERCHANGE` minutes later, excluding journeys where
   the same service covers both legs, deduping against the direct results, sorting
   by arrival then duration, and capping at 5. Each result names the change
   station and the wait. **Runs:** a pair with no direct service returns two
   viable itineraries.

## What the student types

- The index-ordering predicate in `findDirect` - "calls at both" is the wrong
  test, and the seed contains a service that proves it.
- `minutesBetween("09:05", "10:20")` - HH:MM arithmetic as pure string-to-minutes,
  used by duration, by the interchange gap, and by the sort.
- `findWithChange` - the nested loop over candidate interchange stations, the gap
  filter, the same-service exclusion, and the ordering with its tie-break.

## What this teaches that the shipped projects do not

recipe-box filters a flat list with a predicate per item. This is a join: results
are built from *pairs* of records, and validity depends on the relationship
between them, not on either one alone. Nothing shipped has an ordering constraint
inside a record, a dedupe step, or a sort that has to declare its tie-break.

## Out of scope

- Journeys with two or more changes. One change is the lesson.
- Services crossing midnight, and any notion of a calendar date, weekday or
  seasonal variation. One generic service day.
- Fares, seat availability, platforms, live delays, real network data.
- Editing the timetable. The seed is the network.

## Risks

The `after` time must come from the query string with a fixed default, never from
the real clock, or the test suite stops being repeatable. Second risk is the seed:
it has to be small enough to reason about and rich enough that a change is
genuinely required somewhere, that one pair is reachable only by an interchange
that *just* meets the minimum gap, and that another is excluded because it misses
it by a minute.
