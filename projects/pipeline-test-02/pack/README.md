# Clue - instructor pack

A nonogram board you fill by clicking. Two 40-minute sessions.
Next.js 15 App Router, React 19, TypeScript, CSS Modules.

## What the students end up with

One screen, `/puzzles/[id]`. It draws a square grid of empty cells, with a
run-length clue above every column and to the left of every row. Clicking a cell
moves it one step around `empty` -> `filled` -> `crossed` -> `empty`. Every click
posts the whole grid to `POST /api/puzzles/[id]/check`, which grades each row and
each column against its clue and answers `satisfied`, `open` or `violated` per
line, plus one `solved` flag. Each clue carries its own answer in `data-status`,
so a line turns green the moment it is right, and a banner reading `Solved`
appears when every row and every column is satisfied at once.

There are three puzzles: `boat` (5x5), `blanks` (5x5) and `house` (8x8). There is
no index page. A puzzle is reached by typing its id into the address bar. `/`
redirects to `/puzzles/boat`.

## The one idea the whole project hangs on

No clue is ever written down. A puzzle is seeded as its solution and nothing
else - one string per row, `#` for a filled cell, `.` for a blank one:

```ts
type Seed = {
  id: string
  title: string
  rows: string[]
}

const SEEDS: Seed[] = [
  {
    id: 'boat',
    title: 'Boat',
    rows: [
      '..#..',
      '.###.',
      '#####',
      '.#.#.',
      '.#.#.',
    ],
  },
  {
    id: 'blanks',
    title: 'Blanks',
    rows: [
      '.....',
      '#####',
      '#...#',
      '.###.',
      '#.#.#',
    ],
  },
  {
    id: 'house',
    title: 'House',
    rows: [
      '...##...',
      '..####..',
      '.######.',
      '########',
      '.#....#.',
      '.#.##.#.',
      '.#.##.#.',
      '.#....#.',
    ],
  },
]
```

Both clue strips are derived from that solution by one function, `runsOf`,
applied to the rows and then to the output of `transpose`:

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

That is the sentence to say out loud on day one: **one function reads a line, and
the whole project is that function applied to the rows and then to the columns.**
Write `runsOf` correctly and it grades both axes. Write it carelessly and half
the board lies.

## Sessions

| Session | Title | Cuts | Criteria |
|---|---|---|---|
| 1 | Setup, the boards, and the clues | `cut-runs-of`, `cut-transpose` | c-1-1 .. c-1-5 |
| 2 | Filling, checking, and solved | `cut-line-status`, `cut-cell-cycle`, `cut-board-solved` | c-2-1 .. c-2-6 |

**Timing verdict (read this before you teach).** Session 1 fits 40 minutes.
Session 2 does not: timed against the spec's own budget it runs to about 48
minutes, an overrun of 8. See the box at the top of `session-2.md` for the two
places to take the time back. This is the same failure shape `learning/lessons.md`
records three times in a row - the session carrying one oversized cut - and here
that cut is `cut-line-status`.

## The five cut points

| cut | file | skeleton line | lines removed | session | red on its own |
|---|---|---|---|---|---|
| `cut-runs-of` | `lib/nonogram.ts` | 29 | 18 | 1 | c-1-1 |
| `cut-transpose` | `lib/nonogram.ts` | 60 | 11 | 1 | c-1-2 |
| `cut-line-status` | `lib/nonogram.ts` | 85 | 18 | 2 | c-2-2 |
| `cut-board-solved` | `lib/nonogram.ts` | 121 | 8 | 2 | c-2-1 |
| `cut-cell-cycle` | `app/puzzles/[id]/Board.tsx` | 83 | 13 | 2 | c-2-5 |

(Line numbers are from `skeleton/.cut-manifest.json` and point at the TODO
comment in the file the student opens.)

Four of the five are pure functions in `lib/nonogram.ts`. The fifth is one
assignment inside a click handler. Everything else - the App Router tree, the
types, the seed, both route handlers, the whole board component, the CSS - ships
written.

## Two tests are green before the students write anything

`c-1-5` (the not-found screen) and `c-2-4` (404 and 400 on the check endpoint)
have no cuts. They pass on the untouched skeleton, and they are there to grade
the Builder's own branches. If a student reports "two tests already pass", that
is correct and expected. Nine of the eleven are red at the start.

## What runs at the start of session 1

The skeleton builds and serves. `/puzzles/boat` draws 25 empty cells, five empty
clue boxes down the left, and **no clue strip across the top at all** - because
`transpose` hands back an empty array, so `colClues` is `[]` and there is nothing
to map. Clicking a cell does nothing visible. That is the starting picture, and
it is worth showing on the projector before you explain why.

## Running it

```bash
cd skeleton          # or app/ for the finished reference
npm install
npm run dev
```

Then open <http://localhost:3000> - it redirects to `/puzzles/boat`. The other
two boards are `/puzzles/blanks` and `/puzzles/house`.

`package.json` scripts are `dev`, `build` and `start`. The pinned versions:

- `next` 15.5.24, `react` 19.0.0, `react-dom` 19.0.0
- `typescript` ^5.7.3, `@types/react` ^19, `@types/node` ^22

## Running the test suite

The suite is Python: pytest + Playwright for the screen, httpx for the API. It
never starts a server - it reads the URL out of `BASE_URL`.

```bash
npm run build && npm run start          # in one shell
BASE_URL=http://localhost:3000 python -m pytest verify -q   # in another
```

First time only: `pip install pytest playwright httpx && playwright install chromium`.

One test file per surface:

| file | criteria |
|---|---|
| `verify/test_api_puzzles.py` | c-1-1, c-1-2, c-1-3 |
| `verify/test_ui_board.py` | c-1-4, c-1-5 |
| `verify/test_api_check.py` | c-2-1, c-2-2, c-2-3, c-2-4 |
| `verify/test_ui_clicks.py` | c-2-5, c-2-6 |

To check just one session: `-k "c_1_"` or `-k "c_2_"`.

## File map

```
lib/nonogram.ts                    runsOf, transpose, lineStatus, boardSolved   <- 4 cuts
lib/puzzles.ts                     the three seeds and the derivation           <- ships whole
app/page.tsx                       redirect / -> /puzzles/boat                  <- ships whole
app/layout.tsx                     html/body shell                              <- ships whole
app/globals.css                    colour variables                             <- ships whole
app/api/puzzles/route.ts           GET /api/puzzles                             <- ships whole
app/api/puzzles/[id]/check/route.ts  POST .../check                             <- ships whole
app/puzzles/[id]/page.tsx          server component, reads the route id         <- ships whole
app/puzzles/[id]/Board.tsx         the whole screen                             <- 1 cut
app/puzzles/[id]/board.module.css  grid, clue colours, cell states              <- ships whole
```

## The types students will see all day

```ts
export type Cell = 'empty' | 'filled' | 'crossed'

export type LineStatus = 'satisfied' | 'open' | 'violated'

export type CheckResult = {
  rows: LineStatus[]
  cols: LineStatus[]
  solved: boolean
}
```

## The clue tables, for checking work at a glance

| puzzle | rowClues | colClues |
|---|---|---|
| `boat` | `[[1],[3],[5],[1,1],[1,1]]` | `[[1],[4],[3],[4],[1]]` |
| `blanks` | `[[0],[5],[1,1],[3],[1,1,1]]` | `[[2,1],[1,1],[1,2],[1,1],[2,1]]` |
| `house` | `[[2],[4],[6],[8],[1,1],[1,2,1],[1,2,1],[1,1]]` | `[[1],[6],[3],[4,2],[4,2],[3],[6],[1]]` |

`boat` and `house` both have colClues that differ from their rowClues, so a
`transpose` that hands back the rows unchanged is caught. `blanks` has `[1,2]` in
one column and `[2,1]` in another, so a `transpose` that reverses a column is
caught too.

## Files in this pack

- `README.md` - this page
- `session-1.md` - Setup, the boards, and the clues
- `session-2.md` - Filling, checking, and solved
- `troubleshooting.md` - every error a student actually hits, with the fix
