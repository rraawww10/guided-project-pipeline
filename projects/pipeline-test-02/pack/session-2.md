# Session 2 - Filling, checking, and solved

> ## Timing warning - read this first
>
> **This session does not fit 40 minutes as the spec budgets it. Timed honestly
> it runs to 48.** The plan table below is a 40-minute plan; it gets there by
> spending less than the spec allows in two places, both marked. The overrun is
> concentrated in one cut:
>
> | item | spec budget | honest estimate |
> |---|---|---|
> | intro and recap | 4 | 4 |
> | walk the check route | 3 | 5 |
> | `cut-line-status` | 14 | **18** |
> | `cut-cell-cycle` | 9 | **11** |
> | `cut-board-solved` | 6 | 6 |
> | end-of-session run-through | 4 | 4 |
> | **total** | **40** | **48** |
>
> `cut-line-status` is a four-branch rule with an ordered equality test, three
> violation conditions and a `[0]`/`[]` convention, and four of the six criteria
> go red if any one of those is wrong. `learning/lessons.md` records three
> consecutive projects overrunning on exactly this shape - one cut much larger
> than the others - most recently habit-tracker's `cut-api-toggle`, estimated at
> 6 and measured near 20.
>
> **The two levers, in the order to pull them:**
>
> 1. **Minute 12:** put the four `const` lines of `lineStatus` on the board
>    before students start typing, so they only write the `if`/`else if`. Saves
>    about 4.
> 2. **Minute 25:** if `cut-line-status` is not green on most screens, walk
>    `cut-board-solved` instead of having them type it. It is two `every` loops
>    over a function they wrote twenty minutes ago, and it is the cheapest thing
>    in the session to give away. Saves about 4.
>
> Do not fix this by moving a cut into session 1: session 1 would then carry 3
> cuts plus the whole project setup against session 2's 2, which is the
> imbalance `learning/lessons.md` and the spec linter's E113 both warn about.

**Time:** 40 minutes as planned below; 48 if you teach every cut in full.
**Students start from:** session 1 finished. All three boards draw correct clues
on both axes. Clicking a cell does nothing visible. Six of the eleven tests pass:
c-1-1 through c-1-5, plus c-2-4, which has no cuts.
**Students end with:** clicking cycles a cell through three states, every clue
repaints with its own verdict after each click, and filling `blanks` correctly
raises the `Solved` banner. All eleven criteria green.

## What they learn

In this order:

1. **A three-valued cell state that a boolean cannot hold.** `empty`, `filled`,
   `crossed`. `crossed` is the student's own note that a cell is blank. It breaks
   a run exactly as `empty` does - but unlike `empty` it marks the cell as
   *decided*, and that difference is the whole third violation condition.
2. **A total status rule with a closed list of violations.** Three answers,
   three named violation conditions, and nothing else. A line is `open` unless
   the rule says otherwise.
3. **Grading two overlapping axes with one pure function.** The same `lineStatus`
   grades rows, and grades `transpose(grid)` for columns. Every cell is inside
   two constraints at once.
4. **Posting the whole grid and rendering the per-line answer.** No diffing, no
   patching. Send the board, get back the verdict for every line.

## Before you start

- `npm run dev` running, browser on `/puzzles/boat`.
- Editor on `lib/nonogram.ts` and `app/puzzles/[id]/Board.tsx`.
- The status rule written on the board **before** the session begins. You will
  point at it for twenty minutes and you do not want to be writing it live:

```
1. satisfied   when runsOf(cells) equals clue, same numbers, same order
2. violated    when ANY of exactly these three holds:
                 - cells has more blocks than clue has numbers
                 - one block is longer than the largest number in clue
                 - no cell is still 'empty' AND runsOf(cells) differs from clue
3. open        in every other case
```

  And underneath it: `[0]` and `[]` both mean **no blocks, largest of 0**.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap `runsOf` and `transpose`. Click a cell, show that nothing happens, and say why. |
| 4-7 | Walk `POST /api/puzzles/[id]/check` - it ships whole. |
| 7-21 | `cut-line-status`. Read the rule off the board, work the three examples, then they type. **Lever 1 applies here.** |
| 21-30 | `cut-cell-cycle`. The immutable nested update. |
| 30-36 | `cut-board-solved`. **Lever 2 applies here.** |
| 36-40 | Fill `blanks` live to the `Solved` banner. Full test run. |

Total: 40 minutes. See the warning box for what this squeezes.

## What ships whole (say this, do not read it out)

The check route. Two things to point at and then move on: the id is resolved
**first**, so an unknown id is a 404 whatever the body holds; and the result is
built by calling `lineStatus` once per row and once per column of
`transpose(grid)`.

```ts
/**
 * POST /api/puzzles/[id]/check, body { grid } -> CheckResult, 200; or { error }
 * with 404 when no puzzle has that id, or 400 when the body is not a grid of the
 * puzzle's size. The id is resolved first, so an unknown id answers 404 whatever
 * the body holds.
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params
  const puzzle: Puzzle | null = puzzleFor(id)

  if (puzzle === null) {
    return NextResponse.json({ error: `no puzzle with the id ${id}` }, { status: 404 })
  }

  const payload = await request.json().catch(() => null)
  const grid = readGrid(payload, puzzle.size)

  if (!Array.isArray(grid)) {
    return NextResponse.json({ error: grid }, { status: 400 })
  }

  const result: CheckResult = {
    rows: grid.map((row, r) => lineStatus(row, puzzle.rowClues[r] ?? [])),
    cols: transpose(grid).map((col, c) => lineStatus(col, puzzle.colClues[c] ?? [])),
    solved: boardSolved(grid, puzzle.rowClues, puzzle.colClues),
  }

  return NextResponse.json(result)
}
```

The body validation, if anyone asks where the 400 comes from:

```ts
const CELL_STATES: Cell[] = ['empty', 'filled', 'crossed']

/**
 * The posted grid, or a message saying why it is not a grid for this puzzle.
 * A grid is exactly `size` rows of exactly `size` cells, and every cell is one
 * of the three strings.
 */
function readGrid(payload: unknown, size: number): Cell[][] | string {
  if (payload === null || typeof payload !== 'object') {
    return 'the request body must be a JSON object carrying a grid'
  }

  const grid = (payload as { grid?: unknown }).grid

  if (!Array.isArray(grid) || grid.length !== size) {
    return `grid must be an array of ${size} rows`
  }

  for (const row of grid) {
    if (!Array.isArray(row) || row.length !== size) {
      return `every row of grid must hold ${size} cells`
    }

    for (const cell of row) {
      if (typeof cell !== 'string' || !CELL_STATES.includes(cell as Cell)) {
        return 'every cell must be empty, filled or crossed'
      }
    }
  }

  return grid as Cell[][]
}
```

And in `Board.tsx`, the part that already works. The click handler already calls
`setGrid` and already posts - the students only fill in the middle:

```tsx
  async function sendCheck(next: Cell[][]) {
    const seq = sent.current + 1
    sent.current = seq

    const response = await fetch(`/api/puzzles/${puzzleId}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ grid: next }),
    })

    if (!response.ok) {
      return
    }

    const data = (await response.json()) as CheckResult

    // a later click has already been sent, so this answer is out of date
    if (seq === sent.current) {
      setResult(data)
    }
  }
```

Worth one sentence: `sent` is a counter. A response whose sequence number is no
longer the newest is dropped, so a slow answer never repaints the board with a
stale verdict. Nothing in the test suite grades that, and it is still correct.

The banner:

```tsx
      {result !== null && result.solved ? (
        <p className={styles.banner} data-testid="solved-banner">
          Solved
        </p>
      ) : null}
```

## Cut points in this session

### cut-line-status - lib/nonogram.ts:85

**What students see:**

```ts
export function lineStatus(cells: Cell[], clue: number[]): LineStatus {
  let status: LineStatus = 'open'

  // TODO(cut-line-status): Set `status` to `satisfied` when `runsOf(cells)` holds the same numbers in the same order as `clue`. Otherwise set it to `violated` when any one of these three holds: `cells` has more blocks of consecutive `filled` cells than `clue` has numbers, or one of those blocks is longer than the largest number in `clue`, or no cell in `cells` is still `empty` while `runsOf(cells)` and `clue` differ. A `crossed` cell is not `empty`, so it does not hold that third condition off. A `[0]` clue, and a clue carrying no numbers at all, each count as no blocks and a largest of 0. In every other case leave `status` at `open`.

  return status
}
```

The TODO line, verbatim:

```
  // TODO(cut-line-status): Set `status` to `satisfied` when `runsOf(cells)` holds the same numbers in the same order as `clue`. Otherwise set it to `violated` when any one of these three holds: `cells` has more blocks of consecutive `filled` cells than `clue` has numbers, or one of those blocks is longer than the largest number in `clue`, or no cell in `cells` is still `empty` while `runsOf(cells)` and `clue` differ. A `crossed` cell is not `empty`, so it does not hold that third condition off. A `[0]` clue, and a clue carrying no numbers at all, each count as no blocks and a largest of 0. In every other case leave `status` at `open`.
```

**What they write:** first, four values - the runs of this line, the runs with
zeros dropped, the clue numbers with zeros dropped, and the largest of those clue
numbers (or 0 when there are none). Then one equality test: same length, same
numbers in the same order, in which case `status` is `satisfied`. Then one
`else if` whose condition is three tests joined by `or`, matching the three lines
on the board. Anything that reaches neither branch keeps the `open` it started
with.

**Teach it like this:** "This function never looks at the answer. It only asks
what *this line, on its own,* has already ruled out. A line can be `open` while
being flatly impossible for the real picture - that is not a bug, that is the
whole design. What it will not do is call a line `open` once the line has too
many pieces, or one piece too long, or has no undecided cells left."

Work these three on the board before anyone types. They are the three the tests
pin:

| line | clue | answer | why |
|---|---|---|---|
| `boat` row 1, one filled cell at column 0 | `[3]` | `open` | one block, not too long, and there are still `empty` cells |
| `boat` row 0, filled at columns 0 and 2 | `[1]` | `violated` | two blocks against one number |
| `boat` row 1, `filled filled crossed crossed crossed` | `[3]` | `violated` | nothing is `empty` any more, and `[2]` is not `[3]` |

That third one is the only place `crossed` behaves differently from `empty`. Say
it twice.

And the companion case, because it is the other half of the same idea: `boat`
row 3 holding `filled crossed filled empty empty` against clue `[1,1]` reads
`[1,1]` and is `satisfied` - `crossed` breaks a block exactly as `empty` does.

**Passes when:** c-2-2 goes green on its own. c-2-1, c-2-3 and c-2-6 all need it
too.

**Reference - what the finished function looks like** (instructor only):

```ts
/**
 * How one line stands against one clue. The rule never looks at the solution,
 * so a line can read `open` while being inconsistent with the only picture that
 * fits - it only reports what this line, on its own, has already ruled out.
 */
export function lineStatus(cells: Cell[], clue: number[]): LineStatus {
  let status: LineStatus = 'open'

  // >>> CUT cut-line-status
  const runs = runsOf(cells)
  // `[0]` and `[]` both mean no blocks and a largest of 0, on either side
  const blocks = runs.filter((n) => n > 0)
  const wanted = clue.filter((n) => n > 0)
  const largest = wanted.length === 0 ? 0 : Math.max(...wanted)

  const matches =
    runs.length === clue.length && runs.every((n, i) => n === clue[i])

  if (matches) {
    status = 'satisfied'
  } else if (
    blocks.length > wanted.length ||
    blocks.some((n) => n > largest) ||
    cells.every((cell) => cell !== 'empty')
  ) {
    status = 'violated'
  }
  // <<< CUT cut-line-status

  return status
}
```

The `wanted.length === 0 ? 0 : Math.max(...wanted)` is not decoration.
`Math.max()` with no arguments is `-Infinity`, and every block is longer than
that, so a missing guard makes every line `violated` the moment a clue is `[0]`
or `[]`. If you are pulling lever 1, this is one of the four lines to put on the
board.

### cut-cell-cycle - app/puzzles/[id]/Board.tsx:83

**What students see:**

```tsx
  function handleCellClick(r: number, c: number) {
    // the fallback stays above the marker, so a click still runs a check while
    // the cycle is unwritten
    let updated: Cell[][] = grid

    // TODO(cut-cell-cycle): Set `updated` to a fresh copy of `grid` in which only the cell at row `r` and column `c` moves one step along `empty` then `filled` then `crossed` then back to `empty`. Every other cell keeps the state it had, and `grid` itself is not mutated. The `setGrid` call and the POST to /api/puzzles/<id>/check sit below the closing marker and are already written, so this assignment is the whole task.

    setGrid(updated)
    void sendCheck(updated)
  }
```

The TODO line, verbatim:

```
    // TODO(cut-cell-cycle): Set `updated` to a fresh copy of `grid` in which only the cell at row `r` and column `c` moves one step along `empty` then `filled` then `crossed` then back to `empty`. Every other cell keeps the state it had, and `grid` itself is not mutated. The `setGrid` call and the POST to /api/puzzles/<id>/check sit below the closing marker and are already written, so this assignment is the whole task.
```

**What they write:** one expression. Map over `grid`. Rows that are not row `r`
are passed through unchanged. Row `r` is itself mapped: cells that are not column
`c` keep their state, and the cell at column `c` moves one step - `empty` becomes
`filled`, `filled` becomes `crossed`, anything else becomes `empty`. The result
is assigned to `updated`. Nothing is written into `grid`.

**Teach it like this:** "React decides whether to redraw by comparing the array
you handed it to the one it already had. If you reach into the old array and
change a cell, it is the same array, so React sees no change and nothing
redraws - even though the data is different. So we build a new one."

Then show them the failing version deliberately: `grid[r][c] = 'filled'` followed
by `setGrid(grid)`. Click. Nothing moves. That thirty seconds saves ten minutes
of debugging later.

**Passes when:** c-2-5 goes green - `cell-0-2` reads `filled`, then `crossed`,
then `empty` across three clicks, while `cell-0-0` stays `empty` throughout.

**Reference - what the finished assignment looks like** (instructor only):

```tsx
  function handleCellClick(r: number, c: number) {
    // the fallback stays above the marker, so a click still runs a check while
    // the cycle is unwritten
    let updated: Cell[][] = grid

    // >>> CUT cut-cell-cycle
    updated = grid.map((row, ri) =>
      ri === r
        ? row.map((state, ci): Cell =>
            ci !== c
              ? state
              : state === 'empty'
                ? 'filled'
                : state === 'filled'
                  ? 'crossed'
                  : 'empty',
          )
        : row,
    )
    // <<< CUT cut-cell-cycle

    setGrid(updated)
    void sendCheck(updated)
  }
```

Note what is *below* the marker and already written: `setGrid(updated)` and
`void sendCheck(updated)`. Filling this one cut makes a click both cycle the cell
and send a check, so c-2-5 and c-2-6 come alive together.

### cut-board-solved - lib/nonogram.ts:121

**What students see:**

```ts
export function boardSolved(
  grid: Cell[][],
  rowClues: number[][],
  colClues: number[][],
): boolean {
  let solved = false

  // TODO(cut-board-solved): Set `solved` to true only when `lineStatus` answers `satisfied` for every row of `grid` against the matching entry of `rowClues` and for every column of `grid` against the matching entry of `colClues`. Reach the columns through `transpose`, and leave `solved` false when even one line on either axis is not satisfied - a grid whose every row is satisfied is still not solved while any column is not.

  return solved
}
```

The TODO line, verbatim:

```
  // TODO(cut-board-solved): Set `solved` to true only when `lineStatus` answers `satisfied` for every row of `grid` against the matching entry of `rowClues` and for every column of `grid` against the matching entry of `colClues`. Reach the columns through `transpose`, and leave `solved` false when even one line on either axis is not satisfied - a grid whose every row is satisfied is still not solved while any column is not.
```

**What they write:** two checks joined by `and`. Every row of `grid` must be
`satisfied` against the matching entry of `rowClues`. Every row of
`transpose(grid)` must be `satisfied` against the matching entry of `colClues`.
Assign the two together to `solved`.

**Teach it like this:** "You already wrote the hard part. This is the same
function, called once per line, on both axes - and it is `and`, not `or`. Every
row being right is not the same as the board being right."

The case that proves it is c-2-1's second request: take the `boat` solution and
move row 0's single filled cell from column 2 to column 0. Every row still
matches its clue. Column 0 now has two blocks against a clue of `[1]`. The board
is not solved.

**Passes when:** c-2-1 goes green. c-2-6 needs it for the banner.

**Reference - what the finished function looks like** (instructor only):

```ts
/**
 * Whether the whole board is done: every row satisfied against its clue and
 * every column satisfied against its own. Computed from the grid rather than
 * from a pair of status lists, so it is graded on its own.
 */
export function boardSolved(
  grid: Cell[][],
  rowClues: number[][],
  colClues: number[][],
): boolean {
  let solved = false

  // >>> CUT cut-board-solved
  const rowsDone = grid.every(
    (row, r) => lineStatus(row, rowClues[r] ?? []) === 'satisfied',
  )
  const colsDone = transpose(grid).every(
    (col, c) => lineStatus(col, colClues[c] ?? []) === 'satisfied',
  )

  solved = rowsDone && colsDone
  // <<< CUT cut-board-solved

  return solved
}
```

The `?? []` is the reason a partly-written skeleton does not crash here: with
`cut-runs-of` still open the derived clues are empty arrays, and the rule was
written to be total over that.

## Where students get stuck

- **"Every single clue says `violated` the moment the page loads."** They dropped
  the empty-clue guard and `Math.max()` returned `-Infinity`, so every block is
  "longer than the largest". Show them `Math.max()` in the browser console.
- **"blanks row 0 says `violated` and it is an empty row."** The `[0]` clue must
  read as *no blocks, largest 0*. If they compare `runsOf` to `clue` without
  filtering the zeros out for the block count, an empty line has one "block" of
  length 0 against a clue with one number, and the arithmetic goes wrong from
  there.
- **"The line is full of crossed cells and it still says `open`."** Their third
  condition tests `cell === 'empty'` on the wrong side, or tests
  `cell !== 'filled'`. The rule is: no cell is still `empty`. A `crossed` cell is
  decided, so it does not hold the third condition off.
- **A `runsOf` bug from session 1 surfaces here for the first time.** If their
  loop only ends a block on `empty`, everything in session 1 was green (no seed
  string contains a crossed cell) and c-2-2 is now red on the `crossed` request.
  If c-2-2 fails only on its third request, look at `runsOf`, not `lineStatus`.
- **"I click and nothing happens."** Either `updated` is still the fallback
  (`updated = grid`, unchanged), or they mutated `grid` in place and React did
  not redraw. Ask them to click twice and watch `data-state` in devtools: if the
  attribute never changes, it is the first; if it changes but the strips do not,
  it is the response handling.
- **"The cell goes `filled` and then stops."** The third step of the cycle is
  missing, or the ternary chain returns `state` for `crossed`. `crossed` must go
  back to `empty`.
- **"Clicking one cell resets a different cell."** They rebuilt the whole grid
  from scratch instead of copying it, or they mapped rows but rebuilt every cell
  from the clicked coordinates. Every other cell keeps the state it had.
- **"Every clue turns green but there is no banner."** `boardSolved` is checking
  rows only, or it is `or` where it should be `and`. This is exactly c-2-1's
  second request.
- **"The banner is there but a column clue is not green."** Then `boardSolved`
  and `lineStatus` disagree, which should be impossible - they apply the same
  rule to the same lines. Look for a `boardSolved` that reads the two status
  lists instead of re-deriving from the grid.
- **"I get a 400 from the check endpoint."** The posted grid is not `size` rows
  of `size` cells, or a cell is not one of the three strings. Almost always a
  `cut-cell-cycle` that wrote `true`, `1` or `"fill"` into a cell.
- **"The strips flicker back to `open` while I click fast."** They should not,
  and if they do the sequence guard in `sendCheck` has been edited. Nothing
  grades that behaviour, but it is shipped and it is correct.

## Check before moving on

Do this on the projector, and let them do it after:

1. Open `/puzzles/blanks`. Click the five cells of row 1. Watch `row-clue-1` turn
   green while everything else stays as it was.
2. Click column 0 and column 4 of row 2, then columns 1, 2 and 3 of row 3, then
   columns 0, 2 and 4 of row 4. Leave row 0 alone - it is an empty row and its
   `0` clue is already satisfied by an empty line.
3. On the last click, all ten clues read green and the `Solved` banner appears.

Then the full run: `BASE_URL=http://localhost:3000 python -m pytest verify -q` -
eleven passed.

If you had to walk `cut-board-solved` rather than have them type it, that is the
homework: `boardSolved`, and the c-2-1 case that proves rows alone are not
enough.
