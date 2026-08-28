# Session 2 - Reveal and flood fill

**Time:** 46 minutes. **This session does not fit the 40-minute cap. It
overruns by 6.** Read the next paragraph before you plan the day.

**Students start from:** the solved view working and all six session-1 criteria
green. `/boards/field` already draws 64 face-down cells, a `Flag mode: off`
button, `Mines left: -1` and `Playing`; `c-2-4` grades that and is green before
the session starts. Clicking a cell does nothing at all.
**Students end with:** a board that opens. One click on a zero opens the whole
region of zeros plus the numbers fringing it, at the API and on the screen.
`c-2-1`, `c-2-2`, `c-2-5` and `c-2-6` go green.

## The overrun, and what to trim

The spec budgets 20 of this session's 40 for `cut-reveal-from` and leaves no
slack anywhere else. A breadth-first walk written from scratch by a class, run,
and then debugged past the one wrong answer most of them get first - a fill that
walks through numbered cells and opens 54 cells instead of 14 - needs about 26,
not 20. Everything else in the plan below is already at its floor. Hence 46.

Two ways to trim it, cheapest first:

1. **Hand over the queue frame.** If `cut-reveal-from` started below the
   `visited` set, the `queue` and the loop over it, and asked only for the
   eight-neighbour scan and the one `continue` that stops the fill at a number,
   the block is 6 minutes shorter and still grades the only idea that matters.
   That is a Gate 1 change to the cut, not something to improvise in the room.
2. **Move `cut-play-click` to session 3.** This session lands at 40, session 3
   goes to roughly 46, and session 3 has only about 4 minutes of slack - so
   this moves the overrun rather than removing it.

If you have to teach it as it stands today, run over and take the 6 minutes off
the start of session 3's recap, and tell session 3 to expect it.

## What they learn

1. A breadth-first walk over a grid: an explicit queue, a visited set, and why
   you mark a cell visited when you push it, not when you pop it.
2. The boundary rule - a numbered cell is opened but never walked out of. This
   is the whole lesson of the session and the only thing `c-2-1` grades.
3. Merging a set of indices returned by a pure function into React state,
   without duplicates and without mutating the array that is already in state.

## Before you start

- `npm run dev` running, `/boards/field` open, and the `field` drawing from
  `README.md` on the whiteboard with indices 0 to 7 written along the top row.
- Open in the editor: `lib/reveal.ts` and `app/boards/[id]/page.tsx`.
- A terminal ready to hit the replay endpoint, because it is the fastest way to
  show the class an answer with no browser in the way:

```bash
curl -s localhost:3000/api/boards/field/replay \
  -H 'content-type: application/json' -d '{"clicks":[0]}'
```

- Know the two numbers cold: a correct click on `field` index 0 opens **14**
  cells, and a fill that walks through numbers opens **54**.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap: `counts` is done, and it is the only input the fill needs. Set the problem on the `field` drawing - click index 0, and mark by hand which squares should open. Land on 14, and on the reason index 7 stays shut. |
| 4-10 | Walk the two given pieces. First `POST /api/boards/[id]/replay`: it resolves the board before it reads the body, validates `clicks`, then folds the clicks one at a time. Then the face-down grid in `app/boards/[id]/page.tsx` and the two empty branches of `onCellClick`. |
| 10-18 | Teach the walk on the whiteboard, then write the frame live in `lib/reveal.ts`: the early exit for a mine or a numbered cell, the `visited` set, the queue and the loop that drains it. Do not write the neighbour scan. |
| 18-32 | Students write the neighbour scan and the boundary rule. Circulate with the curl command - a student who gets 54 has the boundary rule; a student whose tab freezes has the visited set. |
| 32-38 | `cut-play-click`. Two sentences on why a new array is required, then they write it. First click on the screen. |
| 38-44 | Students finish both, run session 2's four criteria, and try `intro` by hand: index 3 opens one cell, index 20 opens six. |
| 44-46 | What runs now. Session 3 makes the game end and adds flags. |

## Cut points in this session

### cut-reveal-from - `lib/reveal.ts`:36

**What students see** - the counts are computed for them above the cut, and the
sort and de-duplication are done for them below it:

```ts
export function revealFrom(board: Board, index: number): number[] {
  const { width, height, mines } = board
  const counts = neighbourCounts(width, height, mines)

  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles and a click opens nothing
  const opened: number[] = []

  // TODO(cut-reveal-from): Fill `opened` with every index that a single click on `index` opens. A mine cell, or a cell whose entry in `counts` is above 0, opens only itself. A cell whose count is 0 opens itself, every zero-count cell reachable from it through the 8 neighbour offsets, and every cell bordering that region - but a cell whose count is above 0 is added and never walked out of, which is the rule that stops the fill at the numbers. Keep a visited set so the walk ends. Traversal order is free: the code below the markers sorts `opened` ascending and drops duplicates.

  return Array.from(new Set(opened)).sort((a, b) => a - b)
}
```

The eight offsets are given again in this file, so nobody retypes them:

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

**What they write:** first the easy half - if `index` is a mine, or
`counts[index]` is above 0, then `opened` holds that one index and nothing
else. Test the mine first. Otherwise start a `visited` set holding `index` and
a queue holding `index`. While the queue has anything left in it, take the next
cell, push it into `opened`, and stop there if its count is above 0. If its
count is 0, turn the cell back into `x` and `y` (`current % width` and
`Math.floor(current / width)`), walk the eight offsets, skip a neighbour that
falls off the board, and push any neighbour that is not already in `visited`
into both `visited` and the queue. Traversal order does not matter: the code
below the markers sorts and de-duplicates.

**Teach it like this:** "Opening a zero opens everything that zero can see, and
stops at the first number in every direction." Walk it on the drawing: put a
finger on index 0, spread across the zeros of the top two rows, and stop dead on
the 1s. Then say the rule twice, because it is the whole session: **a numbered
cell is added to the set and never walked out of.** The `continue` after pushing
a numbered cell is the line that does it, and it is the line most of them will
forget. Then the visited set: mark a cell the moment you push it onto the queue,
or the same cell is queued from three neighbours and the walk never ends.

**Passes when:** `c-2-1` goes green - 14 entries reading 0, 1, 2, 3, 4, 5, 6, 8,
9, 10, 11, 12, 13, 14 for one click on `field` index 0 - and `c-2-2` goes green,
which clicks a zero, a number and a mine on `intro` and expects 6 cells, 1 cell
and 1 cell. Both are graded through the replay endpoint, with no browser
involved, so they can be green before the screen works.

### cut-play-click - `app/boards/[id]/page.tsx`:60

**What students see** - both branches of the click handler, one of them this
session's and one of them session 3's:

```tsx
  function onCellClick(index: number): void {
    if (view === null) {
      return
    }

    const board: BoardView = view

    if (flagMode) {
      // TODO(cut-flag-toggle): This block is the flag branch of `onCellClick`, reached when flag mode is on. When `revealed` already holds `index`, leave both states exactly as they are, so an open cell cannot be flagged. Otherwise set the `flagged` state to a new array holding `flagged` with `index` added when it is absent and dropped when it is already present. Leave the `revealed` state as it was in both branches, so a click in flag mode never opens a cell.
    } else {
      // TODO(cut-play-click): This block is the reveal branch of `onCellClick`, reached when flag mode is off. When `flagged` already holds `index`, leave both states exactly as they are, so a flag protects its cell from being opened. Otherwise set the `revealed` state to a new array holding every index already in `revealed` together with every index in `revealFrom(board, index)`, with no index appearing twice, so a click on an already-open cell changes nothing. Leave the `flagged` state as it was in both branches.
    }
  }
```

The grid below it is given, and it is worth reading out: the cell text and the
two `data-` attributes are all derived from `revealed` and `flagged`, so the
only thing a click has to do is replace one of those two arrays.

```tsx
  for (let index = 0; index < board.width * board.height; index += 1) {
    const isOpen = openCells.has(index)
    const isFlagged = flaggedCells.has(index)
    const isMine = minedCells.has(index)
    const count = board.counts[index]

    let text = ''

    if (!isOpen) {
      text = isFlagged ? 'F' : ''
    } else if (isMine) {
      text = '*'
    } else if (count !== 0) {
      text = String(count)
    }
```

**What they write:** in the `else` branch only. If `flagged` already holds
`index`, do nothing at all - a flag protects its cell. Otherwise call
`revealFrom(board, index)` and set the `revealed` state to a **new** array made
of everything already in `revealed` plus every index the call returned, with
nothing appearing twice. Do not touch `flagged` in this branch.

**Teach it like this:** `revealFrom` is a pure function - it knows nothing about
React and returns the same answer every time for the same board and index. The
click handler's only job is to merge that answer into state. Two sentences on
why it must be a new array: React compares the array it was given with the one
it has, and `push` gives it back the same array, so nothing re-renders. Then the
union: clicking an already-open cell must change nothing, which is what `c-2-6`
checks by clicking the same cell twice.

**Passes when:** `c-2-5` goes green (one click on `field` cell 0 leaves exactly
14 cells at `data-revealed` true, cell 7 still false, cell 6 reading `1` and
cell 0 blank) and `c-2-6` goes green (on `intro`: click 3 leaves 1 cell open,
then click 20 leaves 7 open in total, then clicking 3 again still leaves 7).
Note the counting rule: those numbers are the total open on the page after the
click, never the number of cells that changed.

## Where students get stuck

- **"My click opens the whole board."** - The fill walks out of numbered cells.
  On `field` they get 54 open instead of 14, and it looks impressive. - "You are
  opening the numbers, which is right, and then walking out of them, which is
  not. Add the numbered cell to the set and then stop."
- **"The tab froze / page unresponsive."** - No visited set, or cells marked
  visited when they come off the queue instead of when they go on, so the same
  cell is queued many times and the queue outruns the walk. - "Mark it the
  moment you push it. Visited means queued, not finished."
- **"Clicking the mine at `intro` index 9 opens six cells."** - The count is
  tested before the mine. Index 9 is a mine that no mine touches, so its count
  is 0 and a count-first fill floods out of it. `c-2-2` grades exactly this. -
  "A mine can have a count of zero. Ask whether the cell is a mine first."
- **"Only the first row opens" or the fill runs sideways.** - `x` and `y` are
  swapped when turning an index back into coordinates. It is `current % width`
  for `x` and `current / width` floored for `y` - `width`, never `height`. On
  the 8x8 `field` the two are the same number and the bug hides; it shows up on
  the 5x5 `intro`.
- **"Nothing happens when I click anything."** - Flag mode was left on. The
  toggle button is given code and flips its own label from day one, but both
  branches of `onCellClick` were empty until now, so a board in flag mode is
  completely dead in session 2. - "Look at the button. It says on. That branch is
  session 3's work."
- **"The first click does nothing, then the second click opens both."** - They
  mutated the state array - `revealed.push(...)` and then set it back. React
  sees the same array and re-renders only when something else forces it. - "Make
  a new array. State you can push into is state React cannot see change."
- **"My `revealed` comes back in a strange order."** - It does not matter. The
  code below the markers sorts ascending and drops duplicates, and no criterion
  in this project pins a traversal order.
- **"The endpoint says 400 when I try it by hand."** - `clicks` must be a JSON
  array of integers inside the board, so `{"clicks": "0"}` and `{"clicks": [25]}`
  on `intro` are both rejected. That validation is given code and `c-2-3` grades
  it. - "Your curl body is wrong, not your fill."
- **"`c-2-4` used to pass and now it fails."** - They edited the given grid
  while looking for their bug. Nothing in this session should change the code
  below the click handler. - Restore it from the original student tree.

## Check before moving on

On `/boards/field`, one click on the top-left cell opens exactly 14 squares, the
top-right cell (index 7) stays shut, and cell 6 reads `1`. Then run the four
criteria: `c-2-1`, `c-2-2`, `c-2-5`, `c-2-6`. `c-2-3` and `c-2-4` must still be
green - if either has gone red, given code was edited. Session 3 adds flags and
the status line on top of this exact handler, so a click that opens the wrong
set here will read as a broken win rule there.
