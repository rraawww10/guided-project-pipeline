# Troubleshooting

Errors students actually hit on this project, in the order they hit them. Each
one is a real failure mode of this code, not a generic React problem.

## Getting started

**`npm install` prints a security advisory**
Read the message, not just the exit code. This project pins `next 15.5.24`. If
an advisory names a version you did not install, it is about a transitive
dependency and `npm install` still succeeded. If it names `next` itself, stop
and tell whoever maintains the pack.

**`npm run dev` fails with `EADDRINUSE` on 3000**
Something else is on the port. `npm run dev -- --port 3001`, and remember the
new URL - including for `BASE_URL` when you run the suite.

**The page is blank and the terminal shows a TypeScript error**
The handout compiles as shipped: every cut keeps its function's `return` outside
the markers, with a typed fallback above. So a compile error means something was
deleted that was not part of a TODO. Restore that one file from the original
handout instead of debugging it.

**`Module not found: Can't resolve 'fs'`**
`lib/store.ts` imports `node:fs`, and something imported it into a client
component as a **value**. Both screens must use
`import type { HabitWeek } from '@/lib/store'`. Drop the `type` keyword and the
bundler tries to ship node's filesystem to the browser. Only files under
`app/api/` and `lib/store.ts` itself run on the server.

**`ENOENT: no such file or directory, open '.../data/habits.json'`**
`readStore()` resolves the store as
`path.join(process.cwd(), 'data', 'habits.json')`, so the dev server must be
started from the project root - the directory that holds `package.json`. `cd`
there and restart.

**`Cannot find module './seed'` or an import that used to work**
`@/` maps to the project root via `tsconfig.json`. `@/lib/store` is correct;
`../../lib/store` from inside `app/api/habits/[id]/` also works and is easy to
get one level wrong. Prefer the `@/` form, which is what every shipped file
uses.

## Running the graded suite

**`KeyError: 'BASE_URL'`**
`BASE_URL` has no default - the suite reads it as `os.environ["BASE_URL"]`. Put
it on the command line:

```bash
BASE_URL=http://localhost:3000 .venv/bin/python -m pytest verify -q
```

**Every store-touching test fails, and the API tests fail in odd ways**
pytest was run from the wrong directory. The suite finds the store as
`os.environ.get("APP_DIR", os.getcwd())`, so **run it from the project root**,
the same directory `npm run dev` was started from. No `APP_DIR` is needed; the
working directory is the answer.

**`ModuleNotFoundError: No module named 'helpers'`**
Same cause, different symptom: `verify/conftest.py` imports `helpers` as a
top-level module, which works when pytest is pointed at the `verify` directory
from the project root. Use `python -m pytest verify -q`, not
`pytest verify/test_api_habits.py` from inside `verify/`.

**`playwright._impl._api_types.Error: Executable doesn't exist`**
The chromium download never ran. `.venv/bin/playwright install chromium`, once
per machine, about 150MB.

**Every UI test times out after 20 seconds and the API tests pass**
The app is up but the browser cannot reach it. Check the port in `BASE_URL`
matches the port `npm run dev` printed.

**All 16 tests fail with a connection error**
Nothing is running. The suite boots nothing on purpose - start the app first, in
another terminal.

**"The tests undid my work"**
They did, deliberately. The suite deletes `data/habits.json` before **and** after
every single test, so each test starts from the seed. Whatever was clicked on
screen is gone. Click it again, or stop running the suite mid-demo.

**The suite passes locally and fails on a colleague's machine, on dates only**
A local-time `Date` accessor got into `lib/week.ts` or `lib/streak.ts`. It works
in some timezones and not others. The `utc-dates` static check exists precisely
because no test suite can catch this - the fix is `getUTCDay`, `getUTCDate`,
`setUTCDate`, and `Date` objects built only as `new Date(day + 'T00:00:00.000Z')`.

## Session 1 - the week and the streak

**Every row reads `Streak: -1`**
Shipped behaviour before `cut-streak-count` is filled. `count` starts at `-1` on
purpose so a missing implementation is visible from across the room. Not a bug.

**No day cells anywhere, and `/api/habits` shows `days: []`**
Shipped behaviour before `cut-week-dates` is filled. `dates` starts as an empty
array, so `habitWeek` maps over nothing.

**Filled the TODO in and nothing changed**
They declared a new variable inside the block - `const dates = ...`, `let count
= 0` - which shadows the one the `return` below reads. Look for `const` or `let`
at the start of the line that should be a bare assignment. No error is raised,
which is why this eats five minutes.

**`days[].date` values look like `2026-08-24T00:00:00.000Z`**
`Date` objects were pushed into `dates` instead of strings, and JSON serialised
them. Every date crosses a boundary as `YYYY-MM-DD`; use the `isoDay` helper
that is already at the top of the file.

**The week is right for the seed and a week off when `trackedDay` is a Sunday**
`getUTCDay()` was used without the shift. `getUTCDay` is 0 on Sunday, so
`getUTCDay() - 1` gives `-1` and steps *forward*. The fix is
`(getUTCDay() + 6) % 7`, which makes Monday 0 and Sunday 6. This is exactly what
`c-1-6` catches.

**`c-1-2` green, `c-1-6` red**
The seven dates were hardcoded. They are printed in `c-1-2` and on the whiteboard,
so a literal array passes four criteria. `c-1-6` moves `trackedDay` twice and is
the criterion that requires actual arithmetic.

**The month boundary looks wrong for `2026-09-06`**
It should be `2026-08-31` through `2026-09-06`. If they wrote month handling by
hand, delete it. `setUTCDate` rolls over: `setUTCDate(0)` is the last day of the
previous month.

**`Streak: 4` on drink-water**
The loop is right and `count` was never reset from its `-1` fallback. `count = 0`
goes before the `while`.

**"drink-water shows 3 shaded cells but says `Streak: 5` - that's wrong"**
It is right. The seed marks `2026-08-22` and `2026-08-23` done as well, and
those are before the tracked week. The streak counts the habit's whole history;
the board draws seven columns. Expect this question every single time.

**`read-pages` says `Streak: 0` with two cells shaded**
Also right. `2026-08-26` is the tracked day and it is not done, so the walk
backwards stops immediately.

**Someone wants `new Date()` for "today"**
There is no today in this app. Every date derives from `trackedDay`, and the
`utc-dates` code check fails the build on a zero-argument `new Date()` or
`Date.now()` anywhere in the project.

**The board is empty but `/api/habits` looks perfect**
Hard refresh. Next's dev server sometimes serves a stale client bundle right
after a fast edit.

## Session 2 - one habit's page

**`/api/habits/drink-water` still returns 501**
The wrong file was edited. `app/api/habits/route.ts` is the list and ships
written; `app/api/habits/[id]/route.ts` is the one with the cut. The editor tabs
both read `route.ts`.

**The route returns 200 with `{"error":"not implemented"}`**
`status` was set in a branch and `body` was not, or the reverse. Both variables,
in both branches.

**A TypeScript error on `params`, or `params.id` is `undefined`**
`params` is a `Promise` in Next 15. `const { id: habitId } = await params` ships
written above the marker; if it was changed to `params.id`, put it back.

**404 for every id, including real ones**
`cut-store-find-habit` is still open, so `found` stays at its `null` fallback and
every lookup misses. The symptom is in the route; the cause is in `lib/store.ts`.

**`find` returns `undefined` and TypeScript complains about the return type**
`findHabit` is declared `Habit | null`. `?? null` converts `undefined` to `null`,
so callers have one missing value to check instead of two.

**`c-2-1` green, `c-2-3` red**
The endpoint works and the page does not. Prove the endpoint in a browser tab
first - it stops the "nothing works" spiral - then look at
`app/habits/[id]/page.tsx`.

**Blank page, console says `Cannot read properties of null (reading 'days')`**
The `habit !== null` guard is missing. A client component renders once before its
data arrives, every time, and on that render `habit` is `null`. The shape is
`if (status === 404) { ... } else if (habit !== null) { ... }`.

**`Habit not found` shows for a habit that exists**
They wrote `if (status !== 200)` or `if (habit === null)` instead of
`if (status === 404)`. On the first render `status` is `null`, which is not 200,
so `missing` goes true before the fetch has answered. Only a literal 404 sets
`missing`.

**A real habit's page shows `Streak: -1`**
`streakText` was never assigned - only the cells were built.

**Seven cells on screen but the test counts one**
`data-testid="day-cell"` went on the wrapping `<div className={styles.days}>`
instead of on each element inside the map.

**The cells all look the same, done or not**
They styled with a class name instead of the attribute. CSS Modules hashes class
names; the shipped rule is `.cell[data-done='true']` and the tests read
`data-done` too. Set it to the exact strings `'true'` and `'false'`.

**`Each child in a list should have a unique "key" prop`**
`key={day.date}` was dropped from the mapped element. The dates are unique.

**Changing the id in the address bar does not change the page**
`habitId` was removed from the `useEffect` dependency array. It ships as
`[habitId]`.

**`/habits/no-such-habit` returns a 500 page instead of `Habit not found`**
Something in the block ran before the guard - usually `habit.days.map` outside
the `else if`. The 404 branch must not touch `habit`.

**The cells on `/habits/<id>` do not respond to clicks**
Correct. That screen is display only, by design - `/` is the only screen that
writes. Its cells are `<div>`s; the board's are `<button>`s.

## Session 3 - toggle a day

**Clicking a cell does nothing and the network tab shows no request**
`cut-board-click` is still open (its shipped body is empty), the file is not
saved, or the fetch was written without being reached. No request at all points
at the handler body, not at the server.

**The POST returns 501**
`cut-api-toggle` is still open. Filling the click handler first is the natural
order and the wrong one.

**The whole board vanishes after one click; console says `Cannot read
properties of undefined (reading 'map')`**
The most common failure of session 3. A non-200 response body -
`{"error":"not implemented"}` from the unfilled route - was put into `habits`
state, so one "row" has no `days` and the next render dies. Two fixes, both
needed: keep the `if (response.ok)` guard, and finish the route first.

**The POST returns 400 on a date that is plainly in the week**
The request went out wrong. In the network tab's request payload, check that the
method is `POST`, that the body is `JSON.stringify({ date })` and not the bare
object, and that the key is spelled `date`. A bare object becomes
`[object Object]` on the wire and `request.json()` throws.

**A 500 instead of a 400 on a malformed body**
The `.catch(() => null)` was removed from `await request.json()`, or a second
`await request.json()` was added inside the block. The body is read once, for
you, above the marker; reading a request body twice is a stream error.

**404 where a 400 was expected, or the reverse**
The two checks are in the wrong order. The date is validated **first**, so a bad
date with a bad id is a 400. `c-3-4` asserts exactly that.

**Every date is rejected with a 400**
`week.includes(date)` is being asked about the wrong list, or `cut-week-dates`
regressed and `weekDates` returns an empty array - in which case nothing can ever
be a member. Check `/api/habits` still shows seven dates.

**A `date` that is not in the seed's week is accepted**
The seven dates were hardcoded in the route rather than taken from
`weekDates(store.trackedDay)`. The spec forbids the hardcoded list precisely so
there is one definition of the week.

**The POST returns 200, the file changes, and the screen does not move**
The React array was mutated in place: `habits[i] = updated; setHabits(habits)`.
React compares with `===`, sees the same array, and does not re-render. Use
`current.map(...)`, which always builds a new array.

**All four rows change, or three rows go blank**
The `map` callback is missing its else branch and returns `undefined` for the
rows that do not match. It must be `habit.id === habitId ? updated : habit`.

**The clicked row moves to the bottom of the board**
The habit was removed and the new one appended. `map` replaces in place and
keeps the order.

**The cell shades and then un-shades a moment later**
A refetch of `/api/habits` raced the POST response. Delete the refetch - the
POST response body is the new row.

**`c-3-5` is red but the board looks perfect**
Almost always a second GET `/api/habits`. `c-3-5` counts every GET to that path
from page load to the end of the click and requires exactly 1. Count them in the
network tab.

**`c-3-4` is red on the byte-for-byte comparison and everything else is green**
Something writes on an error path. There must be exactly one `writeStore(store)`
call and it must be inside the innermost `else`. A call placed after the whole
`if/else` runs on all three branches.

**Toggling the same day twice leaves it done**
`toggleDate` only adds. `c-3-3` posts the same date twice and is the criterion
that catches it. Fix `lib/toggle.ts`, not the route.

**Toggling once wipes a habit's whole history**
`next` was left at its empty-array fallback, or `filter` was written with the
comparison inverted (`candidate === date` keeps only the date being removed).

**The response streak is the value from before the click**
`body = habitWeek(...)` was built before `habit.doneDates` was reassigned. The
order is: flip, `writeStore(store)`, then build the body.

**The change is in the response but gone after a reload**
`writeStore(store)` was never called, or a copy of the habit was modified rather
than the element `findHabit` returned. `findHabit` gives back an element of the
store, so mutating it and saving the store persists it.

**"My clicks disappeared"**
The test suite was run. It deletes `data/habits.json` around every test.

**The board shows yesterday's demo data**
`rm data/habits.json` and reload. `readStore()` re-copies the seed on the next
request, with the server still running.

## Anything, at any time

**Reset the world**

```bash
rm data/habits.json          # from the project root; the next request re-seeds
```

**Prove the server half before the screen half**
Every screen in this project reads only from the API. So there are exactly two
places a value can be wrong, and one browser tab tells you which: paste
`/api/habits`, `/api/habits/<id>`, or `curl` the toggle route. Students who
check the endpoint first fix things in one minute; students who stare at JSX
lose ten.

**Find the test that grades a criterion**
`verify/coverage.json` maps every criterion id to its exact test node id. Or run
one by name:

```bash
BASE_URL=http://localhost:3000 .venv/bin/python -m pytest verify -q -k c_3_4
```
