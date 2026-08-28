# Habit Tracker

Three 40-minute sessions. Next.js 15 App Router, React 19, TypeScript, CSS
Modules. A JSON file under `data/` is the only store. No database, no API keys,
no network.

## Outcome

A weekly habit board. Screen `/` draws one row per habit and seven cells per row
for Monday to Sunday of one fixed week. A done cell is visually distinct from a
not-done cell, and each row states the habit's current streak. Clicking a cell on
`/` flips that day between done and not-done, writes the change to
`data/habits.json`, and replaces that habit's row on screen. Screen
`/habits/[id]` shows the same week and the same streak for one habit, and its
cells are display only.

The tracked week never comes from the real clock. The seed names the tracked day
as `2026-08-26`, a Wednesday, and every date in the app is derived from it, so
the same test run gives the same answer forever. The tracked week is therefore
Monday `2026-08-24` through Sunday `2026-08-30`.

Three things this project teaches that the other house projects do not: date
arithmetic over `YYYY-MM-DD` strings, a grid built from two nested arrays, and a
pure streak function worth unit-testing on its own.

## Out of scope

- Creating, renaming or deleting habits. The seed file is the habit list.
- Any week other than the tracked week. There is no navigation between weeks.
- Accounts, login, or a second user's habits.
- Reminders, notifications, charts, or a monthly view.
- Per-habit target frequency. Every habit is daily.
- Reading the real clock - no zero-argument `new Date()` and no `Date.now()`,
  anywhere in `app/` or `lib/`. Constructing a `Date` from the seed's
  `trackedDay` string is allowed, and so is any UTC accessor on it.
- Toggling from `/habits/[id]`. Its cells are display only; `/` is the only
  screen that writes.
- A loading indicator and a failed-fetch branch on either screen. `/` declares
  one state, `loaded`; `/habits/[id]` declares `loaded` and `not-found`. Before
  the first response arrives a screen draws no rows and no cells, and nothing
  grades that moment.

## Data model

Dates are `YYYY-MM-DD` strings at every boundary: in the seed, in every API
response, and in the toggle request body. A `Date` object may be built from a
`YYYY-MM-DD` string inside a module as an implementation detail, and any date
arithmetic uses the UTC accessors (`getUTCDay`, `setUTCDate`) or plain string
arithmetic, so no computed date changes with the machine's timezone.

The types:

```
Habit     = { id: string; name: string; doneDates: string[] }
Store     = { trackedDay: string; habits: Habit[] }
HabitWeek = {
  id: string
  name: string
  streak: number
  days: { date: string; done: boolean }[]   // always 7 entries, Monday first
}
```

`HabitWeek` is the response body of all three endpoints. Every non-200 response
body is `{ "error": string }` - exactly one key, whose value is a non-empty
message.

`data/habits.seed.json` is the immutable seed, committed to the repository:

```
{
  "trackedDay": "2026-08-26",
  "habits": [
    { "id": "drink-water", "name": "Drink water",
      "doneDates": ["2026-08-22","2026-08-23","2026-08-24","2026-08-25","2026-08-26"] },
    { "id": "read-pages",  "name": "Read 10 pages",
      "doneDates": ["2026-08-24","2026-08-25"] },
    { "id": "meditate",    "name": "Meditate",  "doneDates": [] },
    { "id": "stretch",     "name": "Stretch",   "doneDates": ["2026-08-26"] }
  ]
}
```

`data/habits.json` is the live store. It is listed in `.gitignore` and is never
committed: it appears on the first read and is deleted to reset the world.
`data/habits.json` is absent from every shipped copy of the project - anything
that packages `app/` deletes it first - so the first read of a fresh copy always
re-seeds, and no student ever opens a board built from a test run's leftovers. No
`doneDates` array holds a duplicate - the seed has none, and `toggleDate` adds a
date only when it is absent, so it cannot create one.

The three streak cases the tests need all exist in the seed:

| habit id      | done days in the tracked week          | streak | why                                    |
|---------------|----------------------------------------|--------|----------------------------------------|
| `drink-water` | 2026-08-24, 2026-08-25, 2026-08-26     | 5      | unbroken back to Saturday 2026-08-22   |
| `read-pages`  | 2026-08-24, 2026-08-25                 | 0      | a gap: the tracked day is not done     |
| `meditate`    | none                                   | 0      | no done days at all                    |
| `stretch`     | 2026-08-26                             | 1      | the tracked day only                   |

**Library modules.** Every exported function is spelled out with its parameters,
because the cut hints call them by name:

- `lib/week.ts` - `weekDates(trackedDay: string): string[]`, the seven
  `YYYY-MM-DD` strings of that date's Monday-to-Sunday week, Monday first.
- `lib/streak.ts` - `streakOf(doneDates: string[], trackedDay: string): number`,
  the count of consecutive done days ending at `trackedDay`, so a gap resets it
  to zero.
- `lib/toggle.ts` - `toggleDate(dates: string[], date: string): string[]`, a new
  array with `date` added when absent and dropped when present.
- `lib/store.ts` - `readStore(): Store`, `writeStore(store: Store): void`,
  `findHabit(store: Store, habitId: string): Habit | null`, and
  `habitWeek(habit: Habit, trackedDay: string): HabitWeek`.

`readStore()` copies `data/habits.seed.json` over `data/habits.json` when that
file is absent, then re-reads and re-parses `data/habits.json` on every call and
gives back a fresh object. Nothing is cached, so deleting the file resets the
world even inside a running server. `findHabit` searches the `Store` it is
handed and gives back an element of that store's `habits`, so mutating what it
found and then calling `writeStore(store)` persists the change. Writes go
through `writeStore` using node's `fs`.

**Skeleton fallbacks.** Each cut sits below a fallback declared in the same
function, and every fallback fails the criteria that name the cut. All eight are
fixed here, so the Builder picks none of them:

| cut                    | the fallback above the marker                                            |
|------------------------|--------------------------------------------------------------------------|
| `cut-week-dates`       | `dates` starts as an empty array                                         |
| `cut-streak-count`     | `count` starts at `-1`                                                   |
| `cut-store-find-habit` | `found` starts as `null`                                                 |
| `cut-api-habit-get`    | `status` starts at 501, `body` at `{ "error": "not implemented" }`       |
| `cut-habit-page`       | `missing` starts as `false`, with no cells and `streakText` `Streak: -1` |
| `cut-toggle-dates`     | `next` starts as an empty array                                          |
| `cut-api-toggle`       | `status` starts at 501, `body` at `{ "error": "not implemented" }`       |
| `cut-board-click`      | `onCellClick`'s body below the marker is empty, so a click does nothing  |

`found` starting as `null` is load-bearing: a fallback of `store.habits[0]` also
compiles, and it would let a student fill `cut-api-habit-get` alone and see
`c-2-1`, `c-2-3` and `c-2-4` go green with `findHabit` still empty. No
downstream checker can see that, which is why it is decided here.

## Endpoints

| id                | method | path                          | request            | response                          | status        |
|-------------------|--------|-------------------------------|--------------------|-----------------------------------|---------------|
| `ep-habits-list`  | GET    | `/api/habits`                 | none               | `HabitWeek[]`                     | 200           |
| `ep-habit-get`    | GET    | `/api/habits/[id]`            | none               | `HabitWeek` or `{ error }`        | 200, 404      |
| `ep-habit-toggle` | POST   | `/api/habits/[id]/toggle`     | `{ date: string }` | `HabitWeek` or `{ error }`        | 200, 400, 404 |

`ep-habit-get` answers 404 for a habit id that is not in the store.

`ep-habit-toggle` accepts exactly one set of dates: the seven `YYYY-MM-DD`
strings of the tracked week, `2026-08-24` through `2026-08-30`. Anything else is
a 400 - an absent `date`, a `date` that is not a string, a malformed string such
as `"not-a-date"`, `"2026-13-45"` or `"26-08-2026"`, and an in-shape date outside
the tracked week such as `"2026-08-31"`. The `date` is validated before the
habit id, so an unknown habit sent an invalid `date` answers 400. A 400 or a 404
leaves `data/habits.json` byte-for-byte unchanged.

## Screens

Both screens are client components and both read their data from the API, so
every fetch has an owner. Class names are hashed by CSS Modules, so every
element a test reads carries a `data-testid` and the tests read those, never a
class.

**`sc-board`, route `/`** - the week board. States: loaded.

- one element with `data-testid="habit-row"` per habit, carrying
  `data-habit-id` set to the habit id
- inside each row, `data-testid="habit-name"` with the habit name
- inside each row, `data-testid="habit-streak"` with the text `Streak: `
  followed by the number, for example `Streak: 5`
- inside each row, seven elements with `data-testid="day-cell"`, each carrying
  `data-date` set to that column's date string and `data-done` set to the string
  `"true"` or the string `"false"`. The done styling keys off `data-done`, which
  is what makes the two states visually distinct.
- the board issues one `GET /api/habits` when it mounts and does not issue a
  second one; a cell click sends `POST /api/habits/<id>/toggle` and the row is
  rebuilt from that response.

**`sc-habit`, route `/habits/[id]`** - one habit. States: loaded, not-found.

- `data-testid="habit-name"`, `data-testid="habit-streak"`, and the same seven
  `day-cell` elements with `data-date` and `data-done`
- `data-testid="habit-missing"`, with the text `Habit not found`, shown in place
  of the name, the streak and the cells when `GET /api/habits/[id]` answers 404

## Sessions

Session 1 carries the project setup - types, store, seed, the list endpoint and
the first screen - so it carries two cut points where sessions 2 and 3 carry
three.

The store lives at `data/habits.json` relative to the running app's own
directory, which `readStore()` resolves through `process.cwd()`. **Every test in
every session deletes that file - resolved from the target the suite is running
against, `app/` or `skeleton/` - before it runs**, and lets `readStore()` copy
`data/habits.seed.json` back. Every number in every criterion below is measured
from the seed state, so the suite gives the same answer on its first run and its
hundredth, in any order.

A test may instead write `data/habits.json` itself, with the seed's four habits
and a different `trackedDay`, which is how `c-1-6` drives the week arithmetic
from a second and a third tracked day. That is a test fixture and not a feature:
the app still reads its one tracked day from the store and still renders exactly
one week, so no screen and no endpoint gains week navigation.

A criterion may name a cut declared in an earlier session as a dependency. Only
the cuts declared in a session are opened in that session's skeleton; an earlier
session's cut is already filled by the student who reached this one.

### Session 1 - The week board

**Goal.** Build the JSON file store, derive the fixed tracked week from the
seed, and render the board so `GET /api/habits` and screen `/` show 4 habit rows
with 7 day cells and a streak each.

**Teaches.** Deriving a fixed Monday-to-Sunday week from one date string; a pure
streak function over a list of date strings.

**Builds.** `ep-habits-list`, `sc-board`.

**Acceptance criteria.**

- `c-1-1` - GET /api/habits returns 200 with a JSON array of 4 habits, each
  carrying id, name, streak and a days array of exactly 7 entries.
  Cuts: `cut-week-dates`.
- `c-1-2` - GET /api/habits returns every habit's days[].date as the strings
  2026-08-24, 2026-08-25, 2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29,
  2026-08-30 in that Monday-to-Sunday order. Cuts: `cut-week-dates`.
- `c-1-3` - GET /api/habits returns streak 5 for id drink-water, 0 for id
  read-pages, 0 for id meditate and 1 for id stretch.
  Cuts: `cut-streak-count`.
- `c-1-4` - screen / renders 4 elements with data-testid habit-row, and the row
  with data-habit-id drink-water contains a data-testid habit-streak element
  whose text is exactly `Streak: 5`. Cuts: `cut-streak-count`.
- `c-1-5` - screen / renders 7 elements with data-testid day-cell inside the
  habit-row with data-habit-id drink-water, and data-done is the string true on
  data-date 2026-08-24, 2026-08-25 and 2026-08-26 and the string false on the
  other 4 cells. Cuts: `cut-week-dates`.
- `c-1-6` - with data/habits.json written so trackedDay is 2026-08-30, a Sunday,
  GET /api/habits returns every habit's days[].date as 2026-08-24, 2026-08-25,
  2026-08-26, 2026-08-27, 2026-08-28, 2026-08-29, 2026-08-30 in that order; and
  with data/habits.json written so trackedDay is 2026-09-06, GET /api/habits
  returns every habit's days[].date as 2026-08-31, 2026-09-01, 2026-09-02,
  2026-09-03, 2026-09-04, 2026-09-05, 2026-09-06 in that order.
  Cuts: `cut-week-dates`.

**Cut points.**

- `cut-week-dates` in `lib/week.ts` - the week arithmetic. Hint: fill `dates`
  with the 7 `YYYY-MM-DD` strings for Monday through Sunday of the week that
  contains `trackedDay`, oldest first. Step back from `trackedDay` to that
  week's Monday and forward from there, and use the UTC accessors (`getUTCDay`,
  `setUTCDate`) or plain string arithmetic so the 7 strings do not change with
  the machine's timezone. Read no clock: the same `trackedDay` always gives the
  same 7 strings.
- `cut-streak-count` in `lib/streak.ts` - the streak itself. Hint: walk day by
  day backwards from `trackedDay` while each date is present in `doneDates`, and
  put the number of unbroken done days ending on `trackedDay` into `count`. Step
  with the UTC accessors or plain string arithmetic so the answer does not change
  with the machine's timezone, and leave `count` at 0 when `trackedDay` itself is
  absent from `doneDates`.

The two cuts carry different criteria: `cut-week-dates` is named by `c-1-1`,
`c-1-2`, `c-1-5` and `c-1-6`, `cut-streak-count` by `c-1-3` and `c-1-4`, so each
cut has criteria the other does not gate. `c-1-6` is what makes `cut-week-dates`
arithmetic rather than a lookup: the seven strings for the tracked week are
printed in `c-1-2` and in the session guide, so with one tracked day as the only
fixture a literal array would be green everywhere and the student would be told
they were done. `c-1-6` also pins the Sunday case, where `trackedDay`'s own
weekday number is 0 and the step back to Monday is a full week larger than the
Wednesday case needs, so a formula that is right for 2026-08-26 and a week wrong
for a Sunday is red here instead of shipping as the answer the instructor teaches
from.

The board's nested map over habits and days is written live and handed over
complete - the student's own work in session 1 is the two pure functions in
`lib/`, and the first JSX the student writes is session 2's day-cell map.

### Session 2 - One habit's page

**Goal.** Add the single-habit endpoint with its 404 branch and the
`/habits/[id]` screen that shows one habit's 7 day cells, its streak, and its
not-found message.

**Teaches.** Dynamic route segments with `[id]` in the App Router; a 404 branch
in a route handler; mapping a days array into cells with data attributes.

**Builds.** `ep-habit-get`, `sc-habit`.

**Acceptance criteria.**

- `c-2-1` - GET /api/habits/drink-water returns 200 with name Drink water, a
  days array of exactly 7 entries and streak 5.
  Cuts: `cut-store-find-habit`, `cut-api-habit-get`.
- `c-2-2` - GET /api/habits/no-such-habit returns 404 with a JSON body whose
  error key holds a non-empty string. Cuts: `cut-api-habit-get`.
- `c-2-3` - screen /habits/read-pages renders 7 elements with data-testid
  day-cell, with data-done the string true on data-date 2026-08-24 and
  2026-08-25 and the string false on the other 5 cells.
  Cuts: `cut-store-find-habit`, `cut-api-habit-get`, `cut-habit-page`.
- `c-2-4` - screen /habits/stretch displays a data-testid habit-name element
  whose text is exactly `Stretch` and a data-testid habit-streak element whose
  text is exactly `Streak: 1`. Cuts: `cut-store-find-habit`,
  `cut-api-habit-get`, `cut-habit-page`.
- `c-2-5` - screen /habits/no-such-habit displays an element with data-testid
  habit-missing whose text is exactly `Habit not found`, renders 0 elements with
  data-testid day-cell, and renders no habit-name element and no habit-streak
  element. Cuts: `cut-api-habit-get`, `cut-habit-page`.

**Cut points.**

- `cut-store-find-habit` in `lib/store.ts` - the lookup. Hint: inside
  `findHabit`, assign to `found` the one habit in `store.habits` whose `id`
  equals the `habitId` argument, and leave `found` as `null` when no habit in
  `store.habits` matches.
- `cut-api-habit-get` in `app/api/habits/[id]/route.ts` - the two branches.
  Hint: read the store with `readStore()` into `store` and look the habit up with
  `findHabit(store, habitId)`. When that gives a habit, set `body` to
  `habitWeek(habit, store.trackedDay)` and `status` to 200. When it gives `null`,
  set `body` to an object with an `error` key and `status` to 404.
- `cut-habit-page` in `app/habits/[id]/page.tsx` - the single-habit render.
  Hint: when the `/api/habits/[id]` response status is 404, set `missing` to
  `true`. Otherwise map `habit.days` into one `day-cell` element per entry, each
  with `data-date` set to that entry's date string and `data-done` set to the
  string `"true"` on a done entry and the string `"false"` on every other entry,
  and set `streakText` to `Streak: ` joined with `habit.streak`. Keep the
  `habit-name` element and the `habit-missing` element already in the file: when
  `missing` is `true` the page draws `habit-missing` and no `habit-name`, no
  `habit-streak` and no `day-cell`. Only a 404 sets `missing`; any other non-200
  status leaves the page in its pre-response state, and nothing grades that.

The three cuts carry different criteria. `c-2-2` gates the route's 404 branch
alone. `c-2-5` reaches the page through that 404 without the store lookup, since
an unknown id needs no habit. `c-2-1` names the lookup and the route but not the
page. And `c-2-4` reads a non-zero streak on screen, `Streak: 1` on
`/habits/stretch`, so a fallback that renders `Streak: 0` or `Streak: -1` is red
- `c-2-3` keeps `read-pages` for its false-cell coverage.

### Session 3 - Toggle a day

**Goal.** Add POST /api/habits/[id]/toggle with its 400 and 404 branches, so a
click on a day cell flips that day in `data/habits.json` and replaces that
habit's row on screen `/` from the POST response body.

**Teaches.** A POST route handler that reads and validates a JSON body; writing
the store back to disk with node `fs`; replacing one item inside React array
state.

**Builds.** `ep-habit-toggle`.

**Acceptance criteria.**

- `c-3-1` - POST /api/habits/stretch/toggle with body `{"date": "2026-08-25"}`
  returns 200 with streak 2 and the days entry for 2026-08-25 marked done.
  Cuts: `cut-toggle-dates`, `cut-api-toggle`.
- `c-3-2` - POST /api/habits/drink-water/toggle with body
  `{"date": "2026-08-26"}` returns 200 with streak 0, and a following
  GET /api/habits/drink-water persists streak 0 and 2 days marked done in the
  week. Cuts: `cut-toggle-dates`, `cut-api-toggle`, `cut-store-find-habit`.
- `c-3-3` - POST /api/habits/read-pages/toggle twice with body
  `{"date": "2026-08-26"}` returns 200 both times, streak 3 on the first
  response and streak 0 with 2 days marked done on the second.
  Cuts: `cut-toggle-dates`, `cut-api-toggle`.
- `c-3-4` - POST /api/habits/no-such-habit/toggle with body
  `{"date": "2026-08-26"}` returns 404; POST /api/habits/stretch/toggle returns
  400 for body `{}`, for body `{"date": "not-a-date"}` and for body
  `{"date": "2026-08-31"}`; each of those 4 responses carries a JSON body whose
  error key holds a non-empty string; and after one GET /api/habits has
  materialised data/habits.json from the seed, that file is byte-for-byte
  identical before and after the 4 requests. Cuts: `cut-api-toggle`.
- `c-3-5` - clicking the day-cell with data-date 2026-08-26 in the habit-row
  with data-habit-id meditate on screen / updates that cell's data-done to the
  string true and that row's habit-streak text to `Streak: 1`, leaves the
  drink-water row's habit-streak text at `Streak: 5`, and the browser issues
  exactly 1 GET request whose path is /api/habits from opening screen / to the
  end of that click. Cuts: `cut-board-click`, `cut-api-toggle`,
  `cut-toggle-dates`.

**Cut points.**

- `cut-toggle-dates` in `lib/toggle.ts` - the flip. Hint: inside `toggleDate`,
  assign to `next` a new array holding `dates` with every occurrence of `date`
  dropped when `dates` already contains it, and `dates` with `date` added when it
  does not. Every other string in `dates` stays in `next`, and `dates` itself is
  left unmutated.
- `cut-api-toggle` in `app/api/habits/[id]/toggle/route.ts` - the write path.
  Hint: read `date` from the parsed JSON body and read the store with
  `readStore()` into `store`. When `date` is not one of the 7 strings from
  `weekDates(store.trackedDay)`, set `status` to 400 and `body` to an object with
  an `error` key, and write nothing to disk. Otherwise call
  `findHabit(store, habitId)`: on `null` set `status` to 404 and `body` to an
  object with an `error` key, and write nothing to disk; on a habit set that
  habit's `doneDates` to `toggleDate(habit.doneDates, date)`, persist the whole
  `store` with `writeStore(store)`, then set `body` to
  `habitWeek(habit, store.trackedDay)` and `status` to 200.
- `cut-board-click` in `app/page.tsx` - the click handler. Hint: inside
  `onCellClick`, POST `{ date }` to `/api/habits/` plus the clicked habit id plus
  `/toggle`, and set the `habits` state to the same 4 rows in the same order with
  only the clicked habit replaced by the `HabitWeek` in the response body. Do not
  fetch `/api/habits` a second time.

The three cuts carry different criteria. `c-3-4` gates the route alone, since
both the 400 and the 404 branches sit above the flip and neither one writes.
`c-3-3` drives the flip twice, so an add-only or a drop-only `toggleDate` is red
on one of the two calls even with the route complete. `c-3-5` is the only
criterion that touches the board, and its request count is what separates
replacing one row in React state from refetching the whole list: a refetch makes
a second GET /api/habits and turns it red.
