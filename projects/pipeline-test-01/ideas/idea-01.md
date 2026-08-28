# Cron Line Explainer

**One line:** A page where you paste a five-field cron expression and get back the
exact minutes it covers, a plain-English sentence, and a yes/no answer for whether
it would fire at a timestamp you type in.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 3 x 40 minutes.

## Theme

Every backend developer eventually meets a cron line and guesses at it. This
project makes the guess unnecessary: the student writes the parser that turns
`*/15 9-17 * * 1-5` into a set of minutes, a set of hours and a set of weekdays,
then the describer that turns those sets into a sentence, then the matcher that
answers "does it fire at 2026-03-02T09:15?". It is a parser and nothing else - no
scheduling, no background work, no clock. The reward loop is fast: type an
expression, see it explode into numbers, see it come back as English.

## Sessions

1. **Setup, the store, and the validity badge.** Types, a seed file of six saved
   cron lines, `GET /api/schedules`, and `/` listing each line with a valid or
   invalid badge. Validity is real work already: split into fields, reject the
   wrong field count, range-check each field against its own bounds (minute 0-59,
   hour 0-23, dom 1-31, month 1-12, dow 0-6). **Runs:** a list of six lines, two
   of them flagged invalid with a reason.
2. **Field expansion.** `expandField(text, min, max)` handles `*`, a number, a
   list `1,3,5`, a range `1-5`, a step `*/15`, a stepped range `9-17/2`, and any
   comma-joined mix of those, returning a sorted unique number array. `/schedules/[id]`
   shows all five expanded sets. `POST /api/schedules/check` returns 400 with the
   offending field named. **Runs:** a detail page printing the 4 minutes, 9 hours
   and 5 weekdays a line actually covers.
3. **Describe and match.** `describe(parsed)` builds a sentence from a small fixed
   grammar. `matches(parsed, "YYYY-MM-DDTHH:mm")` answers the fire question. A box
   on the detail page takes a timestamp and shows fires / does not fire.
   **Runs:** the full loop, expression in, English and a verdict out.

## What the student types

- `expandField` - the tokeniser and the step/range arithmetic. The single densest
  function in the project and the one every test leans on.
- `describe` - a table-driven sentence builder: "every 15 minutes, between 09:00
  and 17:59, Monday to Friday". Fixed clause order, fixed wording.
- `matches` - the field intersection, plus the day-of-month/day-of-week rule
  (they OR together when both are restricted, which is the classic cron trap and
  worth one criterion of its own).

## What this teaches that the shipped projects do not

recipe-box, tip-split and habit-tracker all read structured data and compute a
number from it. Here the input is a string with a grammar, and the first job is to
turn text into a data structure - tokenising, validating, and reporting *which*
part of the input was wrong. Nothing shipped has an error path that names a
position in the user's own input.

## Out of scope

- Actually running anything on a schedule. No timers, no jobs, no background work.
- Non-standard cron: `@daily`, `L`, `W`, `#`, seconds, years, timezones.
- Creating or editing saved lines. The seed file is the library.
- Computing the *next* fire time. Matching a given timestamp is the whole job;
  stepping forward through a calendar is a different, bigger project.

## Risks

The English sentence is the overrun risk: phrasing is infinitely arguable, and a
criterion has to pin an exact string. Fix it by declaring the grammar as a closed
clause table in the spec and grading only expressions the table covers. Second
risk: `matches` must parse the timestamp with UTC accessors or pure string
arithmetic - a local-time weekday is off by one west of Greenwich, exactly the bug
`learning/lessons.md` records against habit-tracker.
