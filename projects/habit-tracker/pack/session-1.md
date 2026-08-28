# Session 1 - The week board

**Time:** 40 minutes
**Students start from:** the handout, running. `/` shows the title, the line
"The tracked week, Monday to Sunday", and four rows - each with a habit name,
the text `Streak: -1`, and no day cells at all. `GET /api/habits` answers 200
with four habits whose `days` arrays are empty.
**Students end with:** `/` showing four rows, seven day cells in each, three
shaded cells in the `drink-water` row, and `Streak: 5` on it. `c-1-1` through
`c-1-6` green.

## What they learn

1. The store: one JSON file, read on every request, re-seeded when deleted.
2. Why no date in this app comes from the clock, and what `trackedDay` is.
3. Deriving a fixed Monday-to-Sunday week from one `YYYY-MM-DD` string, with
   UTC accessors only.
4. A pure function - `streakOf` reads no file and no clock, so it can be
   reasoned about on paper.
5. Reading a graded criterion, and where the test that grades it lives.

## Before you start

- **Students must have run `npm install` before the session.** It is 1-3
  minutes on a good connection and much worse on a room full of laptops on
  shared wifi. There is no slack in this plan for it.
- `npm run dev` up, `/` open in a browser, and a second tab on
  `/api/habits`. Have the JSON viewer expanded.
- These seven dates on the board, and leave them up for all three sessions:
  `2026-08-24 25 26 27 28 29 30`, labelled Mon to Sun. Circle `2026-08-26` and
  label it "the tracked day, a Wednesday".
- `data/habits.seed.json` open in the editor.
- Know your undo: `rm data/habits.json`.

## The plan

| Minutes | What you do |
|---|---|
| 0-5 | What we are building. Show the finished board on your own screen for 30 seconds, then close it. Run their handout: four rows, `Streak: -1`, no cells. Name the two things missing and say they are today's work. |
| 5-10 | The tree and the seed. Open `data/habits.seed.json`, read `trackedDay` out loud, and say the rule: **no date comes from the clock**. Point at the seven dates on the board and say they follow from that one string. Then the file map: `lib/` has the logic, `app/api/` has the endpoints, `app/page.tsx` is the board. Note that all eight TODO markers are already in the tree and only two are today's. |
| 10-13 | `/api/habits` in the other tab. Four habits, `days: []`, `streak: -1`. Open `lib/week.ts` and `lib/streak.ts` side by side and show the fallback-above, return-below shape. Say the rule: **assign to the variable that is already there**. |
| 13-26 | `cut-week-dates` live in `lib/week.ts`. Then refresh `/api/habits` and see the seven dates, and refresh `/` and see 28 cells appear. |
| 26-34 | `cut-streak-count` live in `lib/streak.ts`. Refresh `/`: 5, 0, 0, 1. Handle the "why 5" question here, not later. |
| 34-38 | Students catch up. Circulate. Anyone who is done runs the suite and should see c-1-1 to c-1-6 green and the other ten red. |
| 38-40 | What runs now: the board is complete and read-only. Next session: one habit gets its own page, and it can be missing. |

## Cut points in this session

### cut-week-dates - `lib/week.ts`:29

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-week-dates): Fill `dates` with the 7 `YYYY-MM-DD` strings for Monday through Sunday of the week that contains `trackedDay`, oldest first. Step back from `trackedDay` to that week's Monday and forward from there, and use the UTC accessors (`getUTCDay`, `setUTCDate`) or plain string arithmetic so the 7 strings do not change with the machine's timezone. Read no clock: the same `trackedDay` always gives the same 7 strings.
  ```

- **What they write:** find how many days `trackedDay` sits after its Monday,
  step a `Date` back by that many days, then push seven `YYYY-MM-DD` strings
  from that Monday forward. Assign the result into `dates`. Two helpers are
  already written above the marker and they should use both.

- **The two helpers, already in the file:**

  ```ts
  /** Midnight UTC on a `YYYY-MM-DD` string. */
  function utcDate(day: string): Date {
    return new Date(`${day}T00:00:00.000Z`)
  }

  /** A `Date` back as a `YYYY-MM-DD` string. */
  function isoDay(date: Date): string {
    return date.toISOString().slice(0, 10)
  }
  ```

  Teach these first, in one minute. `utcDate` is the only way a `Date` is ever
  built in this project - always from a string, always with the `Z`. `isoDay`
  is the only way one is ever read back. In between, only UTC accessors.

- **Teach it like this:** "`getUTCDay` numbers the days with Sunday as 0 and
  Saturday as 6. We want Monday as 0. Add 6 and take the remainder by 7 - that
  slides the whole scale round by one day, and Sunday's 0 becomes 6, which is
  exactly right because Sunday is the *last* day of our week, six days after its
  Monday. Now subtract that many days and you are standing on Monday. Then walk
  forward seven times."

  Do the two cases on the board before anyone types:

  | trackedDay | `getUTCDay()` | `(day + 6) % 7` | Monday |
  |---|---|---|---|
  | 2026-08-26, Wednesday | 3 | 2 | 2026-08-24 |
  | 2026-08-30, Sunday | 0 | 6 | 2026-08-24 |

  Then say what the naive version does: `getUTCDay() - 1` gives 2 for Wednesday
  and works, and gives `-1` for Sunday, which steps *forward* a day and lands on
  2026-08-31. That is a whole week wrong, and `c-1-6` is the criterion that
  catches it.

- **The model answer** (copied from `app/lib/week.ts`):

  ```ts
  const tracked = utcDate(trackedDay)
  // getUTCDay is 0 on Sunday, so shifting by 6 makes Monday 0 and Sunday 6
  const sinceMonday = (tracked.getUTCDay() + 6) % 7
  const monday = utcDate(trackedDay)
  monday.setUTCDate(tracked.getUTCDate() - sinceMonday)

  dates = []
  for (let offset = 0; offset < 7; offset += 1) {
    const cell = utcDate(isoDay(monday))
    cell.setUTCDate(monday.getUTCDate() + offset)
    dates.push(isoDay(cell))
  }
  ```

- **Two details worth naming while you type them.**
  - `setUTCDate` handles month and year rollover for you. `monday` for the week
    of `2026-09-06` comes out as `2026-08-31` with no special case, because
    `setUTCDate(6 - 6)` is `setUTCDate(0)`, which means "the last day of the
    previous month". Nobody writes month arithmetic in this project.
  - `const monday = utcDate(trackedDay)` builds a *second* `Date`, and the loop
    builds a fresh `cell` from `isoDay(monday)` every time. `setUTCDate` mutates
    the object it is called on, so reusing one `Date` and stepping it seven times
    also works - but only if you never read it twice. Building fresh is the
    version you can explain in ten seconds.

- **Passes when:** `c-1-1`, `c-1-2`, `c-1-5` and `c-1-6` go green. `c-1-6` is
  the one to point at: it rewrites `data/habits.json` with `trackedDay` set to
  `2026-08-30` and then to `2026-09-06` and checks the seven strings each time.
  A hardcoded array of the seven dates in `c-1-2` passes four criteria and fails
  that one. Say that out loud before anyone is tempted.

### cut-streak-count - `lib/streak.ts`:28

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-streak-count): Walk day by day backwards from `trackedDay` while each date is present in `doneDates`, and put the number of unbroken done days ending on `trackedDay` into `count`. Step with the UTC accessors or plain string arithmetic so the answer does not change with the machine's timezone, and leave `count` at 0 when `trackedDay` itself is absent from `doneDates`.
  ```

- **What they write:** put `doneDates` in a `Set`, start a cursor on
  `trackedDay`, and while the cursor's date string is in the set, add one and
  step the cursor back a day. Assign the total into `count`. The same two
  helpers, `utcDate` and `isoDay`, are already at the top of this file too.

- **Teach it like this:** "Start on the tracked day and walk backwards while
  every day you land on is done. The moment you land on a day that is not done,
  stop. So the very first check does the whole job of the 'a gap resets it' rule:
  if the tracked day itself is not done, the loop body never runs and the answer
  is 0. `read-pages` and `meditate` both come out 0 that way, for two completely
  different reasons."

- **The model answer** (copied from `app/lib/streak.ts`):

  ```ts
  const done = new Set(doneDates)
  const cursor = utcDate(trackedDay)

  count = 0
  while (done.has(isoDay(cursor))) {
    count += 1
    cursor.setUTCDate(cursor.getUTCDate() - 1)
  }
  ```

- **`count = 0` before the loop is not decoration.** The fallback above the
  marker is `let count = -1`, deliberately, so that a student who never touches
  it sees `Streak: -1` on screen and knows something is missing. If they write
  the loop but forget to reset `count`, every streak is one less than it should
  be and `drink-water` reads `Streak: 4`. That is a five-second fix and a very
  common one.

- **Why `drink-water` is 5 and not 3.** Ask the room before you tell them. The
  seed has it done on `08-22` and `08-23` as well, which are the Saturday and
  Sunday *before* the tracked week. The streak is a property of the habit's
  whole history; the board only draws seven columns. The screen showing three
  shaded cells and `Streak: 5` is correct, and it is the single most reported
  "bug" of this session.

- **Passes when:** `c-1-3` and `c-1-4` go green. `c-1-3` checks the four numbers
  at the endpoint - 5, 0, 0, 1. `c-1-4` reads the text `Streak: 5` on screen in
  the `drink-water` row.

## Handed over complete, and worth two minutes

The board's JSX in `app/page.tsx` ships written. Students write no JSX today -
their first JSX is session 2's cell map. Read this out to them once, because
session 2 asks them to write something with the same shape (copied from
`app/app/page.tsx`):

```tsx
<div className={styles.days}>
  {habit.days.map((day) => (
    <button
      key={day.date}
      type="button"
      className={styles.cell}
      data-testid="day-cell"
      data-date={day.date}
      data-done={day.done ? 'true' : 'false'}
      onClick={() => {
        void onCellClick(habit.id, day.date)
      }}
    >
      {day.date.slice(8)}
    </button>
  ))}
</div>
```

Three things to point at:

- Two nested maps: habits on the outside, that habit's seven days on the inside.
  That is the whole grid.
- `data-done` is the **string** `'true'` or the string `'false'`, never a
  boolean. The CSS shades a cell with the selector
  `.cell[data-done='true']`, and every test reads that attribute. Class names
  are hashed by CSS Modules, so `data-*` and `data-testid` are the only stable
  hooks in this project.
- `{day.date.slice(8)}` is why a cell reads `24` and not `2026-08-24`. It is the
  last two characters of the date string.

`onCellClick` is already wired to every cell and its body is empty. Clicking
does nothing until session 3. Say so, or someone will click for ten minutes.

## Where students get stuck

- **"Nothing changed after I filled it in"** - they wrote `const dates = [...]`
  or `let count = 0` inside the block, shadowing the variable the `return`
  below reads. No error, no change. Look for `const` or `let` on the line that
  should be a bare assignment.
- **`/api/habits` still shows `days: []` after a correct-looking week function**
  - they pushed `Date` objects instead of strings, and `JSON.stringify` turned
  them into full ISO timestamps. Every date crosses a boundary as
  `YYYY-MM-DD`; `isoDay` is right there.
- **The week is right for Wednesday and a week off for Sunday** - `getUTCDay()`
  used without the `+ 6) % 7` shift. This is `c-1-6` and it is the point of that
  criterion.
- **Every date is one day early or one day late** - a local-time accessor got
  in, usually `getDate`/`setDate` instead of `getUTCDate`/`setUTCDate`. It will
  look fine in some timezones and wrong in others, and the `utc-dates` code
  check refuses it outright.
- **`Streak: 4` on drink-water** - the loop is right and `count` was never reset
  from its `-1` fallback.
- **`Streak: 5` "should be 3"** - it should not. See above. Have the two
  out-of-week dates in the seed ready to point at.
- **Someone reaches for `new Date()`** - the whole design says no. There is no
  today in this app. The static check fails the build on it, so this is not a
  style preference.
- **`ENOENT ... data/habits.json`** - they are running `npm run dev` from the
  wrong directory. `readStore()` resolves the store through `process.cwd()`, so
  the server must be started from the project root, the directory with
  `package.json` in it.
- **The board is empty but `/api/habits` looks perfect** - hard refresh. Next's
  dev server occasionally serves a stale client bundle after a fast edit.

## Check before moving on

`/` shows four rows. The `drink-water` row shows `Streak: 5` and three shaded
cells out of seven. `/api/habits` shows the seven dates `2026-08-24` through
`2026-08-30` in that order for every habit.

`c-1-1` through `c-1-6` green, ten reds below them. Session 2 needs
`weekDates` and `streakOf` both working, because every response it builds runs
through both.
