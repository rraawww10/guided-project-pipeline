# Session 3 - Toggle a day

**Time:** the plan below comes to **47 minutes, 7 over the cap.** Read "This
session does not fit" first and decide which trim you are taking before class.
**Students start from:** both screens complete and read-only. Clicking a day
cell on `/` does nothing. `POST /api/habits/stretch/toggle` answers **501** with
`{"error":"not implemented"}`.
**Students end with:** clicking a cell on `/` shades it, moves that row's
streak, writes the change into `data/habits.json`, and leaves the other three
rows alone. A reload shows the same board. `c-3-1` through `c-3-5` green - 16 of
16.

## This session does not fit

The plan is 47 minutes. Two trims get it to 40, and neither one touches
anything graded:

1. **Drop the standalone `writeStore` read-along** (the 10-13 block, 3 minutes)
   and say its one sentence while you type `writeStore(store)` inside
   `cut-api-toggle` instead. The students never edit that function, so a
   dedicated block buys them nothing.
2. **Demo one 400, not four** (the 28-33 block, from 5 minutes to 2). Show the
   `{}` body getting a 400, then say "there are four error requests and `c-3-4`
   makes all four - run it and read the failure if one is wrong". The suite is a
   better demo of that criterion than you are.
3. **Recap in 3 minutes, not 4.**

That is 7 minutes. The trimmed table is at the bottom of the plan section.

**Why it overruns, for whoever owns the spec.** `cut-api-toggle` is the largest
cut in the project - 20 lines, three branches, and an ordering rule between two
of them - and it lands in the same 40 minutes as two other cuts plus a declared
concept (`writing the store back to disk with node fs`) that the student never
actually writes a line of. Session 1 carries the whole project setup and only
two cuts, which was the right call; session 3 is where the third cut should have
been dropped or the toggle route split in two.

## What they learn

1. A POST route handler: reading a JSON body, and never trusting it.
2. Validating input before doing anything with it, and why the *order* of the
   two checks is a decision.
3. Three status codes out of one handler: 200, 400, 404.
4. Writing to disk with node `fs` - read-along, in `lib/store.ts`. Their own
   line is the `writeStore(store)` call.
5. A pure toggle function that returns a new array instead of editing the one it
   was handed.
6. Replacing one item inside React array state, and why a new array is the whole
   trick.

## Before you start

- Session 2 finished and green. The toggle route calls `findHabit` and
  `weekDates`; both must work.
- `npm run dev` up, `/` open, and the browser's network tab open and filtered to
  `Fetch/XHR`. You will use it twice, and it is where `c-3-5` is won or lost.
- A terminal for `curl`, and `data/habits.json` open in the editor so students
  can watch the file change.
- **Know the reset**: `rm data/habits.json`. Use it between demos. Also warn
  them, before anyone runs the suite: **the suite deletes `data/habits.json`
  before and after every test**, so running it throws away whatever they
  clicked. That is by design and it is not a bug in their code.
- The four numbers of today's demos, on the board:

  | request | streak in the response | why |
  |---|---|---|
  | `stretch` + `2026-08-25` | 2 | adds the day before the tracked day, so 26 then 25 |
  | `drink-water` + `2026-08-26` | 0 | removes the tracked day, so the streak breaks at once |
  | `read-pages` + `2026-08-26` | 3 | fills the gap: 26, 25, 24 |
  | the same request again | 0 | removes it again, back to the seed |

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap: two screens that read. Today one thing writes. Click a cell on `/` - nothing. Open the network tab, click again - no request at all, because `onCellClick`'s body is empty. Then say the shape of the day: one pure function, one route with three answers, one click handler. |
| 4-10 | `cut-toggle-dates` in `lib/toggle.ts`. Three lines. Do it on paper first: `["a","b"]` toggle `"b"` and `["a","b"]` toggle `"c"`. |
| 10-13 | Read along in `lib/store.ts`: `readStore` and `writeStore`, the two `fs` calls in the whole project. Nobody edits this file today. |
| 13-28 | `cut-api-toggle`. Build it in the order the code runs: parse, validate the date, look up the habit, flip, write, respond. Prove the 200 with `curl` and watch `data/habits.json` change in the editor. |
| 28-33 | The error branches. Four requests, four `curl`s: an unknown id, `{}`, `not-a-date`, and `2026-08-31`. Then the invariant: an error writes nothing at all. |
| 33-42 | `cut-board-click`. Network tab open the whole time. Click a cell, watch exactly one POST go out and exactly one row change. |
| 42-45 | Students catch up. Circulate. Run the full suite - all 16. |
| 45-47 | What runs now: the whole project. Where it would go next: more habits, more weeks, a real database behind the same three endpoints. |

**The trimmed 40-minute table:**

| Minutes | What you do |
|---|---|
| 0-3 | Recap. Click a cell, no request, empty handler. Name the three pieces. |
| 3-9 | `cut-toggle-dates`, on paper then in the file. |
| 9-25 | `cut-api-toggle`, including the one sentence about `writeStore` and node `fs` as you type that line. Prove the 200 with `curl`. |
| 25-27 | One 400: body `{}`. Say the other three are in `c-3-4` and move on. |
| 27-36 | `cut-board-click`, network tab open. |
| 36-39 | Students catch up. Circulate. Run the suite. |
| 39-40 | What runs now, and where it would go next. |

## Cut points in this session

### cut-toggle-dates - `lib/toggle.ts`:12

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-toggle-dates): Inside `toggleDate`, assign to `next` a new array holding `dates` with every occurrence of `date` dropped when `dates` already contains it, and `dates` with `date` added when it does not. Every other string in `dates` stays in `next`, and `dates` itself is left unmutated.
  ```

- **What they write:** one conditional. If the array already contains the date,
  `next` is the array with that date filtered out; if it does not, `next` is the
  array with that date appended. Either way `next` is a **new** array.

- **Teach it like this:** do it on the whiteboard before anyone types. "Toggle
  is two operations wearing one name. Ask the array one question - is the date
  already in you? - and the answer picks which of the two you do. `filter` to
  remove, spread-and-append to add. Neither one touches the original array; both
  build a new one."

- **The model answer** (copied from `app/lib/toggle.ts`):

  ```ts
  next = dates.includes(date)
    ? dates.filter((candidate) => candidate !== date)
    : [...dates, date]
  ```

- **"Left unmutated" is a rule the tests cannot see, so say why it matters.**
  `push` and `splice` would also pass every criterion in this session, because
  the caller assigns the result straight back over `habit.doneDates` and the
  mutated array is the same array. Be honest about that and give the reason
  anyway: this function is the one piece of today's code that has no store, no
  request and no React in it, so it is the one piece you can test on paper. A
  function that edits its argument cannot be reasoned about without knowing who
  else is holding that argument. Session 3's last cut is a React state update
  where the same mistake **does** break the app visibly - so this is the cheap
  place to build the habit.

- **The order of the added date does not matter.** `doneDates` is a set of days
  that happens to be stored as an array. `streakOf` puts it into a `Set` on its
  first line, and `habitWeek` does the same. Appending is simplest; sorting would
  be harmless and is not asked for.

- **Duplicates cannot happen.** The date is added only when `includes` says it
  is absent, and the seed has none. Worth one sentence, because someone will ask
  what happens if a date is in there twice.

- **Passes when:** nothing on its own. It is named by `c-3-1`, `c-3-2`, `c-3-3`
  and `c-3-5`, and every one of those also needs the route. `c-3-3` is the
  criterion that specifically punishes doing only half the job: it posts the same
  date twice and expects streak 3 then streak 0, so an add-only or a remove-only
  version is red on one of the two calls.

### Read along: the two `fs` calls - `lib/store.ts`

Three minutes, no typing. This is one of the three concepts the session
declares, and the student writes none of it - what they write is the
`writeStore(store)` call inside the next cut. Say that plainly rather than
pretending otherwise.

Copied from `app/lib/store.ts`:

```ts
/** The live store and the immutable seed, both inside the running app. */
function storePath(): string {
  return path.join(process.cwd(), 'data', 'habits.json')
}

function seedPath(): string {
  return path.join(process.cwd(), 'data', 'habits.seed.json')
}

export function readStore(): Store {
  if (!fs.existsSync(storePath())) {
    fs.copyFileSync(seedPath(), storePath())
  }

  return JSON.parse(fs.readFileSync(storePath(), 'utf8')) as Store
}

/** Write the whole store back to disk. */
export function writeStore(store: Store): void {
  fs.writeFileSync(storePath(), JSON.stringify(store, null, 2) + '\n', 'utf8')
}
```

Four things to name, one sentence each:

- `process.cwd()` is the directory `npm run dev` was started from. That is why
  the server has to be started from the project root.
- `readStore` copies the seed over the live store when the live store is
  missing. So deleting `data/habits.json` resets the whole world, even with the
  server running. Do it live and refresh the board.
- Nothing is cached. Every call re-reads and re-parses the file. That is slow and
  completely fine for four habits, and it is why the file in the editor and the
  screen in the browser never disagree.
- `writeStore` writes the **whole** store, not a patch. One `writeFileSync`, the
  whole object, pretty-printed. So a caller mutates the object it read and hands
  the same object back.

Then link it to session 2: "`findHabit` gives you an element of that store, not
a copy. So changing the habit you found and then calling `writeStore(store)`
saves it. That is the entire write path, and you are about to use it."

### cut-api-toggle - `app/api/habits/[id]/toggle/route.ts`:29

This is the big one. Budget 15 minutes and build it in the order the code runs.

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-api-toggle): Read `date` from the parsed JSON body and read the store with `readStore()` into `store`. When `date` is not one of the 7 strings from `weekDates(store.trackedDay)`, set `status` to 400 and `body` to an object with an `error` key, and write nothing to disk. Otherwise call `findHabit(store, habitId)`: on `null` set `status` to 404 and `body` to an object with an `error` key, and write nothing to disk; on a habit set that habit's `doneDates` to `toggleDate(habit.doneDates, date)`, persist the whole `store` with `writeStore(store)`, then set `body` to `habitWeek(habit, store.trackedDay)` and `status` to 200.
  ```

- **What they write:** pull `date` off the parsed payload; read the store; build
  the week; reject anything that is not a string in that week with a 400; then
  look the habit up and reject a miss with a 404; otherwise flip, write, and
  answer with the fresh `HabitWeek`. Set the same `body` and `status` variables
  in all three branches.

- **The frame, already in the file** (copied from `app/`):

  ```ts
  export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> },
  ): Promise<Response> {
    const { id: habitId } = await params
    const payload = (await request.json().catch(() => null)) as { date?: unknown } | null

    // the fallback stays above the marker and the return below it, so the
    // skeleton still compiles
    let body: HabitWeek | { error: string } = { error: 'not implemented' }
    let status = 501
  ```

  Read the `payload` line out loud - it is the most interesting line in the file
  and they do not have to write it:

  - `await request.json()` is how a route handler reads a POST body, and it
    **throws** on a body that is not valid JSON.
  - `.catch(() => null)` turns that throw into `null`, so a garbage body becomes
    a 400 rather than a 500.
  - The type is `{ date?: unknown }`, not `{ date: string }`. Say why: "this
    value came off the network. Nobody has checked it. Typing it as a string
    would be a lie the compiler then believes, and every check below it would be
    pointless."

- **Teach the validation order as a decision, not a detail.** "We check the date
  *before* we look up the habit. So a request with a bad id **and** a bad date
  gets a 400, not a 404. Either would be defensible; what is not defensible is
  not knowing which one your code does. Pick the order, write it down, and the
  tests can hold you to it." `c-3-4` holds you to it: it posts
  `{"date": "not-a-date"}` and expects a 400 even when the id is fine, and posts
  a valid date to `no-such-habit` and expects 404.

- **The one source of truth for the seven dates.** The route validates against
  `weekDates(store.trackedDay)`, derived from the store it just read - never
  against a hardcoded list. Say the reason: "if someone edits `trackedDay` in
  the file, the valid dates move with it, and nothing else has to change. A
  hardcoded array is a second definition of the week that will drift from the
  first one."

- **The model answer** (copied from
  `app/app/api/habits/[id]/toggle/route.ts`):

  ```ts
  const date = payload === null ? undefined : payload.date
  const store: Store = readStore()
  const week = weekDates(store.trackedDay)

  if (typeof date !== 'string' || !week.includes(date)) {
    body = { error: 'date must be one of the seven days of the tracked week' }
    status = 400
  } else {
    const habit = findHabit(store, habitId)

    if (habit === null) {
      body = { error: `no habit with the id ${habitId}` }
      status = 404
    } else {
      habit.doneDates = toggleDate(habit.doneDates, date)
      writeStore(store)
      body = habitWeek(habit, store.trackedDay)
      status = 200
    }
  }
  ```

- **`typeof date !== 'string' || !week.includes(date)` is one check doing three
  jobs.** Walk the four rejected bodies against it out loud:

  | body | `date` is | which half rejects it |
  |---|---|---|
  | `{}` | `undefined` | `typeof` |
  | `{"date": 5}` | a number | `typeof` |
  | `{"date": "not-a-date"}` | a string, not in the week | `includes` |
  | `{"date": "2026-08-31"}` | a real date, outside the week | `includes` |

  "There is no date-format parsing in this handler and there does not need to be.
  Membership in a list of seven known strings is a stronger check than any regular
  expression you would write, and it is one line."

- **The three lines of the happy path, in order, and the order matters:**

  ```ts
  habit.doneDates = toggleDate(habit.doneDates, date)
  writeStore(store)
  body = habitWeek(habit, store.trackedDay)
  ```

  "We change the habit. We save the whole store - `habit` is an element of it, so
  saving the store saves the change. Then we build the response **from the habit
  we just changed**, so the body is the new truth, not the old one. If you build
  the body before the flip, the screen shows the state before the click and the
  next click looks broken."

- **The invariant to say out loud: neither error branch writes.** There is
  exactly one `writeStore` call and it is inside the innermost `else`. `c-3-4`
  checks this by comparing `data/habits.json` byte for byte before and after four
  failing requests. Show it if you have the minutes:

  ```bash
  curl -s localhost:3000/api/habits > /dev/null       # materialise the store
  md5sum data/habits.json
  curl -s -X POST localhost:3000/api/habits/stretch/toggle \
    -H 'Content-Type: application/json' -d '{}'
  md5sum data/habits.json                             # same
  ```

- **The demos, with `data/habits.json` open in the editor:**

  ```bash
  # 200 - stretch gains the 25th, streak goes to 2
  curl -s -X POST localhost:3000/api/habits/stretch/toggle \
    -H 'Content-Type: application/json' -d '{"date":"2026-08-25"}'

  # 404 - the date is fine, the habit is not
  curl -s -i -X POST localhost:3000/api/habits/no-such-habit/toggle \
    -H 'Content-Type: application/json' -d '{"date":"2026-08-26"}' | head -1

  # 400 - three different ways to be wrong
  curl -s -i -X POST localhost:3000/api/habits/stretch/toggle \
    -H 'Content-Type: application/json' -d '{}' | head -1
  curl -s -i -X POST localhost:3000/api/habits/stretch/toggle \
    -H 'Content-Type: application/json' -d '{"date":"not-a-date"}' | head -1
  curl -s -i -X POST localhost:3000/api/habits/stretch/toggle \
    -H 'Content-Type: application/json' -d '{"date":"2026-08-31"}' | head -1
  ```

  Then `rm data/habits.json` and refresh `/` so everyone is back on the seed.

- **Passes when:** `c-3-1`, `c-3-2`, `c-3-3` and `c-3-4` go green. That is four
  of the session's five, at the endpoint, with no screen work yet. Say so - it
  is a good moment.

### cut-board-click - `app/page.tsx`:40

- **Fill this cut *after* `cut-api-toggle`, and say why.** If the click handler
  is written while the toggle route still answers 501, a click puts
  `{"error":"not implemented"}` into `habits` state, the next render calls
  `.days.map` on `undefined`, and the whole board disappears. The model answer's
  `if (response.ok)` guard is what prevents it. Teach the order and the guard
  together.

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-board-click): Inside `onCellClick`, POST `{ date }` to `/api/habits/` plus the clicked habit id plus `/toggle`, and set the `habits` state to the same 4 rows in the same order with only the clicked habit replaced by the `HabitWeek` in the response body. Do not fetch `/api/habits` a second time.
  ```

- **What they write:** a `fetch` with `method: 'POST'`, a JSON content type and
  `JSON.stringify({ date })`; then, on a successful response, a `setHabits` that
  maps the current array and swaps in the new row where the id matches.

- **What is already wired** (copied from `app/app/page.tsx`) - every cell
  already calls the handler with the two things it needs:

  ```tsx
  onClick={() => {
    void onCellClick(habit.id, day.date)
  }}
  ```

  and the handler's signature, also written:

  ```ts
  async function onCellClick(habitId: string, date: string): Promise<void> {
  ```

- **Teach it like this:** "A POST is a `fetch` with three extra things: the
  method, a header saying what you are sending, and the body as a string.
  `JSON.stringify({ date })` - the braces are the object, `stringify` is what
  puts it on the wire. Then: the server has just told us what that habit now
  looks like. We already have four rows in state. We want the same four rows in
  the same order, with one of them swapped. That is `map`."

- **The model answer** (copied from `app/app/page.tsx`):

  ```ts
  const response = await fetch(`/api/habits/${habitId}/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date }),
  })

  // on anything but a 200 the board is left exactly as it was
  if (response.ok) {
    const updated = (await response.json()) as HabitWeek

    setHabits((current) =>
      current.map((habit) => (habit.id === habitId ? updated : habit)),
    )
  }
  ```

- **`map` is the whole lesson, and the wrong version is the classic bug.**
  Put both on the board:

  ```
  the map:   current.map(h => h.id === habitId ? updated : h)   -> a NEW array
  the trap:  const i = habits.findIndex(...); habits[i] = updated; setHabits(habits)
  ```

  "The second one is not slower or uglier. It does not work at all. React
  compares the array you hand it against the array it already has, with `===`.
  Edit the array in place and you hand back the same array, React sees no change,
  and nothing re-renders. Your data is right, your file on disk is right, and the
  screen is frozen. `map` always builds a new array, which is why it is the
  answer."

- **The other half of the lesson: do not refetch.** The obvious wrong instinct
  after a write is `fetch('/api/habits')` again. It works, it is a whole extra
  round trip for data you were just handed, and `c-3-5` counts the GET requests
  to `/api/habits` from page load to the end of the click and requires **exactly
  1**. Open the network tab and count them live: one GET on load, one POST per
  click, no second GET, ever.

- **`setHabits((current) => ...)` takes a function, not a value.** One sentence:
  "we are computing the new state from the old state, and the updater form is
  how you say 'whatever is in there right now'. With a click that fires twice
  quickly, reading `habits` from the closure instead can lose one of the two
  updates."

- **The demo that is `c-3-5`, exactly:** on `/`, click the `2026-08-26` cell in
  the `meditate` row. That cell shades, `meditate` goes from `Streak: 0` to
  `Streak: 1`, and `drink-water` stays at `Streak: 5`. Then reload the page: it
  is still there, because it is in the file. Then `rm data/habits.json`, reload
  again, and it is gone.

- **Passes when:** `c-3-5` goes green - and with it all 16.

## Where students get stuck

- **Clicking does nothing and the network tab is empty** - `cut-board-click` is
  still open, or they wrote the fetch and never awaited it, or the file is not
  saved. No request at all means the handler body.
- **The POST returns 501** - `cut-api-toggle` is still open. Filling the click
  handler first is the natural order and the wrong one; check the route.
- **The whole board vanishes after one click, and the console says `Cannot read
  properties of undefined (reading 'map')`** - this is the one to expect. They
  put a non-200 body into `habits` state, so one "row" has no `days`. The cause
  is a missing `if (response.ok)` guard plus a route that is not finished. Add
  the guard, finish the route, reload.
- **The POST returns 400 on a date that is obviously in the week** - the body
  went out wrong. Check three things in the network tab's request payload:
  `method: 'POST'` is present, the body is `JSON.stringify({ date })` and not
  the bare object, and the key is `date`. A bare object serialises to
  `[object Object]` and `request.json()` throws.
- **The POST returns 200, the file on disk changes, and the screen does not
  move** - the array was mutated in place and `setHabits` got the same
  reference. Look for `habits[i] =` or `.splice(`. This is the mutation lesson
  and it is worth stopping the room for.
- **Every row changes, or the wrong row changes** - the `map` returned `updated`
  for the wrong condition, usually comparing against `habit.id === updated.id`
  when `updated` is `undefined`, or forgetting the ternary's `: habit` branch and
  returning `undefined` for the other three rows.
- **The clicked row jumps to the bottom** - they removed the habit and appended
  the new one instead of replacing in place. `c-3-5` does not read the order but
  the room will notice; `map` keeps it.
- **The cell shades but the streak does not move** - they updated `data-done`
  from the click and rebuilt the row from something other than the response
  body. The response *is* the new row, streak included; use it whole.
- **The cell shades and then un-shades a moment later** - a refetch of
  `/api/habits` raced the POST. Two problems in one: remove the refetch and
  `c-3-5`'s request count goes green too.
- **`c-3-5` is red but the screen looks perfect** - almost always the extra
  GET. Count the requests in the network tab: exactly one GET `/api/habits` from
  load to the end of the click.
- **`c-3-4` is red on the byte-for-byte comparison, everything else green** -
  something writes on an error path. There must be exactly one `writeStore`
  call, inside the innermost `else`. A `writeStore(store)` placed after the whole
  `if/else` runs on all three branches.
- **A 500 instead of a 400 on a malformed body** - the `.catch(() => null)` on
  `request.json()` was removed, or a fresh `await request.json()` was added
  inside the block. The body has already been read for you; read it twice and
  you get a stream error.
- **"My clicks disappeared"** - they ran the test suite. It deletes
  `data/habits.json` before and after every test. Working as designed.
- **Toggling the same day twice leaves it done, or empties the whole habit** -
  `toggleDate` only adds, or only removes, or `next` was left at its empty-array
  fallback. `c-3-3` is the criterion; the fix is in `lib/toggle.ts`, not in the
  route.
- **The done styling never appears even though `data-done` is right** - they
  changed `data-done={day.done ? 'true' : 'false'}` to a boolean. The CSS
  selector is `.cell[data-done='true']` and it matches the literal string.

## Check before moving on

This is the last session, so this is the ship check.

1. On `/`, click the `2026-08-26` cell in the `meditate` row. It shades,
   `meditate` reads `Streak: 1`, `drink-water` still reads `Streak: 5`.
2. Reload. Still there.
3. Network tab: one GET `/api/habits` for the page, one POST per click, no
   second GET.
4. Click the same cell again. It un-shades and `meditate` is back to
   `Streak: 0`.
5. `rm data/habits.json`, reload: the seeded board is back.
6. The whole suite green - 16 of 16.

If step 6 is short, run the failing criterion on its own with `-k` and read the
message; each test names the criterion it grades and prints the value it got.
