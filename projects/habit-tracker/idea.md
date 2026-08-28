# Habit Tracker

**Track:** fullstack
**Sessions:** 3            <!-- each session is 40 minutes of live teaching -->
**Stack:** Next.js 15 (App Router), React 19, TypeScript, CSS Modules
**Source material:** none

## Theme
A weekly habit board. The student sees their habits as rows and the seven days of
one week as columns, clicks a cell to mark a day done, and watches a streak count
update. It is small enough to finish in three sessions and it teaches three
things the other house projects do not: date arithmetic, a grid built from two
nested arrays, and a pure function worth unit-testing on its own.

## Scope

- **Screen `/`** - the week board. One row per habit, seven cells per row for
  Monday to Sunday of the tracked week. A done cell is visually distinct from a
  not-done cell. Each row shows the habit name and its current streak.
- **Screen `/habits/[id]`** - one habit. Its name, its seven cells for the same
  week, and its current streak spelled out.
- **`GET /api/habits`** - every habit with its done-days for the tracked week and
  its current streak.
- **`GET /api/habits/[id]`** - one habit, same shape. 404 when the id is unknown.
- **`POST /api/habits/[id]/toggle`** - body names one date; flips that date
  between done and not-done for that habit and returns the updated habit.
- **`lib/streak.ts`** - the streak calculation, as a plain function over a list
  of done dates. Counts consecutive done days ending at the tracked day, so a gap
  resets it to zero.

## Out of scope

- Creating, renaming or deleting habits. The seed file is the habit list.
- Any week other than the tracked week. No navigation between weeks.
- Accounts, login, or more than one user's habits.
- Reminders, notifications, charts, or a monthly view.
- Editing a habit's target frequency. Every habit is simply daily.

## Constraints

- No external database. A JSON file under `data/` is the store, read and written
  with node's `fs`. It must run offline with no API keys.
- **The tracked week must not come from the real clock.** The seed file names the
  tracked day, and every date in the app is derived from it. A habit tracker that
  reads `new Date()` cannot be tested twice with the same result, and the whole
  pipeline depends on a test suite that gives the same answer every run.
- Dates are `YYYY-MM-DD` strings at every boundary - in the seed, in the API
  responses, and in the toggle body. A `Date` object may be used inside a module
  as an implementation detail; what is banned is reading the real clock, meaning
  a zero-argument `new Date()` or `Date.now()`. Constructing a `Date` from the
  seed's tracked day is fine.
- Any date arithmetic must give the same answer in every timezone. Use the UTC
  accessors, or plain string arithmetic. A weekday derived with local-time
  accessors from a `YYYY-MM-DD` string is off by one west of Greenwich, which
  would pass here and fail for students.
- The week runs Monday to Sunday.
- Seed with 4 habits, with enough done-days that at least one habit has a streak
  of 3 or more, one has a streak of 0 because of a gap, and one has no done days
  at all. The tests need all three cases to exist.
- Session 1 carries the project setup - types, store, seed, and the first screen -
  so it should carry fewer cut points than sessions 2 and 3.
