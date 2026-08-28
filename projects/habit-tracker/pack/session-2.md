# Session 2 - One habit's page

**Time:** 40 minutes
**Students start from:** `/` complete and read-only: four rows, seven cells
each, real streaks. `/habits/drink-water` loads but draws only the "Back to the
board" link. `GET /api/habits/drink-water` answers **501** with
`{"error":"not implemented"}`.
**Students end with:** `/habits/drink-water`, `/habits/read-pages` and
`/habits/stretch` each showing that habit's name, its streak and its seven
cells, and `/habits/no-such-habit` showing `Habit not found`. `c-2-1` through
`c-2-5` green.

## What they learn

1. Dynamic route segments: what `[id]` means in a folder name, on the API side
   and on the page side.
2. Reading the segment two ways - `await params` in a route handler,
   `useParams()` in a client component.
3. `Array.prototype.find` and why `?? null` is needed after it.
4. A route handler with two branches and two status codes.
5. Writing their first JSX: mapping an array into elements with `data-*`
   attributes.
6. Why an app needs a not-found state, and that it is a *state of the screen*,
   not an error.

## Before you start

- Session 1 finished and green. This session cannot be taught on top of an
  empty `weekDates` or `streakOf` - every response it builds runs through both.
- `npm run dev` up. Have four URLs ready to paste, in this order:
  `/api/habits/drink-water`, `/api/habits/no-such-habit`, `/habits/read-pages`,
  `/habits/no-such-habit`.
- The seven dates still on the board from session 1.
- Two facts you will need: `read-pages` is done on `08-24` and `08-25` only, so
  its page shows two shaded cells and `Streak: 0`. `stretch` is done on `08-26`
  only, so its page shows one shaded cell and `Streak: 1`.
- Open the file tree so the two `[id]` folders are visible:
  `app/api/habits/[id]/` and `app/habits/[id]/`.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap: the board is done and reads. Today: one habit gets its own address, and that address can be wrong. Show the tree - two folders literally named `[id]` - and say what the square brackets mean. Click a row's "Open Drink water" link and land on a page with nothing on it. Paste `/api/habits/drink-water` and show the 501. That is the whole to-do list: a route with two branches, a lookup, and a page. |
| 4-8 | `cut-store-find-habit` in `lib/store.ts`. One line. Nothing visible changes yet - say so before you fill it, so nobody hunts for a result. |
| 8-20 | `cut-api-habit-get`. Fill the 200 branch, refresh `/api/habits/drink-water`. Fill the 404 branch, refresh `/api/habits/no-such-habit`. Two URLs, two answers - the whole point of the cut. |
| 20-32 | `cut-habit-page`. The 404 line first (`/habits/no-such-habit` starts working immediately), then the streak text, then the cell map. Refresh `/habits/read-pages` and count the shaded cells. |
| 32-38 | Students catch up. Circulate. Run the suite: c-1-* and c-2-* green, five reds left. |
| 38-40 | What runs now: two screens, two GET endpoints, nothing writes. Next session: clicking a cell changes the file on disk. |

## The `[id]` explanation, once, at minute 1

Say it in three sentences and move on:

"A folder named `[id]` matches any single path segment. So the one file
`app/api/habits/[id]/route.ts` serves `/api/habits/drink-water` and
`/api/habits/anything-at-all`, and the folder name tells you the segment is
called `id`. On the server you read it out of `params`; in a client component
you read it with the `useParams` hook."

Both reads ship written above the markers, so nobody has to get them right -
but read each one out when you reach its file.

In `app/api/habits/[id]/route.ts` (copied from `app/`):

```ts
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id: habitId } = await params
```

`params` is a `Promise` in Next 15 and must be awaited. Worth one sentence:
"this used to be a plain object, and if you find an older tutorial that reads
`params.id` directly, that is why it does not work."

In `app/habits/[id]/page.tsx` (copied from `app/`):

```tsx
const params = useParams<{ id: string }>()
const habitId = params.id
```

## Cut points in this session

### cut-store-find-habit - `lib/store.ts`:69

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-store-find-habit): Inside `findHabit`, assign to `found` the one habit in `store.habits` whose `id` equals the `habitId` argument, and leave `found` as `null` when no habit in `store.habits` matches.
  ```

- **What they write:** one line. `find` over `store.habits` comparing `id`, with
  a fallback to `null`.

- **Teach it like this:** "`find` gives back the first element that matches, or
  `undefined` if nothing does. Our return type says `Habit | null`, not
  `Habit | undefined`, so we convert. `?? null` means 'if the left side is null
  or undefined, use null'. Two words, and now every caller has exactly one
  'missing' value to check instead of two."

- **The model answer** (copied from `app/lib/store.ts`):

  ```ts
  found = store.habits.find((habit) => habit.id === habitId) ?? null
  ```

- **Say what this does not do.** It does not copy. The doc comment above the
  function says so (copied from `app/lib/store.ts`):

  ```ts
  /**
   * The one habit in this store with that id, or `null`. What comes back is an
   * element of `store.habits`, so mutating it and then calling `writeStore(store)`
   * persists the change.
   */
  ```

  That sentence is the whole mechanism of session 3. Read it out now and remind
  them of it next week.

- **Passes when:** nothing on its own. It is named by `c-2-1`, `c-2-3` and
  `c-2-4`, all of which also need the route. Tell them that before they fill it,
  or the first thing they do is run the suite and conclude they broke something.

### cut-api-habit-get - `app/api/habits/[id]/route.ts`:24

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-api-habit-get): Read the store with `readStore()` into `store` and look the habit up with `findHabit(store, habitId)`. When that gives a habit, set `body` to `habitWeek(habit, store.trackedDay)` and `status` to 200. When it gives `null`, set `body` to an object with an `error` key and `status` to 404.
  ```

- **What they write:** read the store, look up the habit, and set the two
  variables the `return` below already uses - `body` and `status` - once in each
  branch.

- **The frame, already in the file** (copied from `app/`):

  ```ts
  let body: HabitWeek | { error: string } = { error: 'not implemented' }
  let status = 501

  // ... the block goes here ...

  return NextResponse.json(body, { status })
  ```

- **Teach it like this:** "There is one `return` and it is already written. The
  handler already answers - it answers 501, 'I am not built yet'. Your job is two
  branches that each set the same two variables. This is what most route handlers
  look like: decide the body, decide the status, hand both to one response."

  Then, on the 404: "404 is not an error in our code. Nothing threw. We looked,
  we did not find it, and we said so clearly. The body has one key, `error`, with
  a message a human can read - that is the shape of every non-200 response in
  this project."

- **The model answer** (copied from `app/app/api/habits/[id]/route.ts`):

  ```ts
  const store: Store = readStore()
  const habit = findHabit(store, habitId)

  if (habit === null) {
    body = { error: `no habit with the id ${habitId}` }
    status = 404
  } else {
    body = habitWeek(habit, store.trackedDay)
    status = 200
  }
  ```

- **`habitWeek` does the interesting part and it ships written.** Show it once
  while you are here (copied from `app/lib/store.ts`):

  ```ts
  export function habitWeek(habit: Habit, trackedDay: string): HabitWeek {
    const done = new Set(habit.doneDates)

    return {
      id: habit.id,
      name: habit.name,
      streak: streakOf(habit.doneDates, trackedDay),
      days: weekDates(trackedDay).map((date) => ({ date, done: done.has(date) })),
    }
  }
  ```

  One sentence: "this is last week's two functions joined together - the seven
  dates from `weekDates`, each asked whether it is in the habit's done set, plus
  the streak. It is the only thing that ever builds a `HabitWeek`, which is why
  all three endpoints answer with the same shape."

- **Do the demo in two halves.** Fill the 200 branch, refresh
  `/api/habits/drink-water`, read out `"streak": 5` and count seven entries in
  `days`. Then fill the 404 branch and refresh `/api/habits/no-such-habit`. Two
  URLs, two behaviours, in the browser, before any page exists.

- **Passes when:** `c-2-1` and `c-2-2` go green. `c-2-1` is the 200 branch -
  name `Drink water`, seven days, streak 5. `c-2-2` is the 404 branch - status
  404 and a non-empty `error` string.

### cut-habit-page - `app/habits/[id]/page.tsx`:44

- **What students see**, quoted from the handout:

  ```
  // TODO(cut-habit-page): When the `/api/habits/[id]` response status is 404, set `missing` to `true`. Otherwise map `habit.days` into one `day-cell` element per entry, each with `data-date` set to that entry's date string and `data-done` set to the string `"true"` on a done entry and the string `"false"` on every other entry, and set `streakText` to `Streak: ` joined with `habit.streak`. Keep the `habit-name` element and the `habit-missing` element already in the file: when `missing` is `true` the page draws `habit-missing` and no `habit-name`, no `habit-streak` and no `day-cell`. Only a 404 sets `missing`; any other non-200 status leaves the page in its pre-response state, and nothing grades that.
  ```

- **What they write:** an `if` on the status they already have in state - 404
  sets `missing` - and an `else if` for a habit that arrived, which sets
  `streakText` and builds the array of cell elements.

- **The three fallbacks and the fetch, already in the file** (copied from
  `app/app/habits/[id]/page.tsx`):

  ```tsx
  const [habit, setHabit] = useState<HabitWeek | null>(null)
  const [status, setStatus] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    fetch(`/api/habits/${habitId}`).then(async (response) => {
      const data = response.status === 200 ? ((await response.json()) as HabitWeek) : null
      if (!cancelled) {
        setStatus(response.status)
        setHabit(data)
      }
    })

    return () => {
      cancelled = true
    }
  }, [habitId])

  // the fallbacks stay above the marker, so the skeleton still renders
  let missing = false
  let streakText = 'Streak: -1'
  let cells: ReactElement[] = []
  ```

  Two things to point out. The fetch stores **both** the status and the body,
  because the page has to tell "not found" apart from "found" and the body alone
  cannot do that. And `cancelled` is the stale-response guard: if a student
  clicks through to a second habit before the first reply lands, the flag stops
  the old reply from overwriting the new one.

- **Teach it like this:** "Three variables sit above your block with placeholder
  values, and the JSX below already reads all three. So you are not building a
  page - the page is built. You are deciding what those three variables hold.
  Two questions in order: did the server say 404? Then `missing` is true and we
  are done. Otherwise, did a habit actually arrive? Then fill in the streak text
  and the cells."

- **The model answer** (copied from `app/app/habits/[id]/page.tsx`):

  ```tsx
  if (status === 404) {
    missing = true
  } else if (habit !== null) {
    streakText = `Streak: ${habit.streak}`
    cells = habit.days.map((day) => (
      <div
        key={day.date}
        className={styles.cell}
        data-testid="day-cell"
        data-date={day.date}
        data-done={day.done ? 'true' : 'false'}
      >
        {day.date.slice(8)}
      </div>
    ))
  }
  ```

- **The `habit !== null` check is load-bearing, and not for the reason they
  think.** On the very first render nothing has been fetched: `status` is `null`
  and `habit` is `null`. Without that check, `habit.days.map` runs on `null` and
  the page throws before the fetch even resolves - a blank screen with a console
  error, on the happy path. Say it as a rule: "a client component renders once
  before its data arrives, every single time. Write for that render."

- **`data-done` is a string, twice over.** They saw this in session 1's board.
  Say it again: `day.done ? 'true' : 'false'`. The CSS selector is
  `.cell[data-done='true']` and the tests read the attribute's literal text.

- **These are `<div>`s, not `<button>`s.** The board's cells are buttons because
  they will be clickable in session 3. This page is display only - the spec says
  so, and `/` is the only screen that writes. If a student asks why they cannot
  toggle from here: "one writer, one place. It keeps session 3 to one file."

- **Passes when:** `c-2-3`, `c-2-4` and `c-2-5` go green. Check them in that
  order on screen: `/habits/read-pages` has seven cells with two shaded,
  `/habits/stretch` reads `Stretch` and `Streak: 1`, `/habits/no-such-habit`
  reads `Habit not found` and shows nothing else.

- **Why `Streak: -1` is the fallback.** `c-2-4` reads `Streak: 1` on
  `/habits/stretch`. If the fallback had been `Streak: 0`, a student who filled
  the cells and forgot `streakText` would pass on three of the four habits and
  never know. `-1` is a number no correct streak can be, so a forgotten line is
  visible from across the room.

## Where students get stuck

- **`/api/habits/drink-water` still returns 501** - the file was not saved, or
  they edited `app/api/habits/route.ts` (the list) instead of
  `app/api/habits/[id]/route.ts` (the one). The two filenames are identical;
  check the tab, not the code.
- **The route returns 200 with `{"error":"not implemented"}`** - they set
  `status` in a branch and never touched `body`, or the other way round. Both
  variables, in both branches.
- **`Cannot read properties of undefined`, or TS complains about `params`** -
  `params` was read without `await`. It is a `Promise` in Next 15.
- **404 for every id, including real ones** - `findHabit` is still empty, so
  `found` stays at its `null` fallback and every lookup misses. This is the
  cross-file failure of the session: the symptom is in the route and the cause is
  in `lib/store.ts`.
- **`c-2-1` green but `c-2-3` red** - the endpoint works and the page does not.
  Prove the endpoint in a browser tab first; it stops the "nothing works"
  spiral.
- **The page is blank and the console says `Cannot read properties of null
  (reading 'days')`** - the `habit !== null` guard is missing, or they wrote
  `if (status !== 404)` instead of `else if (habit !== null)`. The first render
  has no habit.
- **`Habit not found` shows for a habit that exists** - they compared against
  the wrong thing: `if (status !== 200)` sets `missing` on the very first render,
  when `status` is still `null`. Only a literal 404 sets `missing`.
- **`Streak: -1` on a real habit** - `streakText` was never assigned; only the
  cells were.
- **Seven cells appear but the test says one** - `data-testid="day-cell"` went
  on the wrapping `<div>` instead of on each cell inside the map.
- **The cells appear unstyled or all identical** - they styled with a class name
  instead of `data-done`, or set `data-done` to a boolean-looking value other
  than the exact strings `'true'` and `'false'`. The selector is
  `.cell[data-done='true']`.
- **`Each child in a list should have a unique "key" prop`** in the console -
  `key={day.date}` was left off the mapped element. The dates are unique, so the
  date is the key.
- **Changing the id in the URL does not change the page** - they left `habitId`
  out of the `useEffect` dependency array. It ships written as `[habitId]`; if
  someone "cleaned it up" to `[]`, this is why.

## Check before moving on

Four URLs, in this order, all by hand:

1. `/api/habits/drink-water` - 200, `"name": "Drink water"`, `"streak": 5`,
   seven entries in `days`.
2. `/api/habits/no-such-habit` - 404 with an `error` string.
3. `/habits/read-pages` - the name, `Streak: 0`, seven cells with the first two
   shaded.
4. `/habits/no-such-habit` - `Habit not found`, and nothing else on the page but
   the back link.

`c-1-1` through `c-2-5` green - eleven of sixteen. Session 3 needs `findHabit`
working, because the toggle route looks the habit up the same way.
