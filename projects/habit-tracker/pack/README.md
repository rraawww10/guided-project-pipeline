# Habit Tracker - instructor pack

A weekly habit board. Three sessions of 40 minutes. Next.js 15 App Router,
React 19, TypeScript, CSS Modules. It runs offline: the store is one JSON file
on disk, read and written through route handlers. No database, no API keys.

**Read this first if you are teaching session 3.** Its plan comes to **47
minutes, 7 over the cap**. The trim is written out in `session-3.md` under
"This session does not fit", it costs nothing that is graded, and it takes one
minute to apply. Sessions 1 and 2 land on 40.

| Session | Title | Cuts | Plan comes to |
|---|---|---|---|
| 1 | The week board | 2 (+ all of the project setup) | 40 min |
| 2 | One habit's page | 3 | 40 min |
| 3 | Toggle a day | 3 | **47 min** - trim inside |

## What students end with

- `/` - four habit rows. Each row has the habit's name, its streak, and seven
  day cells for Monday to Sunday of one fixed week. A done cell is shaded, a
  not-done cell is not.
- Clicking a cell flips that day, writes it to `data/habits.json`, and replaces
  that one row on screen from the POST response. The board never refetches the
  whole list.
- `/habits/<id>` - the same week and the same streak for one habit, display
  only. An unknown id shows `Habit not found`.

## The one idea the whole project turns on

**No date in this app comes from the real clock.** The seed names a tracked day,
`2026-08-26`, and every date is derived from that string. So the board looks the
same today, next month and on a student's machine in another timezone.

The tracked week is therefore always Monday `2026-08-24` through Sunday
`2026-08-30`. Write those seven dates on the board at the start of session 1 and
leave them there for all three sessions. Every number in every criterion comes
from them.

This is enforced, not requested. `spec.json` declares
`"code_checks": ["utc-dates"]`, and the check reads every `.ts`/`.tsx` file and
fails the build on any local-time `Date` member (`getDay`, `getDate`,
`setDate`, `toLocaleDateString`, and that family) and on any read of the real
clock (`new Date()` with no argument, `Date.now()`). That is why the model
answers use `getUTCDay` and `setUTCDate` and nothing else. If a student asks
"why UTC" the answer is short: so the answer cannot depend on where the machine
is.

## The seed, and every number that comes out of it

`data/habits.seed.json`, copied exactly:

```json
{
  "trackedDay": "2026-08-26",
  "habits": [
    {
      "id": "drink-water",
      "name": "Drink water",
      "doneDates": ["2026-08-22", "2026-08-23", "2026-08-24", "2026-08-25", "2026-08-26"]
    },
    {
      "id": "read-pages",
      "name": "Read 10 pages",
      "doneDates": ["2026-08-24", "2026-08-25"]
    },
    {
      "id": "meditate",
      "name": "Meditate",
      "doneDates": []
    },
    {
      "id": "stretch",
      "name": "Stretch",
      "doneDates": ["2026-08-26"]
    }
  ]
}
```

| habit id | name | done days *in the week* | streak | why that streak |
|---|---|---|---|---|
| `drink-water` | Drink water | 08-24, 08-25, 08-26 | **5** | unbroken back to Saturday 08-22, which is outside the week |
| `read-pages` | Read 10 pages | 08-24, 08-25 | **0** | the tracked day itself is not done, so a gap resets it |
| `meditate` | Meditate | none | **0** | no done days at all |
| `stretch` | Stretch | 08-26 | **1** | the tracked day only |

`drink-water` showing 3 shaded cells and `Streak: 5` is the single most common
"this is broken" report in session 1. It is correct. The streak counts backwards
past Monday; the board only draws seven columns.

## Run it

```bash
cd <the copy you hand out>
npm install
npm run dev            # http://localhost:3000
```

`data/habits.json` is the live store. It does not exist in a fresh copy -
`readStore()` copies the seed over it on the first request. **Deleting it resets
the world**, even with the server running, because nothing is cached:

```bash
rm data/habits.json
```

That is your undo button for every demo in session 3. It is also in
`.gitignore`, so a student's clicks never end up in a commit.

## Running the graded suite

The suite lives in `verify/` inside the copy you hand out. It boots nothing and
installs nothing - the app must already be running, and its URL arrives in
`BASE_URL`.

Once per machine:

```bash
cd <the copy you hand out>
python3 -m venv .venv
.venv/bin/pip install pytest playwright httpx
.venv/bin/playwright install chromium     # ~150MB, once
```

Then, with `npm run dev` up in another terminal:

```bash
cd <the copy you hand out>
BASE_URL=http://localhost:3000 .venv/bin/python -m pytest verify -q
```

One test per criterion, 16 in all. Name a criterion to run one:

```bash
BASE_URL=http://localhost:3000 .venv/bin/python -m pytest \
  verify/test_api_habits.py -q -k c_1_2
```

**Two things about that command are load-bearing.**

1. `BASE_URL` has no default. The suite reads it as `os.environ["BASE_URL"]`,
   so leaving it out is a `KeyError` before any assertion runs, not a failure
   message.
2. **Run pytest from the copy's own root.** The suite finds the store as
   `os.environ.get("APP_DIR", os.getcwd())`, so a student needs no `APP_DIR` at
   all - the working directory is the answer. Run it from one directory up and
   every test that touches the store looks for `data/habits.json` in the wrong
   place. (`APP_DIR` exists for the pipeline, which runs the same suite from
   outside against two different app directories.)

**The suite deletes `data/habits.json` before and after every single test.** So
running the suite throws away whatever was clicked on screen and puts the seed
back. Tell students that before they run it in session 3, or you will spend five
minutes on "the tests undid my work".

## The shape of the project

The Next.js project root is the directory you hand out. Paths below are relative
to it.

| File | What it holds | Cuts in it |
|---|---|---|
| `data/habits.seed.json` | the immutable seed: 4 habits, `trackedDay` | none, ships written |
| `data/habits.json` | the live store, created on first read | not in the handout |
| `lib/week.ts` | `weekDates(trackedDay)` | `cut-week-dates` (s1) |
| `lib/streak.ts` | `streakOf(doneDates, trackedDay)` | `cut-streak-count` (s1) |
| `lib/store.ts` | the 3 types, `readStore`, `writeStore`, `findHabit`, `habitWeek` | `cut-store-find-habit` (s2) |
| `lib/toggle.ts` | `toggleDate(dates, date)` | `cut-toggle-dates` (s3) |
| `app/api/habits/route.ts` | `GET /api/habits` | none, ships written |
| `app/api/habits/[id]/route.ts` | `GET /api/habits/[id]` | `cut-api-habit-get` (s2) |
| `app/api/habits/[id]/toggle/route.ts` | `POST /api/habits/[id]/toggle` | `cut-api-toggle` (s3) |
| `app/page.tsx` | the board, client component | `cut-board-click` (s3) |
| `app/habits/[id]/page.tsx` | one habit, client component | `cut-habit-page` (s2) |
| `app/layout.tsx`, both `*.module.css`, `globals.css` | shell and styling | none, ship written |

8 cut points across 3 sessions: **2 / 3 / 3**. Session 1 carries two because it
also carries the whole project setup.

The types, copied from `lib/store.ts`:

```ts
export type Habit = {
  id: string
  name: string
  doneDates: string[]
}

export type Store = {
  trackedDay: string
  habits: Habit[]
}

export type HabitWeek = {
  id: string
  name: string
  streak: number
  days: { date: string; done: boolean }[]
}
```

`HabitWeek` is the response body of all three endpoints. Every non-200 body is
`{ "error": "<some non-empty message>" }`.

The types live in `lib/store.ts`, the one module that imports node's `fs`. Both
screens are client components and both need `HabitWeek`, so they import it as
`import type { HabitWeek } from '@/lib/store'`. The `type` keyword is what keeps
`fs` out of the client bundle. Drop it and the build dies with
`Module not found: Can't resolve 'fs'`.

## How the skeleton behaves

Every cut is a block **inside** a function. The `return` always sits outside the
markers, with a typed fallback above it, so **the handout compiles and runs from
minute one**. A student never faces a project that will not build.

```ts
export function weekDates(trackedDay: string): string[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let dates: string[] = []

  // TODO(cut-week-dates): ...

  return dates
}
```

Say this out loud in session 1 and repeat it at every cut: **assign to the
variable that is already there.** A student who writes `const dates = [...]`
inside the block shadows it, gets no error, and sees nothing change.

The eight fallbacks, and what each one looks like on screen:

| cut | fallback | what you see before it is filled |
|---|---|---|
| `cut-week-dates` | `dates` is `[]` | every habit's `days` is an empty array; no cells anywhere |
| `cut-streak-count` | `count` is `-1` | every row reads `Streak: -1` |
| `cut-store-find-habit` | `found` is `null` | every id looks unknown to `findHabit` |
| `cut-api-habit-get` | `status` 501, `{ "error": "not implemented" }` | `/habits/<id>` draws only the back link |
| `cut-habit-page` | `missing` false, no cells, `Streak: -1` | same - the page has no habit to draw |
| `cut-toggle-dates` | `next` is `[]` | a toggle would wipe a habit's done days |
| `cut-api-toggle` | `status` 501, `{ "error": "not implemented" }` | a click gets a 501 and the board does not move |
| `cut-board-click` | `onCellClick`'s body is empty | clicking a cell does nothing at all |

All eight markers are open in the handout from day one. Session 2's and session
3's TODO comments are visible during session 1. Say so at the start, so nobody
thinks they missed a file - and say that the criteria for later sessions are
expected red until their session.

## Where each criterion lives

16 criteria, one test each.

| Session | Criteria | Test files |
|---|---|---|
| 1 | c-1-1 .. c-1-6 | `verify/test_api_habits.py`, `verify/test_ui_board.py` |
| 2 | c-2-1 .. c-2-5 | `verify/test_api_habit.py`, `verify/test_ui_habit.py` |
| 3 | c-3-1 .. c-3-5 | `verify/test_api_toggle.py`, `verify/test_ui_board.py` |

`verify/coverage.json` maps every criterion id to its exact test node id if you
need to run one on its own.

## Files in this pack

- `session-1.md` - The week board
- `session-2.md` - One habit's page
- `session-3.md` - Toggle a day
- `troubleshooting.md` - the errors students actually hit, in session order
