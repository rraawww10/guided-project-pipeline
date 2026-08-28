# Habit Tracker

Three 40-minute sessions. Next.js 15 App Router, React 19, TypeScript, CSS
Modules. A JSON file under `data/` is the only store. No database, no API keys,
no network.

## Outcome

A weekly habit board. Screen `/` draws one row per habit and seven cells per row
for Monday to Sunday of one fixed week. A done cell is visually distinct from a
not-done cell, and each row states the habit's current streak. Clicking a cell
flips that day between done and not-done, writes the change to
`data/habits.json`, and updates that row's cell and streak. Screen
`/habits/[id]` shows the same week and streak for one habit.

The tracked week never comes from the real clock. The seed names the tracked day
as `2026-08-26`, a Wednesday, and every date in the app is derived from it, so
the same test run gives the same answer forever. The tracked week is therefore
Monday `2026-08-24` through Sunday `2026-08-30`.

Three things this teaches that the other house projects do not: date arithmetic
over `YYYY-MM-DD` strings, a grid built from two nested arrays, and a pure
streak function worth unit-testing on its own.

## Out of scope

- Creating, renaming or deleting habits. The seed file is the habit list.
- Any week other than the tracked week. There is no navigation between weeks.
- Accounts, login, or a second user's habits.
- Reminders, notifications, charts, or a monthly view.
- Per-habit target frequency. Every habit is daily.
- Reading `new Date()` anywhere in `app/` or `lib/`.

## Data model

Dates are `YYYY-MM-DD` strings everywhere: in the seed, in every API response,
and in the toggle request body. No `Date` object crosses a module boundary.

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

`data/habits.json` is the live store. `readStore()` copies the seed file over it
when it is absent, so a test can reset the world by deleting one file. Writes go
through `writeStore(store)` using node's `fs`.

The three streak cases the tests need all exist in the seed:

| habit id      | done days in the tracked week          | streak | why                                    |
|---------------|----------------------------------------|--------|----------------------------------------|
| `drink-water` | 2026-08-24, 2026-08-25, 2026-08-26     | 5      | unbroken back to Saturday 2026-08-22   |
| `read-pages`  | 2026-08-24, 2026-08-25                 | 0      | a gap: the tracked day is not done     |
| `meditate`    | none                                   | 0      | no done days at all                    |
| `stretch`     | 2026-08-26                             | 1      | the tracked day only                   |

The response type, shared by all three endpoints:

```
HabitWeek = {
  id: string
  name: string
  streak: number
  days: { date: string; done: boolean }[]   // always 7 entries, Monday first
}
```

Library modules: `lib/week.ts` exports `weekDates(trackedDay)`, the seven date
strings; `lib/streak.ts` exports `streakOf(doneDates, trackedDay)`, the streak
as a plain function over a list of done dates, counting consecutive done days
ending at the tracked day so a gap resets it to zero; `lib/toggle.ts` exports
`toggleDate(dates, date)`; `lib/store.ts` exports `readStore`, `writeStore`,
`findHabit` and `habitWeek`.

## Endpoints

| id                | method | path                          | request            | response                          | status        |
|-------------------|--------|-------------------------------|--------------------|-----------------------------------|---------------|
| `ep-habits-list`  | GET    | `/api/habits`                 | none               | `HabitWeek[]`                     | 200           |
| `ep-habit-get`    | GET    | `/api/habits/[id]`            | none               | `HabitWeek` or `{ error }`        | 200, 404      |
| `ep-habit-toggle` | POST   | `/api/habits/[id]/toggle`     | `{ date: string }` | `HabitWeek` or `{ error }`        | 200, 400, 404 |

`ep-habit-toggle` answers 404 for an unknown habit id and 400 when the body
carries no `date` string.

## Screens

Both screens are client components and both read their data from the API, so
every fetch has an owner. Class names are hashed by CSS Modules, so every
element a test reads carries a `data-testid` and the tests read those, never a
class.

**`sc-board`, route `/`** - the week board. States: loading, loaded, error.

- one element with `data-testid="habit-row"` per habit, carrying
  `data-habit-id` set to the habit id
- inside each row, `data-testid="habit-name"` with the habit name
- inside each row, `data-testid="habit-streak"` with the text
  `Streak: ` followed by the number, for example `Streak: 5`
- inside each row, seven elements with `data-testid="day-cell"`, each carrying
  `data-date` set to that column's date string and `data-done` set to `"true"`
  or `"false"`. The done styling keys off `data-done`, which is what makes the
  two states visually distinct.

**`sc-habit`, route `/habits/[id]`** - one habit. States: loading, loaded,
not-found, error.

- `data-testid="habit-name"`, `data-testid="habit-streak"`, and the same seven
  `day-cell` elements with `data-date` and `data-done`
- `data-testid="habit-missing"` when the endpoint answers 404

## Sessions

Session 1 carries the project setup - types, store, seed, the list endpoint's
scaffolding and the first screen - so it carries two cut points where sessions 2
and 3 carry three.

### Session 1 - The week board

**Goal.** Build the JSON file store, derive the fixed tracked week from the
seed, and render the board so `GET /api/habits` and screen `/` show 4 habit rows
with 7 day cells and a streak each.

**Teaches.** Deriving a fixed Monday-to-Sunday week from one date string; a pure
streak function over a list of date strings; rendering a grid from two nested
arrays.

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
  habit-row with data-habit-id drink-water, and data-done is true on data-date
  2026-08-24, 2026-08-25 and 2026-08-26 and false on the other 4 cells.
  Cuts: `cut-week-dates`.

**Cut points.**

- `cut-week-dates` in `lib/week.ts` - the week arithmetic. Hint: fill `dates`
  with the 7 `YYYY-MM-DD` strings for Monday through Sunday of the week that
  contains `trackedDay`, oldest first. Step back from `trackedDay` to that
  week's Monday and forward from there; read no clock, so the same `trackedDay`
  always gives the same 7 strings.
- `cut-streak-count` in `lib/streak.ts` - the streak itself. Hint: walk day by
  day backwards from `trackedDay` while each date is present in `doneDates`, and
  put the number of unbroken done days ending on `trackedDay` into `count`.
  Leave `count` at 0 when `trackedDay` itself is absent from `doneDates`.

The two cuts are graded apart: `c-1-2` and `c-1-5` pin the seven dates and say
nothing about streaks, while `c-1-3` and `c-1-4` pin the four streak numbers and
pass with an empty week array. Neither can be done inside the other.

### Session 2 - One habit's page

**Goal.** Add the single-habit endpoint with its 404 branch and the
`/habits/[id]` screen that shows one habit's 7 day cells and its streak.

**Teaches.** Dynamic route segments with `[id]` in the App Router; a 404 branch
in a route handler; reusing one response shape across two endpoints.

**Builds.** `ep-habit-get`, `sc-habit`.

**Acceptance criteria.**

- `c-2-1` - GET /api/habits/drink-water returns 200 with name Drink water, a
  days array of exactly 7 entries and streak 5.
  Cuts: `cut-store-find-habit`, `cut-api-habit-get`.
- `c-2-2` - GET /api/habits/no-such-habit returns 404 with a JSON body carrying
  an error key. Cuts: `cut-api-habit-get`.
- `c-2-3` - screen /habits/read-pages renders 7 elements with data-testid
  day-cell, with data-done true on data-date 2026-08-24 and 2026-08-25 and false
  on the other 5 cells. Cuts: `cut-store-find-habit`, `cut-api-habit-get`,
  `cut-habit-page`.
- `c-2-4` - screen /habits/read-pages displays a data-testid habit-name element
  whose text is exactly `Read 10 pages` and a data-testid habit-streak element
  whose text is exactly `Streak: 0`. Cuts: `cut-store-find-habit`,
  `cut-api-habit-get`, `cut-habit-page`.

**Cut points.**

- `cut-store-find-habit` in `lib/store.ts` - the lookup. Hint: inside
  `findHabit`, assign the one habit from `readStore().habits` whose `id` equals
  the `habitId` argument to `found`, and leave `found` as `null` when no habit in
  `data/habits.json` matches.
- `cut-api-habit-get` in `app/api/habits/[id]/route.ts` - the two branches.
  Hint: when `found` holds a habit, set `body` to `habitWeek(found)` and
  `status` to 200. When `found` is `null`, set `body` to an object with an
  `error` key and `status` to 404.
- `cut-habit-page` in `app/habits/[id]/page.tsx` - the single-habit render.
  Hint: map `habit.days` into one `day-cell` element per entry, each with
  `data-date` set to that entry's date string and `data-done` set to `"true"`
  only where the entry is done, and set `streakText` to `Streak: ` joined with
  `habit.streak`. Keep the existing `habit-name` element.

The three cuts are graded apart. `c-2-2` gates only the route's 404 branch, so
the route cut has a criterion the lookup does not gate. The lookup earns a
criterion the route does not share in session 3 (`c-3-2`). And `c-2-1` needs
both filled: with the lookup empty, `found` is `null`, the route answers 404,
and the 200 case is red.

### Session 3 - Toggle a day

**Goal.** Add POST /api/habits/[id]/toggle so a click on a day cell flips that
day in `data/habits.json` and refreshes only that habit's row on screen `/`.

**Teaches.** A POST route handler that reads a JSON body; writing the store back
to disk with node `fs`; replacing one item inside React array state.

**Builds.** `ep-habit-toggle`.

**Acceptance criteria.**

- `c-3-1` - POST /api/habits/stretch/toggle with body `{"date": "2026-08-25"}`
  returns 200 with streak 2 and the days entry for 2026-08-25 marked done.
  Cuts: `cut-toggle-dates`, `cut-api-toggle`.
- `c-3-2` - POST /api/habits/drink-water/toggle with body
  `{"date": "2026-08-26"}` returns 200 with streak 0, and a following
  GET /api/habits/drink-water persists streak 0 and 2 done days in the week.
  Cuts: `cut-toggle-dates`, `cut-api-toggle`, `cut-store-find-habit`.
- `c-3-3` - POST /api/habits/read-pages/toggle twice with body
  `{"date": "2026-08-26"}` returns 200 both times, streak 3 on the first
  response and streak 0 with 2 done days on the second.
  Cuts: `cut-toggle-dates`, `cut-api-toggle`.
- `c-3-4` - POST /api/habits/no-such-habit/toggle with body
  `{"date": "2026-08-26"}` returns 404, and POST /api/habits/stretch/toggle with
  body `{}` returns 400. Cuts: `cut-api-toggle`.
- `c-3-5` - clicking the day-cell with data-date 2026-08-26 in the habit-row
  with data-habit-id meditate on screen / updates that cell's data-done to true
  and that row's habit-streak text to `Streak: 1`, and leaves the drink-water
  row's habit-streak text at `Streak: 5`.
  Cuts: `cut-board-click`, `cut-api-toggle`, `cut-toggle-dates`.

**Cut points.**

- `cut-toggle-dates` in `lib/toggle.ts` - the flip. Hint: inside `toggleDate`,
  assign to `next` the `dates` list with `date` dropped when `dates` already
  contains it, and `dates` with `date` added when it does not. Every other string
  in `dates` stays in `next`, and `dates` itself is left unmutated.
- `cut-api-toggle` in `app/api/habits/[id]/toggle/route.ts` - the write path.
  Hint: read `date` from the parsed JSON body; with no `date` string set `status`
  to 400. Otherwise, when `findHabit(habitId)` gives `null` set `status` to 404,
  and when it gives a habit set its `doneDates` to
  `toggleDate(habit.doneDates, date)`, save the file with `writeStore(store)`,
  then set `body` to `habitWeek(habit)` and `status` to 200.
- `cut-board-click` in `app/page.tsx` - the click handler. Hint: inside
  `onCellClick`, POST `{ date }` to `/api/habits/` plus the clicked habit id plus
  `/toggle`, and set `habits` state to the same 4 rows in the same order with
  only the clicked habit replaced by the `HabitWeek` in the response body.

The three cuts are graded apart. `c-3-4` gates only the route, since both the
400 and the 404 branches sit above the flip. `c-3-3` drives the flip twice, so
an add-only or a remove-only `toggleDate` is red on one of the two calls even
with the route complete. `c-3-5` is the only criterion touching the board, so
the click handler stands alone.

**Reading order for a test run.** Every criterion in session 3 mutates
`data/habits.json`, so each test deletes that file first and lets `readStore()`
copy `data/habits.seed.json` back. The numbers above are all measured from the
seed state.
