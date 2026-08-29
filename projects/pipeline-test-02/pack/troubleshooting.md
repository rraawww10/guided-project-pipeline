# Troubleshooting

Errors students actually hit on this project, in the order they hit them. Each
entry is the symptom they report, the cause, and the fix.

## Getting it running

### `npm install` fails, or `npm run dev` exits immediately

Next 15 and React 19 need Node 18.18 or newer; Node 20 LTS is the safe answer.
`node -v` first. If a student is on Node 16, nothing else in this list matters.

### `Error: listen EADDRINUSE: address already in use :::3000`

A dev server is already running - usually yesterday's, or a second terminal tab.
Kill it, or run `npm run dev -- -p 3001` and use `http://localhost:3001`. If you
change the port, the test command's `BASE_URL` has to change with it.

### The page is blank and the terminal says nothing

Look at the browser console, not the terminal. A thrown error inside a client
component shows up there. On this project the usual cause is reading `.join` off
something that is not an array.

### Changes do not show up

They are looking at `npm run start`, which serves the last `npm run build`, not
`npm run dev`. If they really are on `dev` and it is still stale, stop the
server, delete `.next`, and start again.

## Imports and TypeScript

### `Module not found: Can't resolve '@/lib/nonogram'`

The `@/*` alias maps to the project root, set in `tsconfig.json`:

```json
"paths": { "@/*": ["./*"] }
```

So `@/lib/nonogram` is `lib/nonogram.ts`, which sits **next to** `app/`, not
inside it. A file moved into `app/lib/` breaks this.

### `A function whose declared type is neither 'undefined', 'void', nor 'any' must return a value. ts(2355)`

They deleted the `return` line at the bottom of the function. Every one of the
four cuts in `lib/nonogram.ts` is an *assignment* to a variable declared above
the TODO, and the `return` below the TODO is not part of the task. Put it back:

- `runsOf` ends with `return runs`
- `transpose` ends with `return out`
- `lineStatus` ends with `return status`
- `boardSolved` ends with `return solved`

### `Cannot assign to 'runs' because it is a constant. ts(2588)`

They changed `let runs` to `const runs`. `runs` is reassigned when the line has
no filled cell at all, so it has to be `let`. Same for `out`, `status`, `solved`
and `updated`.

### `Type 'string' is not assignable to type 'Cell'`

`Cell` is a union of three exact strings:

```ts
export type Cell = 'empty' | 'filled' | 'crossed'

export type LineStatus = 'satisfied' | 'open' | 'violated'

export type CheckResult = {
  rows: LineStatus[]
  cols: LineStatus[]
  solved: boolean
}
```

TypeScript widens a string inside a `.map` callback unless the callback is
annotated. The shipped code annotates the return type on the inner map - that is
what `(state, ci): Cell =>` is doing in `Board.tsx`. If a student's cycle will
not typecheck, that annotation is what is missing.

### `Argument of type 'Cell[][]' is not assignable to parameter of type 'number[][]'`

They passed the grid where the clues go, or the clues where the grid goes.
`boardSolved(grid, rowClues, colClues)` - grid first, then the two clue arrays.

## Session 1 - the clues

### The API returns `rowClues: [[],[],[],[],[]]` and `colClues: []`

Nothing is wrong. That is the untouched skeleton: `runsOf` hands back its empty
fallback and `transpose` hands back its empty one. It is the starting picture.

### The board has clues down the left but nothing across the top

`cut-transpose` is not written yet, so `colClues` is `[]` and there are no
elements to draw. Do not "fix" this in the JSX - the strips deliberately map the
clue array rather than counting to `size`, because counting to `size` would read
`undefined` and throw on `undefined.join`, white-screening every board.

### `blanks` row 1 reads `0` where it should read `5`

The last block is never written down. A run that ends because the line ran out is
not ended by any cell, so it needs a push after the loop.

### c-1-3 fails: `At index 0 diff: [] != [0]`

An empty line still has a clue and that clue is `[0]`. This is the last thing
`runsOf` does: if nothing was pushed, set `runs` to `[0]`.

### `boat`'s column clues are identical to its row clues

`transpose` is copying rather than transposing. The assignment is
`out[c][r] = grid[r][c]` - column index outside, row index inside. `boat`,
`blanks` and `house` were all chosen so that a copy is visibly wrong.

### `TypeError: Cannot read properties of undefined (reading 'length')` inside `transpose`

`grid[0].length` on an empty grid. The shipped version guards it:
`const width = grid.length === 0 ? 0 : grid[0].length`.

### `TypeError: clue.join is not a function` / `Cannot read properties of undefined (reading 'join')`

Something is indexing a clue array past its end. It means a strip is being drawn
by counting to `size` instead of mapping the array. Map the array.

## Session 2 - the rule

### Every clue reads `violated` as soon as the page has been clicked once

`Math.max()` with no arguments is `-Infinity`, so "one block is longer than the
largest number in the clue" is true of every block. The guard is
`const largest = wanted.length === 0 ? 0 : Math.max(...wanted)`.

### `blanks` row 0 is `violated`, and it is an empty row with clue `[0]`

`[0]` means *no blocks and a largest of 0*, not *one block of length zero*. The
block count and the largest have to be computed after dropping the zeros; the
equality test in step 1 compares the raw arrays, which is why an empty line whose
`runsOf` is `[0]` matches a clue of `[0]` exactly.

### A line with no `empty` cells left still reads `open`

The third violation condition is "no cell in `cells` is still `empty`". A
`crossed` cell is decided, so it does **not** hold that condition off. If the
test is written against `filled` instead of `empty`, this is the symptom.

### c-2-2 passes its first two requests and fails the third

That third request is the `crossed` one. Two candidates, in this order: `runsOf`
only ends a block on `empty` and treats `crossed` as continuing it (a session-1
bug that nothing in session 1 could see, because no seed string contains a
crossed cell); or the third violation condition is wrong. Check `runsOf` first.

### Clicking a cell changes nothing

Three causes, in the order to check them:

1. `updated` is still the shipped fallback, `let updated: Cell[][] = grid`, so
   the click sets the grid to what it already was.
2. They mutated the grid in place - `grid[r][c] = 'filled'` - and handed the same
   array back to `setGrid`. React compares references, sees no change and does
   not redraw. The data is right and the screen is wrong.
3. They wrote the new grid to a different variable and never assigned `updated`.

Open devtools and watch the cell's `data-state` attribute across two clicks. If
it never changes, it is 1 or 3. If it changes but no clue repaints, look at the
network tab instead.

### The cell goes `empty` -> `filled` and then stops

The cycle has three steps and the last one wraps: `crossed` goes back to `empty`.
A chain that returns the current state for `crossed` gets stuck.

### Clicking one cell wipes another cell

The whole grid is being rebuilt rather than copied. Rows other than `r` must be
passed through untouched, and cells other than `c` must keep the state they had.

### The clue strips never repaint, but `data-state` on the cells does change

The POST is happening and the answer is being thrown away, or the answer is all
`open`. Check the network tab: a 200 whose `rows` are all `"open"` means
`lineStatus` is still returning its fallback. A 400 means the grid being posted
is malformed - see below.

### `POST /api/puzzles/boat/check` returns 400

The body is not a grid for that puzzle. The route wants exactly `size` rows of
exactly `size` cells, and every cell must be one of `empty`, `filled` or
`crossed`. On this project it is nearly always a cycle that wrote `true`, `1`,
`"fill"` or `undefined` into a cell.

### `POST /api/puzzles/<id>/check` returns 404

There is no puzzle with that id. The three are `boat`, `blanks` and `house`. The
id is resolved before the body is read, so a 404 comes back whatever the body
holds.

### The screen says `Puzzle not found`

Same cause, from the URL bar - a typo in the id. This is the shipped `not-found`
branch working correctly; c-1-5 grades it.

### Every clue is green but no `Solved` banner

`boardSolved` is checking rows and not columns, or it is joining the two with
`or` instead of `and`. The proving case: take the `boat` solution and move row
0's filled cell from column 2 to column 0. Every row still matches its clue and
column 0 now has two blocks against a clue of `[1]`.

### The `Solved` banner appears when the board is not solved

`solved` is being read off the two status lists rather than computed from the
grid, and something is defaulting to `satisfied`. Compute it from the grid, which
is what the shipped version does and why it is graded on its own.

### `You're importing a component that needs useState. This React Hook only works in a Client Component.`

The `'use client'` directive on the first line of `Board.tsx` was deleted or
pushed below an import. It must be the very first line of the file.

## Running the tests

### `KeyError: 'BASE_URL'`

The suite never starts a server; it reads the URL from the environment. Start the
app, then run:

```bash
BASE_URL=http://localhost:3000 python -m pytest verify -q
```

### `playwright._impl._errors.Error: Executable doesn't exist`

Playwright's browser was never downloaded. `playwright install chromium`.

### `Locator expected to have count '5', Actual value: 0`

The clue strip has no elements at all. On c-1-4 and c-2-6 that means `transpose`
is still empty. The counts are asserted before anything is read off the strips
precisely so that an absent strip fails instead of passing vacuously.

### Two tests pass on a completely untouched skeleton

Correct. c-1-5 and c-2-4 have no cut points - they grade branches that ship
written. Nine of the eleven start red.

### A test passes for one student and fails for another on the same code

Check they are not both pointing `BASE_URL` at the same server. Otherwise: each
test gets a fresh browser context and there is no store, no file and no state
between runs, so the same code gives the same answer every time. A flake here
means the two are not running the same code.

### `-k` selection

`-k "c_1_"` runs session 1's five criteria, `-k "c_2_"` runs session 2's six.
Test names carry the criterion id, so `-k "c_2_2"` runs exactly one.
