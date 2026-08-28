# Session 1 - Boards and the solved view

**Time:** 40 minutes
**Students start from:** the student tree with `npm install` already done and
`npm run dev` running. `/boards/intro/solved` loads, shows the title
`Intro - solved` and an empty grid. `GET /api/boards/intro` answers 200 with
`"counts": []`. Five criteria are already green: `c-1-3`, `c-1-6`, `c-2-3`,
`c-2-4`, `c-3-1`.
**Students end with:** all three boards drawn face up at `/boards/[id]/solved`,
a `*` on every mine and a neighbour count everywhere else. `c-1-1`, `c-1-2`,
`c-1-4` and `c-1-5` go green, so all six of session 1's criteria pass.

## What they learn

1. A fixed grid is a flat array. The cell at column `x`, row `y` is index
   `y * width + x`, and that one integer is the cell's name everywhere - in
   `mines`, in `counts`, in `data-index`, in a request body.
2. The eight-offset neighbour scan, and the bounds test that makes a corner
   cell weigh 3 neighbours and an edge cell 5.
3. Drawing a grid from a flat array, with `data-testid` and `data-*` hooks a
   test can read - because CSS Modules hashes every class name, so a test can
   never read a class.

## Before you start

- `npm install` must already have been run in every student tree. It is the one
  thing that can eat 10 minutes of this session for nothing. If a machine is
  not ready, pair that student for today.
- `npm run dev` running, `/boards/intro/solved` open in a browser.
- Open in the editor: `lib/boards.ts`, `lib/board.ts`,
  `app/boards/[id]/solved/page.tsx`.
- The solved drawings of all three boards from `README.md` on the projector or
  the whiteboard. You will point at them all session.
- Also have `http://localhost:3000/api/boards/intro` open in a second tab. It
  is how the class sees `counts` change.

## The plan

| Minutes | What you do |
|---|---|
| 0-5 | What Sweeper is, and the one rule the whole project rests on: a board is a flat array, the cell at column `x` row `y` is index `y * width + x`. Draw the 5x5 `intro` grid, write the index in every square, then write the mines 9, 11, 18, 23 in. Show the empty grid the app draws today. |
| 5-13 | Walk the given code, in this order: the four types and `BOARDS` and `findBoard` in `lib/boards.ts`; the `GET /api/boards/[id]` handler; the solved page's fetch, its not-found branch and its empty `cells` fallback. Refresh `/api/boards/intro` and read `"counts": []` out loud - that is the hole they are about to fill. |
| 13-25 | `cut-neighbour-counts`. Count the neighbours of a corner square on the whiteboard, out loud, before any code. Write the two loops and the counter live, then hand over the eight-offset scan and its bounds test. |
| 25-32 | `cut-solved-cells`. One element per index, the four attributes, the three text cases. Write the first two attributes live, hand over the rest. |
| 32-38 | Students finish both. Circulate. Refresh `/api/boards/intro` first, then the page - a broken count shows up in the JSON before it shows up in the grid. |
| 38-40 | Run session 1's criteria. What runs now, and what session 2 does with it: the same `counts` array decides which squares open in one click. |

## Cut points in this session

### cut-neighbour-counts - `lib/board.ts`:36

**What students see** - the fallback, the TODO and the return, exactly as the
file hands them over:

```ts
export function neighbourCounts(
  width: number,
  height: number,
  mines: number[],
): number[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles and every criterion that reads a count is red
  const counts: number[] = []

  // TODO(cut-neighbour-counts): Fill `counts` with one number per cell of the board, in index order, where the number at index `y * width + x` is how many of that cell's 8 neighbours appear in `mines`. A cell that is itself a mine still gets its own neighbour count. Skip any neighbour that falls off the edge, so a corner cell weighs 3 neighbours and an edge cell 5, and `counts` ends up exactly `width * height` long.

  return counts
}
```

The eight offsets are given to them above the function, so nobody spends this
session typing coordinate pairs:

```ts
/** The eight neighbour offsets as [dx, dy], clockwise from the top left. */
const OFFSETS: ReadonlyArray<readonly [number, number]> = [
  [-1, -1],
  [0, -1],
  [1, -1],
  [-1, 0],
  [1, 0],
  [-1, 1],
  [0, 1],
  [1, 1],
]
```

**What they write:** a loop over every row `y`, and inside it a loop over every
column `x`. For each cell, start a counter at zero, walk the eight offsets, add
the offset to `x` and `y` to get `nx` and `ny`, skip that neighbour when `nx`
or `ny` falls outside the board, and add one to the counter when
`ny * width + nx` is a mine. Store the counter at `counts[y * width + x]`.
Building a `Set` from `mines` once, before the loops, turns the mine lookup
into one step instead of a scan of the array per neighbour.

**Teach it like this:** point at the top-left square of the drawn `intro` grid
and count its neighbours out loud - three, not eight. Then an edge square -
five. The bounds test is the only thing in the code that makes that true. Then
show them why it bites: index -1 is not "off the board" to a flat array, it is
the last cell of the row before, so a missing test silently wraps a row.

**Passes when:** `c-1-1` goes green (the whole 25-number `counts` array for
`intro`) and `c-1-2` goes green (64 numbers for `field`, read at all four
corners, three edges and the interior cell 54, whose count of 3 is the highest
on the board).

### cut-solved-cells - `app/boards/[id]/solved/page.tsx`:64

**What students see** - the fallback, the TODO, and the grid that is already
written below it:

```tsx
  const board: BoardView = view
  const counts = board.counts

  // the fallback stays above the marker, so the skeleton draws 0 cells
  const cells: ReactElement[] = []

  // TODO(cut-solved-cells): Fill `cells` with one element per index of `board`, in index order, each carrying `data-testid` `cell`, `data-index` set to that index, `data-count` set to that index's entry in `counts`, and `data-mine` set to the string `true` when `board.mines` holds the index and the string `false` when it does not. A mine cell shows the text `*`, a non-mine cell whose count is 0 shows empty text, and every other cell shows its count.

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>{`${board.name} - solved`}</h1>
      <div
        className={styles.grid}
        data-testid="board-grid"
        data-width={board.width}
        data-height={board.height}
        style={{ gridTemplateColumns: `repeat(${board.width}, 2rem)` }}
      >
        {cells}
      </div>
    </main>
  )
```

**What they write:** a loop from `0` to `board.width * board.height - 1`. For
each index, read `counts[index]` and ask whether `board.mines` holds the index.
Push one element per cell into `cells` carrying `data-testid` set to `cell`,
`data-index` set to the index, `data-count` set to that index's count, and
`data-mine` set to the string `true` or the string `false` - write those two
words out as strings, do not hand React a boolean. The visible text has three
cases: `*` when the cell is a mine, empty when it is not a mine and its count
is 0, and the count as digits otherwise. Give each element a `key`.

**Teach it like this:** the array is flat, so the loop is flat - there is no
inner loop and no array of rows. The wrapping into a 5-wide grid is already
done for you by `gridTemplateColumns` on the `board-grid` element, which is
built from `board.width`. Two sentences on why the attributes exist: class
names are hashed by CSS Modules, so the test suite reads `data-testid` and the
`data-*` attributes and nothing else. If they rename one, the criterion cannot
find the cell.

**Passes when:** `c-1-4` goes green (25 cells on `intro`, `data-mine` true on
exactly 9, 11, 18 and 23, and `data-count` 0, 1, 2, 3 and 2 on cells 0, 3, 12,
17 and 24) and `c-1-5` goes green (16 cells on `corner`, cell 10 reading `3`,
cell 15 reading `*`, and cells 0, 1 and 4 blank with `data-count` 0).

**Order matters.** Tell the class to fill `cut-neighbour-counts` first. With it
still empty, `counts` is an empty array, so every non-mine square on the solved
page renders the word `undefined` and the grid looks broken for a reason that
is not in the file they are editing.

## Where students get stuck

- **"Every square says `undefined`."** - `counts` is still the empty fallback in
  `lib/board.ts`, and `counts[index]` on an empty array is `undefined`. - "The
  page is fine. You are reading a count that nobody has computed yet. Finish
  `lib/board.ts` and refresh."
- **"My numbers are too big down the left-hand edge."** - No bounds test on
  `nx`. On `intro`, cell 5 comes out as 2 instead of 1: the neighbour at
  `nx = -1, ny = 2` computes `2 * 5 - 1 = 9`, and index 9 is a mine on the row
  below and the far side. On `field`, cell 8 comes out as 2 instead of 1 the
  same way, by picking up the mine at index 15. - "You did not go off the board.
  You went round the corner of it. Add the four-way test on `nx` and `ny` before
  you look anything up."
- **"c-1-1 says my counts array has `null` in it."** - They looped over
  `mines` and did `counts[n] += 1` on the neighbours, which leaves holes in the
  array; JSON prints a hole as `null`, and the array can end up shorter than
  `width * height`. - "Loop over cells and ask about mines. Do not loop over
  mines and write into cells - a flat array with holes is not a flat array of
  numbers."
- **"Every empty square shows a 0."** - They rendered the count straight out.
  The rule is: a non-mine cell whose count is 0 shows *empty text*, and `c-1-5`
  reads cells 0, 1 and 4 on `corner` as empty. - "Zero is a real count and it
  still belongs in `data-count`. It is only the visible text that is blank."
- **"The mine squares lost their number."** - They set `data-count` only on
  non-mines, or let the `*` replace the count. A mine still gets its own
  neighbour count: `corner` cell 15 shows `*` and carries `data-count` 2;
  `field` cell 63 is a mine whose count is 0. - "The glyph is the text. The
  count is the attribute. They are two different things and `c-1-4` reads
  both."
- **"I get 0 cells on the page and my loop is right."** - They looped over
  `counts` instead of over the index range, and `counts` is empty until
  `lib/board.ts` is done. - "Iterate `board.width * board.height`. The number of
  squares on the page must not depend on the neighbour scan."
- **"Warning: each child in a list should have a unique key."** - No `key` on
  the pushed element. - Harmless for the criteria, one word to fix, fix it now.
- **"It says Board not found."** - The id in the URL is not `intro`, `field` or
  `corner`. That page is the given not-found state working correctly, and it is
  what `c-1-6` grades. - "Read your URL. There are exactly three boards."

## Check before moving on

`/boards/field/solved` draws the 8x8 grid with numbers that match the drawing
on the whiteboard, corners included, and `/boards/corner/solved` shows `3` at
cell 10 next to a `*` at 15. Then run session 1's tests: `c-1-1`, `c-1-2`,
`c-1-3`, `c-1-4`, `c-1-5` and `c-1-6` all green. Session 2 builds directly on
`counts` - if the scan is wrong at the edges, the flood fill will be wrong in a
way that looks like a flood fill bug.
