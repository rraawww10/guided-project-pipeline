# Session 3 - Flags, status, and replay

**Time:** 40 minutes
**Students start from:** a board that opens. One click on a zero opens its
region, `c-2-1`, `c-2-2`, `c-2-5` and `c-2-6` are green. But the readouts are
still the fallbacks: `Mines left: -1` on every board whatever they do, the
status line stuck on `Playing`, and flag mode dead - the button changes its
label and clicking a cell with it on does nothing.
**Students end with:** a finished game. Flags plant and lift, the counter
tracks them and is allowed to go negative, and the status line reads `Won` or
`Lost`. `c-3-2`, `c-3-3`, `c-3-4`, `c-3-5` and `c-3-6` go green, which makes all
18 criteria green.

If session 2 ran over - it is planned to - take the time out of this session's
recap and its last catch-up block. This is the session with slack.

## What they learn

1. The win rule as arithmetic, not as bookkeeping: you have won when the number
   of distinct open cells equals cells minus mines. Nothing counts flags.
2. Branch order as a design decision. Open the last safe cell and a mine in the
   same list and the answer is `Lost`, because the mine is tested first.
3. A mode toggle that changes what one click means, and two branches that each
   have to guard the other's state.

## Before you start

- `npm run dev` running, `/boards/corner` open. `corner` is the board for this
  session: 4x4, three mines at 11, 14 and 15, and 13 safe cells that are one
  connected zero region, so a single click on cell 0 wins the game.
- Open in the editor: `lib/status.ts` and `app/boards/[id]/page.tsx`.
- A terminal for the replay endpoint. These three calls are the session in
  miniature - win, lose, and flags that change nothing:

```bash
curl -s localhost:3000/api/boards/corner/replay \
  -H 'content-type: application/json' -d '{"clicks":[0]}'
curl -s localhost:3000/api/boards/corner/replay \
  -H 'content-type: application/json' -d '{"clicks":[0,15]}'
curl -s localhost:3000/api/boards/corner/replay \
  -H 'content-type: application/json' -d '{"clicks":[6],"flags":[15,11,14,15]}'
```

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap on the drawn `corner` board: one click on cell 0 opens 13 of the 16 squares and the game should be over. Show that it still says `Playing`, and that `Mines left` has read -1 all along. Name the three things this session adds. |
| 4-8 | Walk the given `GET /api/boards` handler - the board index, and the one endpoint in the project that needs no new idea. Then run the first curl above and read the response: `revealed` has 13 entries and `status` is whatever their `lib/status.ts` says today, which is `lost`. |
| 8-16 | `cut-game-status`. Derive the win threshold on the board - 16 cells minus 3 mines is 13 - then the branch order. Students write it. Re-run the three curl calls: two of them go right immediately. |
| 16-24 | `cut-flag-toggle`. The toggle-in-an-array idiom and the guard against flagging an open cell. Students write it, then plant and lift a flag on screen. |
| 24-31 | `cut-play-status`. Two lines of arithmetic and a three-way mapping to the three strings. Students write it. The counter and the status line come alive together. |
| 31-38 | Students finish. Run the whole suite - all 18 criteria - and play `corner` and `intro` by hand. Circulate. |
| 38-40 | What they built: a grid as a graph, a pure flood fill, a rule expressed as arithmetic. Where it goes next - a bigger board, a timer, a first-click rule - and why none of that is in this project. |

## Cut points in this session

### cut-game-status - `lib/status.ts`:21

**What students see:**

```ts
export function gameStatus(board: Board, revealed: number[]): GameStatus {
  // the fallback stays above the marker and the return below it. `lost` is the
  // one constant that is the wrong answer to every status criterion.
  let status: GameStatus = 'lost'

  // TODO(cut-game-status): Set `status` to `lost` when any index in `revealed` is also in `board.mines`. Otherwise set `status` to `won` when the number of distinct indices in `revealed` equals `board.width * board.height` minus the number of entries in `board.mines`, and to `playing` in every other case. Test the mine case first, so a list that opens the last safe cell and a mine together reads `lost`. Flags are no part of this rule: a board with every mine flagged and 1 cell open is still `playing`.

  return status
}
```

**What they write:** three cases, in this order. If any index in `revealed` is
also in `board.mines`, `status` is `lost`. Otherwise, if the number of
*distinct* indices in `revealed` equals `board.width * board.height` minus the
number of entries in `board.mines`, `status` is `won`. Otherwise it is
`playing`. A `Set` for the mines and a `Set` for the revealed indices makes both
tests one line each.

**Teach it like this:** count it out on the `corner` drawing - 16 squares, 3
mines, so 13 safe squares, so you have won when 13 distinct squares are open.
Then ask the class the question the criterion is built on: what if the list
opens 13 safe squares *and* a mine? Both rules fire. The spec says `lost`, and
the only thing that makes it `lost` is testing the mine first. Say the other
half too: flags are no part of this rule. A board with all three mines flagged
and one cell open is still `playing`, which is what `c-3-4` checks.

**Passes when:** `c-3-2` goes green (`won` for one click on `corner` cell 0,
`playing` for one click on cell 6), `c-3-3` goes green - and its third case is
the one that grades the branch order: nine clicks on `intro` open 21 distinct
cells against a win threshold of 25 minus 4, one of them the mine at index 9, and
the answer must be `lost` - and `c-3-4` goes green, three flags on `corner` with
one cell open, still `playing`.

### cut-flag-toggle - `app/boards/[id]/page.tsx`:58

**What students see** - the flag branch, above the reveal branch they wrote last
session:

```tsx
    if (flagMode) {
      // TODO(cut-flag-toggle): This block is the flag branch of `onCellClick`, reached when flag mode is on. When `revealed` already holds `index`, leave both states exactly as they are, so an open cell cannot be flagged. Otherwise set the `flagged` state to a new array holding `flagged` with `index` added when it is absent and dropped when it is already present. Leave the `revealed` state as it was in both branches, so a click in flag mode never opens a cell.
    } else {
      // TODO(cut-play-click): This block is the reveal branch of `onCellClick`, reached when flag mode is off. When `flagged` already holds `index`, leave both states exactly as they are, so a flag protects its cell from being opened. Otherwise set the `revealed` state to a new array holding every index already in `revealed` together with every index in `revealFrom(board, index)`, with no index appearing twice, so a click on an already-open cell changes nothing. Leave the `flagged` state as it was in both branches.
    }
  }
```

**What they write:** in the `if (flagMode)` branch only. If `revealed` already
holds `index`, do nothing - an open cell cannot be flagged. Otherwise set the
`flagged` state to a new array: the same indices with `index` removed if it is
already there, or added if it is not. Do not touch `revealed` in this branch.

**Teach it like this:** one click, two meanings, and the mode decides which.
Then the idiom, which is the reusable part: to toggle a value in an array of
values, ask whether it is in there - filter it out if it is, spread and append
if it is not. Same rule as last session about a new array, and this time they
have already met it. Finally the guard, and why it is not fussiness: `c-3-5`
flags an open cell on purpose and expects the counter not to move.

**Passes when:** `c-3-5` goes green, together with `cut-play-status`. It drives
the whole sequence on `corner`, in this order:

```text
flag-mode on
click 15  -> that cell data-flagged true, data-revealed false, text F, Mines left: 2
click 14  -> Mines left: 1
click 15  -> that cell data-flagged false, Mines left: 2
click 15, 11, 0 -> Mines left: -1
flag-mode off
click 0   -> 0 cells open (the flag protects it), Mines left: -1
click 6   -> exactly 1 cell open
flag-mode on, click 6 -> still data-flagged false, Mines left: -1
```

### cut-play-status - `app/boards/[id]/page.tsx`:88

**What students see** - the two fallbacks and the TODO:

```tsx
  const board: BoardView = view

  // the fallbacks stay above the marker, so the skeleton reads
  // "Mines left: -1" and "Playing" whatever the board is
  let minesLeft = -1
  let statusText = 'Playing'

  // TODO(cut-play-status): Set `minesLeft` to the number of entries in `board.mines` minus the number of entries in `flagged`, which is allowed to go below 0 and must not be clamped. Set `statusText` from `gameStatus(board, revealed)` to the string `Playing`, `Won` or `Lost`, mapping the three `playing`, `won` and `lost` values one for one.
```

And the readouts they feed, which are already written:

```tsx
      <div className={styles.readouts}>
        <button
          type="button"
          className={styles.toggle}
          data-testid="flag-mode"
          onClick={() => {
            setFlagMode(!flagMode)
          }}
        >
          {`Flag mode: ${flagMode ? 'on' : 'off'}`}
        </button>
        <span data-testid="mines-left">{`Mines left: ${minesLeft}`}</span>
        <span data-testid="game-status">{statusText}</span>
      </div>
```

**What they write:** two things. `minesLeft` is the number of entries in
`board.mines` minus the number of entries in `flagged` - plain subtraction, no
clamp, it is allowed to go below 0. `statusText` comes from calling
`gameStatus(board, revealed)` and mapping its three values one for one to the
strings `Playing`, `Won` and `Lost`.

**Teach it like this:** the counter is not a count of mines you have found, it
is mines minus flags - the game has no idea whether a flag is right. Plant a
fourth flag on a three-mine board and it reads -1, and that is correct. On the
mapping, one sentence: the module speaks lowercase, the screen speaks
capitalised, and this line is the only place the two meet.

**Passes when:** `c-3-6` goes green - click cell 0 on `corner`, 13 cells open
and the status reads `Won`; click cell 9 on `intro`, 1 cell opens showing `*`
and the status reads `Lost`; then one more click on cell 3 opens a second cell
and the status still reads `Lost`. `c-3-5` needs this cut too, for the counter.

## Where students get stuck

- **"My replay says `won` when it should say `lost`."** - They tested the win
  count before the mine. It is the only input in the project where the two
  orders disagree, and `c-3-3` uses it deliberately: 21 open cells on `intro`,
  win threshold 21, and one of the 21 is a mine. - "Both rules are true at once
  there. We chose which one wins, and it is the mine."
- **"I win as soon as I flag all the mines."** - They wrote the rule about
  flags. `c-3-4` flags all three mines on `corner` with one cell open and
  expects `playing`. - "Flags are a note to yourself. The game never reads
  them."
- **"The status never reaches `Won`."** - They counted `revealed.length` instead
  of the distinct indices, and their reveal handler appended duplicates in
  session 2. - "Put it in a Set and count that. Then you do not care what the
  click handler did."
- **"`Mines left` stops at 0."** - They clamped it with `Math.max(0, ...)`.
  `c-3-5` plants a fourth flag on a three-mine board and reads `Mines left: -1`.
  - "Nothing is wrong with -1. It is telling the player they have over-flagged."
- **"The status line shows `won` in lower case."** - They rendered the value
  from `gameStatus` straight into `statusText`. The screen wants `Playing`,
  `Won`, `Lost`. - The criteria read the exact string.
- **"Flag mode is on but nothing plants."** - Either they wrote into the wrong
  branch (the `else` is last session's reveal branch), or they mutated the
  array with `push`/`splice` and set the same array back. - "Which branch is
  your cursor in? And is that a new array?"
- **"I flagged a cell and then it opened anyway."** - The reveal branch's guard
  is missing or inverted. That guard is session 2's code, and `c-3-5` is the
  first criterion that drives it: with flag mode off, a click on the flagged
  cell 0 on `corner` must leave 0 cells open, not 13. - "Your flag is not
  protecting the cell. Go back to the `else` branch."
- **"I flagged an open cell and the counter moved."** - The flag branch's guard
  is missing. Last line of `c-3-5`. - Same fix, other branch.
- **"I locked the board when the game ends and now a test fails."** - The spec
  says the board is not locked: a click after `Won` or `Lost` opens or flags its
  cell exactly as before, and `c-3-6`'s last step clicks after `Lost` and
  expects the cell to open. - "It looks wrong and it is what we specified. No
  cut hint mentions the status, which is the tell."
- **"`c-3-1` went red."** - `GET /api/boards` is given code that nobody should
  have touched today. Restore it.

## Check before moving on

Run the whole suite. All 18 criteria - `c-1-1` through `c-3-6` - green on the
student's own tree. Then play it: on `/boards/corner`, one click on the
top-left square opens 13 cells and the line reads `Won`. On `/boards/intro`,
flag a couple of squares, watch `Mines left` move, click the mine at index 9 and
read `Lost`. That is the project.
