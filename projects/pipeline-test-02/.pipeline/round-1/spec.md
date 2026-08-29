# Clue

Two 40-minute sessions. Next.js 15 App Router, React 19, TypeScript, CSS
Modules. Three puzzles are compiled into the project as TypeScript. Nothing is
written to disk at runtime, there is no database, no API key and no network call
out of the app.

## Outcome

A nonogram board you fill by clicking. Screen `/puzzles/[id]` draws one seeded
puzzle as a square grid of empty cells, with a run-length clue above every
column and to the left of every row. Clicking a cell moves it one step around
`empty` -> `filled` -> `crossed` -> `empty`. Every click posts the whole grid to
`POST /api/puzzles/[id]/check`, which grades each row and each column against
its clue and answers `satisfied`, `open` or `violated` per line plus a single
`solved` flag. Each clue strip carries its own answer as `data-status`, so a
line turns green the moment it is right, and a banner reading `Solved` appears
when every row and every column is satisfied at once.

The clues are never authored. Each puzzle is seeded as its solution only, and
both clue strips are derived from that solution at request time by one function,
`runsOf`, applied to the rows and then to the output of `transpose`. A grid read
twice by the same rule is the point of the project: write `runsOf` correctly and
it grades both axes, write it carelessly and half the board lies. Because the
clues are computed from the answer, a seed cannot disagree with itself and a
student cannot fudge a clue to match a bug.

Three things this project teaches that the other house projects do not: a cell
that participates in two overlapping constraints at once, transposition met as a
way to reuse code rather than as a puzzle, and a three-valued cell state that a
boolean cannot hold.

## Out of scope

- Solving, hinting, auto-filling forced cells, or marking which cells are wrong.
  The student solves the board by hand and the app only grades lines.
- Creating, editing, importing or deleting puzzles. The three seeded solutions
  are the whole catalogue, and no board is larger than 8 by 8.
- Colour nonograms. A cell is filled or it is not; `crossed` is the student's own
  note that a cell is blank, and it grades exactly like `empty`.
- Timers, scores, difficulty, undo history, and saving progress. A reload starts
  the board empty again, and nothing is persisted between page loads.
- Accounts, login, and a second player.
- A puzzle index page. There is no screen that lists the three puzzles; a puzzle
  is reached by typing its id into the URL. `app/page.tsx` is a two-line server
  component that redirects `/` to `/puzzles/boat` so the preview link opens on a
  board. It is not a declared screen, no criterion grades it, and its worst case
  is a preview link that opens on a 404 - which the person at Gate 3 sees.
- A failed-fetch branch on the screen. `sc-puzzle` declares three states -
  `loading`, `loaded` and `not-found`. If `GET /api/puzzles` never answers, the
  screen stays on `loading` forever, and nothing grades that.
- Any check on mount. The board grades nothing until the first click, so on load
  every clue reads `data-status="open"`, including the `blanks` row-0 clue `0`
  that an empty board already satisfies. This is deliberate: a check on mount
  would make `sc-puzzle` depend in session 1 on an endpoint built in session 2,
  and would leave session 1's skeleton throwing.

## Data model

The Next.js project root is the pipeline's `app/` directory. Inside it sit
`app/` (the App Router tree) and `lib/` (the two library modules). Every path in
this spec is written relative to that project root, so the cuts in
`lib/nonogram.ts` are the file `app/lib/nonogram.ts` as seen from the
repository. There is no `data/` directory and no runtime store: nothing in this
project writes a file, so `app/.gitignore` needs no store entry and the suite has
no world to reset. Every test may run in any order, any number of times, and get
the same answer.

The types:

```
Cell        = "empty" | "filled" | "crossed"
LineStatus  = "satisfied" | "open" | "violated"
Puzzle      = { id: string; title: string; size: number
                rowClues: number[][]; colClues: number[][] }
CheckResult = { rows: LineStatus[]; cols: LineStatus[]; solved: boolean }
```

`Puzzle` is what the API hands out and it carries no solution. Every non-200
response body is `{ "error": string }` - exactly one key, whose value is a
non-empty message.

**The seed.** `lib/puzzles.ts` holds the three solutions and nothing else. A
solution is written as one string per row, `#` for a filled cell and `.` for a
blank one, which keeps an 8 by 8 board readable:

```
boat    5x5      blanks  5x5      house   8x8
..#..            .....            ...##...
.###.            #####            ..####..
#####            #...#            .######.
.#.#.            .###.            ########
.#.#.            #.#.#            .#....#.
                                  .#.##.#.
                                  .#.##.#.
                                  .#....#.
```

The seeded titles are `Boat`, `Blanks` and `House`, and the ids are `boat`,
`blanks` and `house`, listed in that order. `size` is the length of a row, and
every board is square. `blanks` exists to carry the two cases that break a naive
`runsOf`: row 0 is completely empty and row 1 is completely full, and rows 2 and
4 end their last run at the last cell.

**Derived, never stored.** No clue appears anywhere in `lib/puzzles.ts`. The
clues below are the derivation evaluated against the seed above, printed here so
the criteria can pin literals, and they are not a second definition:

| puzzle   | rowClues                                              | colClues                                              |
|----------|-------------------------------------------------------|-------------------------------------------------------|
| `boat`   | `[[1],[3],[5],[1,1],[1,1]]`                            | `[[1],[4],[3],[4],[1]]`                                |
| `blanks` | `[[0],[5],[1,1],[3],[1,1,1]]`                          | `[[2,1],[1,1],[1,2],[1,1],[2,1]]`                      |
| `house`  | `[[2],[4],[6],[8],[1,1],[1,2,1],[1,2,1],[1,1]]`        | `[[1],[6],[3],[4,2],[4,2],[3],[6],[1]]`                |

`boat` and `house` both have rowClues that differ from their colClues, so a
`transpose` that hands back the rows unchanged is red on `c-1-2`. `blanks` has
`[1,2]` in one column and `[2,1]` in another, so a `transpose` that reverses a
column is red too.

**Library modules.** Every exported function is spelled out with its parameters,
because the cut hints call them by name:

- `lib/puzzles.ts` - `solutionRows(id: string): string[] | null` gives the seeded
  strings for an id, `rowCells(row: string): Cell[]` maps `#` to `"filled"` and
  every other character to `"empty"`, `puzzleFor(id: string): Puzzle | null`
  derives one `Puzzle` from a solution, and `allPuzzles(): Puzzle[]` derives all
  three in seed order. `puzzleFor` computes
  `rowClues = rows.map(r => runsOf(rowCells(r)))` and
  `colClues = transpose(rows.map(rowCells)).map(runsOf)` - one function, two
  axes, which is the whole design.
- `lib/nonogram.ts` - `runsOf(cells: Cell[]): number[]`,
  `transpose<T>(grid: T[][]): T[][]`,
  `lineStatus(cells: Cell[], clue: number[]): LineStatus`, and
  `boardSolved(grid: Cell[][], rowClues: number[][], colClues: number[][]): boolean`.

**The status rule, closed.** This is the whole rule and there is no other clause.
Read `runsOf(cells)` as the blocks of consecutive `filled` cells, in order, and
read the one-entry list `[0]` - whether it comes from `runsOf` or from a clue -
as no blocks and a largest block of 0. Then, in this order:

1. `satisfied` when `runsOf(cells)` holds the same numbers in the same order as
   `clue`.
2. Otherwise `violated` when any of exactly these three conditions holds:
   - `cells` has more blocks than `clue` has numbers;
   - one block in `cells` is longer than the largest number in `clue`;
   - no cell in `cells` is still `empty` and `runsOf(cells)` differs from `clue`.
3. `open` in every other case.

The three clauses cannot overlap with step 1: a satisfied line has exactly as
many blocks as the clue has numbers and no block longer than the clue's largest.
The rule is deliberately local and permissive. It never looks at the solution, so
a line can read `open` while being flatly inconsistent with the only picture that
fits - `boat` row 1, clue `[3]`, with a single filled cell at column 0 is `open`,
and `c-2-2` pins that case. What it will not do is call a line `open` once the
line has too many pieces or a piece too long: `boat` row 0, clue `[1]`, filled at
columns 0 and 2, has two blocks against one number and is `violated`, which
`c-2-2` also pins. A `[0]` clue has a largest of 0, so any filled cell in that
line is `violated` at once.

`boardSolved` is computed from the grid on its own and not from the two status
lists, so it is graded on its own; the two agree by construction because they
apply the same rule to the same lines.

**Skeleton fallbacks.** Each cut sits below a fallback declared in the same
function, the function's only `return` stays outside the markers, and every
fallback fails the criteria that name the cut. All five are fixed here, so the
Builder picks none of them:

| cut                | the fallback above the marker                                  |
|--------------------|----------------------------------------------------------------|
| `cut-runs-of`      | `runs` starts as an empty array                                  |
| `cut-transpose`    | `out` starts as an empty array                                   |
| `cut-line-status`  | `status` starts as `"open"`                                      |
| `cut-board-solved` | `solved` starts as `false`                                       |
| `cut-cell-cycle`   | `updated` starts as `grid`, so a click changes nothing            |

`runs` starting empty is load-bearing. A fallback of `[0]` also compiles, and it
would hand the student the empty-line case that `c-1-3` exists to grade.
`status` starting at `"open"` is the third of the three answers on purpose: a
fallback of `"satisfied"` would make `c-2-1` green with `lineStatus` still empty.

**What nothing checks.** Two constraints here are not behaviour a test can read:

- *The clues must be derived rather than typed into the seed.* This one does have
  an owner, and it is the skeleton check at step 8. `cut-runs-of` and
  `cut-transpose` live on the derivation path, so a Builder who stored a clue
  table would leave `c-1-1` through `c-1-4` green in a skeleton with those cuts
  open, and step 8 fails on exactly that.
- *`crossed` must grade identically to `empty`.* Every criterion that pins a
  `violated` or `open` line uses `empty` cells, so a `runsOf` that treats
  `crossed` as filled is caught by `c-2-2`, but no criterion posts a grid
  containing a `crossed` cell. The Verifier is free to add one; the spec does not
  require it, and the gap is a wrong status on a board a student crossed out.
  Owner: `nothing`. It is small, it is stated in the `cut-runs-of` hint, and it is
  the one thing on this page a reader at Gate 1 is being asked to accept.

## Endpoints

| id                 | method | path                        | request            | response                        | status        |
|--------------------|--------|-----------------------------|--------------------|---------------------------------|---------------|
| `ep-puzzles-list`  | GET    | `/api/puzzles`              | none               | `Puzzle[]`                      | 200           |
| `ep-puzzle-check`  | POST   | `/api/puzzles/[id]/check`   | `{ grid: Cell[][] }` | `CheckResult` or `{ error }`  | 200, 400, 404 |

`ep-puzzles-list` answers with all three puzzles in seed order - `boat`,
`blanks`, `house` - each with `id`, `title`, `size`, `rowClues` and `colClues`
and no other key. The solution is not in the response, which is what stops the
board grading itself in the browser.

`ep-puzzle-check` resolves the puzzle id first, so an unknown id answers 404
whatever the body holds. With a known id, the body is validated next, and
exactly these make it a 400: the body is not JSON, the body has no `grid` key,
`grid` is not an array of exactly `size` arrays, an inner array is not exactly
`size` long, or an entry is not one of the three strings `empty`, `filled`,
`crossed`. Anything that passes both is a 200 whose `rows` holds one
`LineStatus` per row in row order, whose `cols` holds one per column in column
order, and whose `solved` is `boardSolved` over the same grid. The clues it
grades against are re-derived from the seeded solution on every request; the
request never carries a clue.

## Screens

One screen. Class names are hashed by CSS Modules, so every element a test reads
carries a `data-testid` and the tests read those, never a class. The clue
colouring keys off `data-status`, so green and `satisfied` are the same fact.

**`sc-puzzle`, route `/puzzles/[id]`** - one board. States: loading, loaded,
not-found.

- `data-testid="board-loading"`, text `Loading`, drawn until the
  `GET /api/puzzles` response arrives and never after it
- `data-testid="puzzle-missing"`, text `Puzzle not found`, drawn in place of the
  title, the grid and both clue strips when no puzzle in the response has the
  route id
- `data-testid="puzzle-title"`, carrying the puzzle title
- `size` x `size` button elements with `data-testid="cell-<r>-<c>"`, `r` and `c`
  counted from 0 with row 0 at the top and column 0 at the left, each carrying
  `data-state` set to the string `empty`, `filled` or `crossed`
- `size` elements with `data-testid="row-clue-<r>"` down the left and `size` with
  `data-testid="col-clue-<c>"` across the top. The text of each is that clue's
  numbers joined by one space, so `[1,2,1]` reads `1 2 1` and `[0]` reads `0`.
  Each carries `data-status` set to `satisfied`, `open` or `violated` - the value
  from the last check response, and `open` on every strip before the first click.
- `data-testid="solved-banner"`, text `Solved`, drawn only while the last check
  response carried `solved` true
- the page is a server component that reads the route `id` and hands it to
  `app/puzzles/[id]/Board.tsx`, a client component. `Board` issues one
  `GET /api/puzzles` when it mounts and does not issue a second one. A cell click
  sends one `POST /api/puzzles/<id>/check` carrying the grid that click produced,
  and no other event sends one.

## Sessions

Session 1 carries the project setup - the Next.js app, the types, the seed, the
list endpoint and the whole screen - so it carries two cut points where session 2
carries three.

**Cut dependencies and the one skeleton.** A criterion's `cuts` list is its full
dependency set: it names every cut that makes the criterion fail while that cut
alone is left empty. Two of the session-2 criteria therefore name session-1 cuts,
because the check route re-derives its clues through `runsOf` and `transpose`.
Where a criterion does not name a cut, leaving that cut empty genuinely does not
change the answer - `c-2-2` and `c-2-3` expect `solved: false`, which is also the
`cut-board-solved` fallback, so neither of them grades it and neither pretends to.
Step 8 cuts one skeleton, not two: all five cuts are open in it at once, and the
session grouping in `.cut-manifest.json` groups the hints, not the artifacts.

Each cut is graded by a set of criteria no other cut shares, and each is red on
its own: `cut-runs-of` alone fails `c-1-1`, `cut-transpose` alone fails `c-1-2`,
`cut-line-status` alone fails `c-2-2`, `cut-board-solved` alone fails `c-2-1`,
and `cut-cell-cycle` alone fails `c-2-5`.

### Session 1 - Setup, the boards, and the clues

**Goal.** Serve three seeded puzzles whose row and column clues are derived from
their solutions, and draw one of them as an empty playable grid with a clue strip
down the top and down the left.

**Teaches.** Run-length encoding a line of cells; transposing a grid so row logic
grades columns; deriving fixtures from the answer instead of storing them;
pinning every rendered element to a `data-testid` a test can read.

**Builds.** `ep-puzzles-list`, `sc-puzzle`.

**Runs at the end.** Three boards on screen, each showing correct clues on both
strips, derived rather than stored, with every cell empty and clickable-looking
but inert.

Acceptance criteria:

- **c-1-1** - `GET /api/puzzles` returns 200 with a JSON array of 3 puzzles whose
  ids in order are `boat`, `blanks` and `house`; the `boat` entry has `size` 5,
  `title` `Boat` and `rowClues` `[[1],[3],[5],[1,1],[1,1]]`, and no entry carries
  a `solution` key. Cuts: `cut-runs-of`.
- **c-1-2** - `GET /api/puzzles` returns the `boat` entry with `colClues`
  `[[1],[4],[3],[4],[1]]` and the `house` entry with `size` 8 and `colClues`
  `[[1],[6],[3],[4,2],[4,2],[3],[6],[1]]`. Cuts: `cut-runs-of`, `cut-transpose`.
  This is the criterion `cut-transpose` lives or dies by: both boards have
  colClues that differ from their rowClues.
- **c-1-3** - `GET /api/puzzles` returns the `blanks` entry with `rowClues`
  `[[0],[5],[1,1],[3],[1,1,1]]`, so the empty row reads `[0]`, the full row reads
  `[5]`, and the run that ends at the last cell of row 4 is counted. Cuts:
  `cut-runs-of`. Together with c-1-1 this is the second fixture for `runsOf`, and
  it is the edge case: a 5-element literal that passes c-1-1 cannot pass this.
- **c-1-4** - `/puzzles/blanks` renders 25 elements with `data-testid` `cell-0-0`
  through `cell-4-4` each carrying `data-state` `empty`, renders `row-clue-0` with
  text `0`, `row-clue-1` with text `5` and `col-clue-2` with text `1 2`, gives
  each of `row-clue-0` through `row-clue-4` `data-status` `open`, and renders no
  `solved-banner` element. Cuts: `cut-runs-of`, `cut-transpose`.
- **c-1-5** - `/puzzles/nope` renders an element with `data-testid`
  `puzzle-missing` and text `Puzzle not found`, and renders no element with
  `data-testid` `cell-0-0` and no element with `data-testid` `puzzle-title`. No
  cuts: the not-found branch is the Builder's, and it is here so the `not-found`
  state the screen declares is graded.

Cut points:

- **cut-runs-of** - `lib/nonogram.ts`. Fill `runs` with the length of each block
  of consecutive `filled` cells in `cells`, in the order the blocks appear,
  counting a block that ends at the last cell. A `crossed` cell and an `empty`
  cell both break a block. When `cells` holds no `filled` cell at all, `runs`
  must be the one-entry list `[0]`, which is the clue an empty line carries.
- **cut-transpose** - `lib/nonogram.ts`. Set `out` so that `out[c][r]` holds
  `grid[r][c]`: one entry per column of `grid`, each as long as `grid` has rows.
  Every row of `grid` has the same length, and `grid` itself is left unchanged.

### Session 2 - Filling, checking, and solved

**Goal.** Cycle a cell through three states on click, grade every row and every
column against its clue with one rule, and declare the board solved when all of
them are satisfied.

**Teaches.** A three-valued cell state that a boolean cannot hold; a total status
rule with a closed list of violations; grading two overlapping axes with one pure
function; posting the whole grid and rendering the per-line answer.

**Builds.** `ep-puzzle-check`.

**Runs at the end.** Fill a board by clicking, watch each clue turn green as its
line comes right, and get the `Solved` banner on the last cell.

Acceptance criteria:

- **c-2-1** - `POST /api/puzzles/boat/check` with the `boat` solution as the grid
  returns 200 with `solved` true, 5 entries in `rows`, 5 entries in `cols`, and
  each of those 10 entries equal to `satisfied`. Cuts: `cut-transpose`,
  `cut-line-status`, `cut-board-solved`. This is the only criterion that pins
  `solved` true, so it is the one that grades `cut-board-solved`.
- **c-2-2** - `POST /api/puzzles/blanks/check` with every cell empty returns 200
  with `rows[0]` `satisfied`, `rows[1]` `open` and `solved` false, and
  `POST /api/puzzles/boat/check` with row 0 set to filled, empty, filled, empty,
  empty and every other cell empty returns 200 with `rows[0]` `violated` and
  `rows[1]` `open`. Cuts: `cut-runs-of`, `cut-line-status`. All three answers in
  one criterion: a `[0]` clue satisfied by an empty line, a line that is
  wrong-but-still-open, and a line that is genuinely violated.
- **c-2-3** - `POST /api/puzzles/house/check` with every cell of row 3 filled and
  every other cell empty returns 200 with 8 entries in `rows`, 8 entries in
  `cols`, `rows[3]` `satisfied`, `rows[0]` `open`, `cols[0]` `satisfied` and
  `cols[3]` `open`. Cuts: `cut-runs-of`, `cut-transpose`, `cut-line-status`. The
  8 by 8 board and the column axis of the check, in one request.
- **c-2-4** - `POST /api/puzzles/nope/check` with a 5 by 5 grid of empty cells
  returns 404, `POST /api/puzzles/house/check` with a grid of 7 rows returns 400,
  and `POST /api/puzzles/boat/check` with the cell at row 0 column 0 set to the
  string `maybe` returns 400, each with a JSON body whose only key is `error`. No
  cuts: the id lookup and the body validation are the Builder's.
- **c-2-5** - On `/puzzles/boat` a first click on `cell-0-2` updates its
  `data-state` to `filled`, a second click updates it to `crossed` and a third
  click updates it to `empty`, while `cell-0-0` stays at `data-state` `empty`
  across all three clicks. Cuts: `cut-cell-cycle`.
- **c-2-6** - On `/puzzles/blanks`, one click on each of the 13 cells filled in
  the `blanks` solution renders a `solved-banner` element with text `Solved` and
  gives each of `row-clue-0` through `row-clue-4` and `col-clue-0` through
  `col-clue-4` `data-status` `satisfied`. Cuts: `cut-cell-cycle`,
  `cut-transpose`, `cut-line-status`, `cut-board-solved`. The 13 cells are the
  five of row 1, columns 0 and 4 of row 2, columns 1, 2 and 3 of row 3, and
  columns 0, 2 and 4 of row 4; row 0 is left untouched.

Cut points:

- **cut-line-status** - `lib/nonogram.ts`. Set `status` to `satisfied` when
  `runsOf(cells)` holds the same numbers in the same order as `clue`. Otherwise
  set it to `violated` when any one of these three holds: `cells` has more blocks
  of consecutive `filled` cells than `clue` has numbers, or one of those blocks is
  longer than the largest number in `clue`, or no cell in `cells` is still `empty`
  while `runsOf(cells)` and `clue` differ. A `[0]` clue counts as no numbers and a
  largest of 0. In every other case leave `status` at `open`.
- **cut-board-solved** - `lib/nonogram.ts`. Set `solved` to true only when
  `lineStatus` answers `satisfied` for every row of `grid` against the matching
  entry of `rowClues` and for every column of `grid` against the matching entry of
  `colClues`. Reach the columns through `transpose`, and leave `solved` false when
  even one of those lines is not satisfied.
- **cut-cell-cycle** - `app/puzzles/[id]/Board.tsx`. Set `updated` to a fresh copy
  of `grid` in which only the cell at row `r` and column `c` moves one step along
  `empty` then `filled` then `crossed` then back to `empty`. Every other cell
  keeps the state it had, and `grid` itself is not mutated.
