# Session 1 - Setup, the boards, and the clues

**Time:** 40 minutes
**Students start from:** the skeleton, `npm install` done and `npm run dev`
running. `/puzzles/boat` draws 25 empty cells with five blank clue boxes down the
left and nothing across the top. Two of the eleven tests pass (c-1-5, c-2-4).
**Students end with:** `GET /api/puzzles` serving all three puzzles with correct
clues on both axes, and all three boards drawing both clue strips. Criteria
c-1-1, c-1-2, c-1-3 and c-1-4 go green.

## What they learn

In this order:

1. **Run-length encoding a line of cells.** Walk the cells, count a block of
   consecutive `filled`, push the count when the block ends. The two things that
   are always wrong the first time: the block that ends at the *last* cell, and
   the line that has no filled cell at all.
2. **Transposing a grid so row logic grades columns.** You do not write a second
   function for columns. You turn the grid on its side and call the first one
   again.
3. **Deriving fixtures from the answer instead of storing them.** The seed is the
   solution; the clues are computed. A seed cannot disagree with itself, and the
   solution never leaves the server.
4. **Pinning every rendered element to a `data-testid` a test can read.** The CSS
   class names are hashed by CSS Modules, so the test hooks are `data-testid` and
   `data-state`, and they are already in the shipped markup.

## Before you start

- `npm run dev` running in the `skeleton/` directory, browser on
  `/puzzles/boat`, and a second tab on `http://localhost:3000/api/puzzles`. That
  raw JSON tab is your main teaching instrument today - it shows the clue arrays
  changing as the students write.
- Editor open on `lib/nonogram.ts` and `lib/puzzles.ts` side by side.
- Do **not** read `Board.tsx` top to bottom. It is 190 lines and it will eat the
  session. The tour below names the four places to look and nothing else.

## The plan

| Minutes | What you do |
|---|---|
| 0-7 | Show the running skeleton and the empty JSON. Tour the shipped setup in the fixed order below. |
| 7-12 | Walk `GET /api/puzzles` and the four places in `Board.tsx` that matter. |
| 12-26 | `cut-runs-of` - teach it, live-code it, students write it, you circulate. |
| 26-32 | `cut-transpose` - teach it, students write it. |
| 32-38 | All three boards open, students check their clues against the table, you circulate. |
| 38-40 | Run-through, and what session 2 does with these two functions. |

Total: 40 minutes.

**The 0-7 tour only fits if you follow this order and stop:** the seed strings in
`lib/puzzles.ts`; the three type aliases at the top of `lib/nonogram.ts`; the two
TODOs the students will fill; `puzzleFor`, to show that both clue strips come out
of the same two functions. Four stops, roughly 100 seconds each.

## What ships whole (say this, do not read it out)

The endpoint is three lines of real code:

```ts
import { NextResponse } from 'next/server'

import { allPuzzles } from '@/lib/puzzles'
import type { Puzzle } from '@/lib/puzzles'

// the clues are derived on every request rather than stored, so this handler is
// never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/puzzles -> Puzzle[], 200. All three puzzles in seed order, each with
 * id, title, size, rowClues and colClues and no other key. The solution is not
 * in the response, which is what stops the board grading itself in the browser.
 */
export async function GET(): Promise<Response> {
  const puzzles: Puzzle[] = allPuzzles()

  return NextResponse.json(puzzles)
}
```

And the derivation - the two lines at the bottom are the whole design:

```ts
/**
 * The puzzle an id names, with both clue strips derived from its solution.
 * `size` is the length of a seeded row, so a board still has its true size
 * while the derivation is being written.
 */
export function puzzleFor(id: string): Puzzle | null {
  const seed = SEEDS.find((entry) => entry.id === id)

  if (seed === undefined) {
    return null
  }

  const rows = seed.rows
  const cells = rows.map(rowCells)

  return {
    id: seed.id,
    title: seed.title,
    size: rows.length === 0 ? 0 : rows[0].length,
    rowClues: cells.map(runsOf),
    colClues: transpose(cells).map(runsOf),
  }
}
```

The only four places in `Board.tsx` you need in this session:

1. It fetches once on mount and builds a `size` by `size` grid of `empty`:

```tsx
  useEffect(() => {
    let cancelled = false

    fetch('/api/puzzles').then(async (response) => {
      if (!response.ok) {
        return
      }

      const data = (await response.json()) as Puzzle[]

      if (cancelled) {
        return
      }

      const found = data.find((entry) => entry.id === puzzleId)

      setPuzzles(data)

      if (found !== undefined) {
        setGrid(
          Array.from({ length: found.size }, () =>
            Array.from({ length: found.size }, (): Cell => 'empty'),
          ),
        )
      }
    })

    return () => {
      cancelled = true
    }
  }, [puzzleId])
```

2. It maps the clue **arrays**, not `size`:

```tsx
      <div className={styles.board}>
        <div className={styles.colStrip}>
          <div className={styles.corner} aria-hidden="true" />
          {puzzle.colClues.map((clue, c) => (
            <div
              key={`col-${c}`}
              className={styles.clue}
              data-testid={`col-clue-${c}`}
              data-status={statusOf(result?.cols, c)}
            >
              {clue.join(' ')}
            </div>
          ))}
        </div>
```

Say why out loud, because it explains what students are about to see: while
`transpose` is unwritten, `colClues` is an empty array. Mapping an empty array
renders nothing. Counting to `size` and indexing the array would read `undefined`
and throw on `undefined.join`, and every board would white-screen before anybody
had written a line.

3. The cells, and where the test hooks live:

```tsx
          <div className={styles.grid}>
            {grid.map((row, r) => (
              <div key={`line-${r}`} className={styles.line}>
                {row.map((state, c) => (
                  <button
                    key={`cell-${c}`}
                    type="button"
                    className={styles.cell}
                    data-testid={`cell-${r}-${c}`}
                    data-state={state}
                    aria-label={`row ${r + 1}, column ${c + 1}`}
                    onClick={() => handleCellClick(r, c)}
                  />
                ))}
              </div>
            ))}
          </div>
```

4. The default every clue shows before any click:

```tsx
  const statusOf = (line: LineStatus[] | undefined, index: number): LineStatus =>
    line === undefined ? 'open' : line[index] ?? 'open'
```

## Cut points in this session

### cut-runs-of - lib/nonogram.ts:29

**What students see** - the file, exactly as handed over:

```ts
export function runsOf(cells: Cell[]): number[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let runs: number[] = []

  // TODO(cut-runs-of): Fill `runs` with the length of each block of consecutive `filled` cells in `cells`, in the order the blocks appear, counting a block that ends at the last cell. A `crossed` cell and an `empty` cell both break a block. When `cells` holds no `filled` cell at all, `runs` must be the one-entry list `[0]`, which is the clue an empty line carries.

  return runs
}
```

The TODO line, verbatim:

```
  // TODO(cut-runs-of): Fill `runs` with the length of each block of consecutive `filled` cells in `cells`, in the order the blocks appear, counting a block that ends at the last cell. A `crossed` cell and an `empty` cell both break a block. When `cells` holds no `filled` cell at all, `runs` must be the one-entry list `[0]`, which is the clue an empty line carries.
```

**What they write:** a counter for the current block and a loop over `cells`. A
`filled` cell adds one to the counter. Anything else ends the block - push the
counter if it is above zero, then reset it. After the loop finishes, push once
more if a block is still open. Finally, if nothing was pushed at all, set `runs`
to `[0]`.

**Teach it like this:** "Read the line left to right and count how long each
black stripe is. Two things a first attempt always gets wrong: the stripe that
runs off the end of the line never gets written down, because nothing after it
ends it; and a line with no stripes at all still has a clue, and that clue is
zero, not nothing."

Draw `blanks` row 4 on the board - `#.#.#` - and ask for the clue before anyone
types. Then row 1, `#####`. Those are the two failing shapes.

**Passes when:** c-1-1 goes green (boat rowClues `[[1],[3],[5],[1,1],[1,1]]`) and
c-1-3 goes green (blanks rowClues `[[0],[5],[1,1],[3],[1,1,1]]`). c-1-3 is the
edge-case fixture: it is the one a hardcoded five-element list cannot fake.

**Reference - what the finished function looks like** (instructor only):

```ts
/**
 * The run-length clue a line of cells carries: the length of each block of
 * consecutive `filled` cells, in order. A line holding no `filled` cell at all
 * carries the one-entry clue `[0]`.
 */
export function runsOf(cells: Cell[]): number[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let runs: number[] = []

  // >>> CUT cut-runs-of
  let block = 0

  for (const cell of cells) {
    if (cell === 'filled') {
      block += 1
    } else if (block > 0) {
      runs.push(block)
      block = 0
    }
  }

  if (block > 0) {
    runs.push(block)
  }

  if (runs.length === 0) {
    runs = [0]
  }
  // <<< CUT cut-runs-of

  return runs
}
```

Note `runs` starts as an empty array on purpose. A fallback of `[0]` would have
compiled too, and would have handed the students the empty-line case that c-1-3
exists to grade.

### cut-transpose - lib/nonogram.ts:60

**What students see:**

```ts
export function transpose<T>(grid: T[][]): T[][] {
  let out: T[][] = []

  // TODO(cut-transpose): Set `out` so that `out[c][r]` holds `grid[r][c]`: one entry per column of `grid`, each as long as `grid` has rows. Every row of `grid` has the same length, and `grid` itself is left unchanged.

  return out
}
```

The TODO line, verbatim:

```
  // TODO(cut-transpose): Set `out` so that `out[c][r]` holds `grid[r][c]`: one entry per column of `grid`, each as long as `grid` has rows. Every row of `grid` has the same length, and `grid` itself is left unchanged.
```

**What they write:** two nested loops. The outer one runs over the columns of
`grid`, the inner one over the rows. For each column index, collect `grid[r][c]`
for every `r` into a new array and push that array onto `out`. Nothing is written
back into `grid`.

**Teach it like this:** "The rows are already easy - we just wrote the function
that reads a row. The columns are the same problem wearing a hat. So instead of
writing a column reader, turn the board on its side and use the row reader
again."

Physically turn a printed 5x5 grid ninety degrees while you say it. Then show
`puzzleFor` again: `cells.map(runsOf)` and `transpose(cells).map(runsOf)` - same
function, two axes.

**Passes when:** c-1-2 goes green (boat colClues `[[1],[4],[3],[4],[1]]`, house
`size` 8 with colClues `[[1],[6],[3],[4,2],[4,2],[3],[6],[1]]`). This is the
criterion `cut-transpose` lives or dies by, because both those boards have
colClues that differ from their rowClues. c-1-4 also needs it - the board has
zero elements across the top until it works.

**Reference - what the finished function looks like** (instructor only):

```ts
/**
 * The columns of `grid`, as rows. `grid` is left as it was, so the caller can
 * read both axes off the same board.
 */
export function transpose<T>(grid: T[][]): T[][] {
  let out: T[][] = []

  // >>> CUT cut-transpose
  const width = grid.length === 0 ? 0 : grid[0].length

  for (let c = 0; c < width; c += 1) {
    const column: T[] = []

    for (let r = 0; r < grid.length; r += 1) {
      column.push(grid[r][c])
    }

    out.push(column)
  }
  // <<< CUT cut-transpose

  return out
}
```

The `grid.length === 0 ? 0 : grid[0].length` guard is why an empty grid does not
throw. Point at it if a student asks why the width is not just `grid[0].length`.

## Where students get stuck

- **"blanks row 1 says `0` and it should say `5`."** They never push the block
  after the loop ends. `#####` never hits a non-filled cell, so the counter is
  never written down, `runs` ends up empty, and the `[0]` fallback fires. The
  fix is the three lines after the loop. Say: "your loop only writes a stripe
  down when something ends it. Nothing ends the last stripe except the line
  running out."
- **"c-1-3 fails, index 0 is `[]` but it wants `[0]`."** They returned an empty
  array for the empty row. An empty line has a clue and the clue is `[0]`. This
  is the exact message the runner prints, so read it with them.
- **`crossed` breaks a block too, and nothing today can tell them they got that
  wrong.** No seed string contains a crossed cell, so a `runsOf` that only ends a
  block on `empty` is green all through session 1 and blows up in session 2 on
  c-2-2. If you see `cell === 'empty'` in the else-branch instead of
  `cell === 'filled'` in the if-branch, fix it now - it is free now and expensive
  next week.
- **"There are still no clues along the top."** Expected until `transpose` is
  written. Zero `col-clue` elements is the honest rendering of an empty
  `colClues` array. Do not let them "fix" it by counting to `size` in the JSX.
- **"boat's column clues are the same as its row clues."** `transpose` is
  returning the grid unchanged - usually `out[r][c] = grid[r][c]` instead of
  `out[c][r] = grid[r][c]`, or the loops nested the wrong way round. Ask them to
  print `transpose([[1,2],[3,4]])` in their head and say what it should be.
- **"`Cannot read properties of undefined (reading 'length')`."** They wrote
  `grid[0].length` with no guard and something called it with an empty array. The
  shipped version guards it; show the guard.
- **"`Module not found: Can't resolve '@/lib/nonogram'`."** They moved a file or
  typed the alias wrong. `@/*` maps to the project root in `tsconfig.json`, so
  `@/lib/nonogram` is `lib/nonogram.ts` next to `app/`, not inside it.
- **The JSON tab shows old clues.** The dev server has the old module. Reload the
  tab - `export const dynamic = 'force-dynamic'` means it is never cached by
  Next, but the browser will happily show you a stale tab.
- **Two tests already passed and a student thinks they cheated.** c-1-5 and c-2-4
  have no cuts. Tell them at the start, not when they ask.

## Check before moving on

Open all three boards and read the strips against the table in `README.md`:

- `/puzzles/blanks` - down the left: `0`, `5`, `1 1`, `3`, `1 1 1`. Across the
  top: `2 1`, `1 1`, `1 2`, `1 1`, `2 1`. Twenty-five empty cells.
- `/puzzles/house` - sixty-four cells, eight clues down and eight across, and
  `4 2` in columns 3 and 4.
- `/puzzles/nope` - the words `Puzzle not found`, and no grid.

Then: `BASE_URL=http://localhost:3000 python -m pytest verify -q -k "c_1_"` -
five passed. If c-1-4 is red while c-1-1 through c-1-3 are green, the endpoint is
right and the screen is not; that is almost always a stale dev server.

Session 2 does not add a new data source. It adds one rule over the same two
functions, so both of these must be correct before it starts.
