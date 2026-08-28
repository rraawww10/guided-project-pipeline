# Sweeper

Three 40-minute sessions. Next.js 15 App Router, React 19, TypeScript, CSS
Modules. Three hand-authored boards live in a TypeScript module. There is no
database, no file store, no API key and no network call out of the app.

## Outcome

Minesweeper on three fixed boards. Screen `/boards/[id]` draws one cell per
square, face-down, with a flag-mode button, a mines-left counter and a status
line. Clicking a face-down cell opens it; clicking a cell whose neighbour count
is zero opens the whole connected region of zeros plus the numbered cells
fringing that region, in one click. Clicking with flag mode on plants or removes
a flag instead and never opens anything. The status line reads `Playing` until
every non-mine cell is open, when it reads `Won`, or until a mine is opened,
when it reads `Lost`. Screen `/boards/[id]/solved` draws the same board entirely
face-up - a mine glyph or a neighbour count in every square - and is the view
session 1 ships.

Nothing is random. The three boards are seed data written by hand, so the same
click always opens the same squares and every test gives the same answer twice.
What is left is the algorithm: the eight-way neighbour count with its edge
cases, and the flood fill with its boundary rule.

Three things this project teaches that the other house projects do not: a grid
treated as a graph rather than as two nested arrays, a pure function whose
result is a *set* that no criterion may pin to a traversal order, and an
adversarial edge case - the corner, the wall, and the region that touches
itself - that is visible on screen the moment it is wrong.

`POST /api/boards/[id]/replay` folds an ordered list of clicks into the final
open set and the final status. It is the server-side surface for the same two
pure functions the browser uses, so the flood fill and the win rule are each
graded directly at the API as well as through the DOM.

## Out of scope

- Random board generation. Randomness would break repeatable tests, so the
  three boards are authored and fixed in `lib/boards.ts`.
- Difficulty selection, timers, best scores, or anything that measures elapsed
  time. Nothing in the app reads the clock.
- Right-click and the context menu. Flagging goes through the `flag-mode`
  button so a test can drive it with a plain left click.
- Saving progress. The app writes nothing to disk. Open cells and flags live in
  React state and are lost on reload; `POST /api/boards/[id]/replay` is the only
  way to reproduce a game, and it stores nothing either.
- Chording, question marks, auto-flagging, and a first-click-is-never-a-mine
  rule.
- Creating, editing or deleting boards. The three seeded boards are the whole
  catalogue.
- A screen that consumes `POST /api/boards/[id]/replay`. It is an API-only
  feature, called by tests and by nothing in the browser, and this spec says so
  rather than inventing a screen for it.
- A home page listing the boards. `GET /api/boards` is the board index and it is
  graded at the API; the app's `/` route is a static page with three links,
  which no criterion reads.
- A loading indicator and a failed-fetch branch on either screen. `sc-solved`
  and `sc-play` each declare two states, `loaded` and `not-found`. Before the
  first response arrives a screen draws no cells, and nothing grades that
  moment.
- The third parameter of the idea's `gameStatus(board, revealed, flagged)`. The
  win rule never consults flags, and a parameter that is never read is a lint
  failure waiting to happen, so the signature here is
  `gameStatus(board, revealed)`. The lesson the third parameter was there to
  teach is kept by `c-3-4`, which flags all three mines on the `corner` board
  with one cell open and still expects `playing`.

## Data model

The Next.js project root is the pipeline's `app/` directory. Inside it sit
`app/` (the App Router tree), `lib/` (the four library modules) and the usual
Next configuration. Every path in this spec is written relative to that project
root, so the cut in `lib/board.ts` is the file `app/lib/board.ts` as seen from
the repository.

A board is a flat array of cells addressed by a single integer index, row-major:
the cell at column `x`, row `y` has index `y * width + x`. Every index in every
request body, every response body and every `data-index` attribute is that
number. The types:

```
Board        = { id: string; name: string; width: number; height: number; mines: number[] }
BoardSummary = { id: string; name: string; width: number; height: number; mineCount: number }
BoardView    = { id: string; name: string; width: number; height: number
                 mines: number[]; counts: number[] }
GameStatus   = "playing" | "won" | "lost"
```

`mines` is sorted ascending and holds no duplicates. `counts` has exactly
`width * height` entries and `counts[i]` is the number of the eight cells
touching `i` that are mines - **including when `i` is itself a mine**, which is
why `counts[63]` on the `field` board is `0` even though index 63 holds a mine.
Every non-200 response body is `{ "error": string }`: exactly one key, whose
value is a non-empty message.

**Nothing is written to disk.** The boards are a `const` in `lib/boards.ts`,
every endpoint is a pure function of that constant plus its request, and both
screens hold their own state in React. There is no store to reset between tests,
no `data/` directory and no runtime state to keep out of `skeleton/`, so
`app/.gitignore` needs no store entries. The suite gives the same answer on its
first run and its hundredth, in any order, and the test process needs only
`BASE_URL`.

### The three boards

`lib/boards.ts` exports `BOARDS: Board[]` in the order `intro`, `field`,
`corner`, and `findBoard(id: string): Board | null`, which searches `BOARDS` by
`id` and gives back `null` on a miss. `findBoard` is written live and handed
over complete; it is not a cut point.

```
{ id: "intro",  name: "Intro",  width: 5, height: 5, mines: [9, 11, 18, 23] }
{ id: "field",  name: "Field",  width: 8, height: 8,
  mines: [15, 17, 20, 42, 44, 46, 47, 49, 56, 63] }
{ id: "corner", name: "Corner", width: 4, height: 4, mines: [11, 14, 15] }
```

Drawn solved, with `*` for a mine and the neighbour count everywhere else:

```
intro (5x5, 4 mines, 21 non-mine cells)      field (8x8, 10 mines, 54 non-mine cells)
  0 0 0 1 1                                    0 0 0 0 0 0 1 1
  1 1 1 1 *                                    1 1 1 1 1 1 1 *
  1 * 2 2 2                                    1 * 1 1 * 1 1 1
  1 1 3 * 2                                    1 1 1 1 1 1 0 0
  0 0 2 * 2                                    0 1 1 2 1 2 2 2
                                               1 2 * 2 * 2 * *
corner (4x4, 3 mines, 13 non-mine cells)       2 * 2 2 1 2 3 3
  0 0 0 0                                      * 2 1 0 0 0 1 *
  0 0 1 1
  0 1 3 *
  0 1 * *
```

The full `counts` arrays, in index order, are decided here so no one derives
them twice:

- `intro`: 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 2, 2, 2, 1, 1, 3, 1, 2, 0, 0, 2, 1, 2
- `corner`: 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 3, 2, 0, 1, 2, 2
- `field`, by row: `0 0 0 0 0 0 1 1` / `1 1 1 1 1 1 1 0` / `1 0 1 1 0 1 1 1` /
  `1 1 1 1 1 1 0 0` / `0 1 1 2 1 2 2 2` / `1 2 1 2 0 2 1 1` / `2 2 2 2 1 2 3 3` /
  `1 2 1 0 0 0 1 0`

Each board earns its place:

| board    | what it is for                                                                                                  |
|----------|-----------------------------------------------------------------------------------------------------------------|
| `intro`  | two disjoint zero regions (indices 0-2 and 20-21), so one click never opens the whole board                       |
| `field`  | the flood fill's headline case - one click on index 0 opens 14 cells, and the wrong boundary rule opens 54        |
| `corner` | mines clustered in one corner, so a single click on index 0 opens all 13 non-mine cells and wins the game outright |

**Why `field` is the board that catches the bug.** A flood fill that expands
*through* numbered cells instead of stopping at them looks nearly right on a
sparse board. On `field`, a click on index 0 opens 14 cells under the correct
rule and 54 under the wrong one - a difference of 40 cells, which `c-2-1` and
`c-2-5` both count. On `intro` the same click on index 20 gives 6 against 21.
On `corner` the two rules agree, which is exactly why `corner` is never used to
grade the boundary.

### Library modules

Every exported function is spelled out here, because the cut hints call them by
name:

- `lib/board.ts` - `neighbourCounts(width: number, height: number, mines: number[]): number[]`,
  the flat `width * height` array described above.
- `lib/boards.ts` - `BOARDS` and `findBoard`, both given.
- `lib/reveal.ts` - `revealFrom(board: Board, index: number): number[]`, the set
  of indices one click on `index` opens. The function computes
  `neighbourCounts(board.width, board.height, board.mines)` into `counts` above
  the cut markers, and below the markers it sorts the result ascending and drops
  duplicates, so **no criterion in this spec pins a traversal order**. The rule:
  a mine, or a cell whose count is above 0, opens only itself; a cell whose count
  is 0 opens itself, every zero-count cell reachable through the eight neighbour
  offsets, and every cell bordering that region, and a cell whose count is above
  0 is added to the set but never expanded out of. A zero-count cell touches no
  mine by definition, so a mine can never enter the set this way.
- `lib/status.ts` - `gameStatus(board: Board, revealed: number[]): GameStatus`.
  `lost` when any index in `revealed` is a mine; otherwise `won` when the number
  of distinct indices in `revealed` equals `board.width * board.height` minus
  `board.mines.length`; otherwise `playing`. `lost` is tested first, so opening
  the last safe cell and a mine in the same list reads `lost`.

### Skeleton fallbacks

Each cut sits below a fallback declared in the same function, so the return of a
typed function is never inside the markers and the skeleton always compiles.
Every fallback fails every criterion that names its cut. All eight are fixed
here, so the Builder picks none of them:

| cut                     | the fallback above the marker                                                       |
|-------------------------|--------------------------------------------------------------------------------------|
| `cut-neighbour-counts`  | `counts` starts as an empty array                                                    |
| `cut-solved-cells`      | `cells` starts as an empty array, so the page draws 0 cell elements                  |
| `cut-reveal-from`       | `opened` starts as an empty array                                                    |
| `cut-play-cells`        | `cells` starts as an empty array, so the board draws 0 cell elements                 |
| `cut-play-click`        | the reveal branch of `onCellClick` is empty below the marker, so a click opens nothing |
| `cut-game-status`       | `status` starts as `lost`                                                            |
| `cut-flag-toggle`       | the flag branch of `onCellClick` is empty below the marker, so a click plants nothing  |
| `cut-play-status`       | `statusText` starts as `Playing` and `minesLeft` starts at `-1`, so the counter reads `Mines left: -1` |

`status` starting as `lost` is load-bearing and is decided here rather than left
to the Builder. `GameStatus` has three values, so any constant fallback is the
right answer to *some* status criterion; `lost` is the value that makes `c-3-2`
(expects `won`), `c-3-4` (expects `playing`) and `c-3-6` (expects `Won` then
`Lost`) all red, and `c-3-3` asks for `lost` on one board and `playing` on
another in the same criterion, so the constant fails it too. A fallback of
`playing` would let `c-3-4` pass with `cut-game-status` still empty.

`minesLeft` starting at `-1` matters for the same reason: the `corner` board has
3 mines, so a fallback of `board.mines.length` would already read
`Mines left: 3` and `c-3-5`'s first assertion would be graded against given
code.

## Endpoints

| id                 | method | path                        | request                                | response                                        | status        |
|--------------------|--------|-----------------------------|----------------------------------------|-------------------------------------------------|---------------|
| `ep-boards-list`   | GET    | `/api/boards`               | none                                   | `BoardSummary[]`                                | 200           |
| `ep-board-get`     | GET    | `/api/boards/[id]`          | none                                   | `BoardView` or `{ error }`                      | 200, 404      |
| `ep-board-replay`  | POST   | `/api/boards/[id]/replay`   | `{ clicks: number[], flags?: number[] }` | `{ revealed, flagged, status }` or `{ error }` | 200, 400, 404 |

`ep-boards-list` answers the three summaries in the seed order `intro`, `field`,
`corner`, with `mineCount` 4, 10 and 3. Its route handler is written live and
handed over complete; it has no cut point, which is why `c-3-1` names none.

`ep-board-get` answers 404 for an id that `findBoard` misses. Its handler calls
`neighbourCounts` and is otherwise given.

`ep-board-replay` resolves the board id first, so an unknown board answers 404
even when the body is malformed. With the board found, the body is validated:
`clicks` must be present and an array, `flags` may be absent and must be an array
when present, and every entry of both must be an integer from 0 to
`width * height - 1`. Anything else is a 400 - an absent `clicks`, a `clicks`
that is a string, an entry that is 25 on a 25-cell board, a negative entry, a
non-integer. On a valid body the handler folds the clicks left to right, starting
from the empty set and taking the union with `revealFrom(board, click)` at each
step, then answers `revealed` (sorted ascending, no duplicates), `flagged` (the
submitted `flags` sorted ascending with duplicates dropped, defaulting to the
empty array) and `status` from `gameStatus(board, revealed)`. An empty `clicks`
array is valid and answers 200 with an empty `revealed`. The handler itself is
given code in session 2; `c-2-3` grades its validation and none of it is a cut
point.

Both pure functions therefore have a direct API grading surface: `c-2-1` and
`c-2-2` read `revealFrom` through `revealed`, and `c-3-2` through `c-3-4` read
`gameStatus` through `status`, without going near the DOM.

## Screens

Both screens are client components. Class names are hashed by CSS Modules, so
every element a test reads carries a `data-testid` and the tests read those,
never a class name. Both screens fetch `GET /api/boards/[id]` once on mount and
make no other request; that endpoint is built in session 1, before either screen
that uses it, so no session ships a skeleton whose fetch has no owner.

**`sc-solved`, route `/boards/[id]/solved`** - the face-up view. States: loaded,
not-found.

- one element with `data-testid="board-grid"`, carrying `data-width` and
  `data-height`
- inside it, one element with `data-testid="cell"` per index, in index order,
  each carrying `data-index` set to that index, `data-count` set to that index's
  entry in `counts`, and `data-mine` set to the string `"true"` or the string
  `"false"`
- a cell's visible text: `*` when it is a mine, empty when it is not a mine and
  its count is 0, and the count as decimal digits otherwise
- `data-testid="board-missing"` with the text `Board not found`, drawn in place
  of the grid when `GET /api/boards/[id]` answers 404, with 0 cells on the page

**`sc-play`, route `/boards/[id]`** - the playable board. States: loaded,
not-found.

- one element with `data-testid="board-grid"`, carrying `data-width` and
  `data-height`
- inside it, one element with `data-testid="cell"` per index, in index order,
  each carrying `data-index`, `data-revealed` set to the string `"true"` or
  `"false"`, and `data-flagged` set the same way, and each calling
  `onCellClick` with its own index when clicked
- a cell's visible text: `F` when it is flagged and not open; empty when it is
  neither flagged nor open; `*` when it is open and a mine; empty when it is open
  and its count is 0; the count as decimal digits otherwise. A flagged cell can
  never be open, because the flag branch never opens anything.
- a button with `data-testid="flag-mode"` whose text is `Flag mode: off` or
  `Flag mode: on`. It starts off, so every click in session 2 opens cells and
  session 2's criteria stay green once session 3 lands.
- `data-testid="mines-left"` with the text `Mines left: ` followed by the number
  of mines minus the number of flags, which may go below 0
- `data-testid="game-status"` with the text `Playing`, `Won` or `Lost`
- `data-testid="board-missing"` with the text `Board not found`, drawn in place
  of the grid when `GET /api/boards/[id]` answers 404, with 0 cells on the page

Open cells and flags are held as two arrays of indices in React state. Both
start empty. Neither screen ever mutates the board it fetched.

## Sessions

Session 1 carries the whole project setup - the Next project, the types, the
three seeded boards, `findBoard`, the first route handler and the first screen -
so it carries two cut points where sessions 2 and 3 carry three. For the same
reason `GET /api/boards`, the one endpoint that needs no new concept, is
deferred to session 3, where it is written alongside the replay traffic that
enumerates the boards. Nothing about it depends on session 3's work, and `c-3-1`
names no cut.

**Cut dependencies and the one skeleton.** A criterion's `cuts` list is its full
dependency set: it names every cut that makes the criterion fail while that cut
alone is left empty, whichever session declared it. So a session-3 criterion
names the session-1 and session-2 cuts its request passes through, and no cut in
any list is redundant. A criterion with an empty `cuts` list depends on no
student work and is expected green on the skeleton from the start: that is
`c-1-3`, `c-1-6`, `c-2-3` and `c-3-1`, all of which grade handed-over code
(a 404, a not-found message, the replay validation, the board index).

Step 8 cuts one skeleton, not three. All eight cuts are open in it at once, and
the session grouping in `.cut-manifest.json` groups the hints, not the artifacts.
A session's guide names only that session's cuts; the later sessions' markers are
visible in the tree from the start, the guide says so, and every criterion
belonging to a later session is expected red until its session.

**Repeatability.** No endpoint and no screen writes anything, so no test needs to
reset the world and no test can leave the next one a different world. Every
number in every criterion below is measured from the seeded boards.

### Session 1 - Boards and the solved view

**Goal.** Seed the three boards, count the mines touching every cell, and draw
board intro, board field and board corner face-up at `/boards/[id]/solved`.

**Teaches.** Addressing a fixed grid as a flat array with `index = y * width + x`;
the eight-offset neighbour scan and its bounds test at the edges and corners;
drawing a grid from a flat array with `data-testid` hooks a test can read.

**Builds.** `ep-board-get`, `sc-solved`.

**Acceptance criteria.**

- `c-1-1` - GET /api/boards/intro returns 200 with width 5, height 5, a mines
  array reading 9, 11, 18, 23 and a counts array of exactly 25 numbers reading
  0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 2, 2, 2, 1, 1, 3, 1, 2, 0, 0, 2, 1, 2 in
  index order. Cuts: `cut-neighbour-counts`.
- `c-1-2` - GET /api/boards/field returns 200 with a counts array of exactly 64
  numbers whose entries at indices 0, 7, 8, 15, 54, 56, 57 and 63 are 0, 1, 1,
  0, 3, 1, 2 and 0. Cuts: `cut-neighbour-counts`.
- `c-1-3` - GET /api/boards/no-such-board returns 404 with a JSON body whose
  error key holds a non-empty string. Cuts: none.
- `c-1-4` - screen /boards/intro/solved renders 25 elements with data-testid
  cell, the cells with data-index 9, 11, 18 and 23 carry data-mine true while
  the other 21 carry data-mine false, and the cells with data-index 0, 3, 12, 17
  and 24 carry data-count 0, 1, 2, 3 and 2.
  Cuts: `cut-neighbour-counts`, `cut-solved-cells`.
- `c-1-5` - screen /boards/corner/solved renders 16 elements with data-testid
  cell, the cell with data-index 10 displays the text 3, the cell with data-index
  15 displays the text *, and the cells with data-index 0, 1 and 4 display empty
  text and carry data-count 0. Cuts: `cut-neighbour-counts`, `cut-solved-cells`.
- `c-1-6` - screen /boards/no-such-board/solved displays an element with
  data-testid board-missing whose text is exactly `Board not found` and renders
  0 elements with data-testid cell. Cuts: none.

**Cut points.**

- `cut-neighbour-counts` in `lib/board.ts` - the eight-way scan. Hint: fill
  `counts` with one number per cell of the board, in index order, where the
  number at index `y * width + x` is how many of that cell's 8 neighbours appear
  in `mines`. A cell that is itself a mine still gets its own neighbour count.
  Skip any neighbour that falls off the edge, so a corner cell weighs 3
  neighbours and an edge cell 5, and `counts` ends up exactly `width * height`
  long.
- `cut-solved-cells` in `app/boards/[id]/solved/page.tsx` - the face-up grid.
  Hint: fill `cells` with one element per index of `board`, in index order, each
  carrying `data-testid` `cell`, `data-index` set to that index, `data-count` set
  to that index's entry in `counts`, and `data-mine` set to the string `true`
  when `board.mines` holds the index and the string `false` when it does not. A
  mine cell shows the text `*`, a non-mine cell whose count is 0 shows empty
  text, and every other cell shows its count.

The two cuts carry different criteria: `cut-neighbour-counts` is named by
`c-1-1`, `c-1-2`, `c-1-4` and `c-1-5` and by eight more in sessions 2 and 3,
`cut-solved-cells` only by `c-1-4` and `c-1-5`, so neither can stand in for the
other and each is red on its own. Neither is a constant that could be pasted in:
the scan is graded against three boards of three shapes - a 5x5 in `c-1-1`, an
8x8 in `c-1-2`, a 4x4 in `c-1-5` - and `c-1-2` reads all four corners of the 8x8
(indices 0, 7, 56 and 63) plus two edge cells, which is where a missing bounds
test wraps a row or reads off the end. Index 63 is itself a mine and its count is
0, which pins the rule that a mine still gets a count and that a count is never
overwritten by the glyph.

### Session 2 - Reveal and flood fill

**Goal.** Write `revealFrom` so one click on a zero opens the whole connected
region of zeros plus the numbered cells fringing it, and make `/boards/[id]`
play face-down.

**Teaches.** A breadth-first walk over a grid with an explicit queue and a
visited set; the boundary rule that a numbered cell is opened but never walked
out of; merging a returned index set into React state without duplicates.

**Builds.** `ep-board-replay`, `sc-play`.

**Acceptance criteria.**

- `c-2-1` - POST /api/boards/field/replay with body `{"clicks": [0]}` returns 200
  with a revealed array of exactly 14 entries reading 0, 1, 2, 3, 4, 5, 6, 8, 9,
  10, 11, 12, 13, 14 in ascending order.
  Cuts: `cut-neighbour-counts`, `cut-reveal-from`.
- `c-2-2` - POST /api/boards/intro/replay returns 200 with a revealed array of
  exactly 6 entries reading 15, 16, 17, 20, 21, 22 for body `{"clicks": [20]}`,
  of exactly 1 entry reading 3 for body `{"clicks": [3]}`, and of exactly 1 entry
  reading 9 for body `{"clicks": [9]}`.
  Cuts: `cut-neighbour-counts`, `cut-reveal-from`.
- `c-2-3` - POST /api/boards/no-such-board/replay with body `{"clicks": [0]}`
  returns 404, POST /api/boards/intro/replay returns 400 for body `{}`, for body
  `{"clicks": "0"}` and for body `{"clicks": [25]}`, and each of those 4
  responses carries a JSON body whose error key holds a non-empty string.
  Cuts: none.
- `c-2-4` - screen /boards/field renders 64 elements with data-testid cell, all
  64 carrying data-revealed false and data-flagged false and displaying empty
  text, and screen /boards/no-such-board displays an element with data-testid
  board-missing whose text is exactly `Board not found` and renders 0 elements
  with data-testid cell. Cuts: `cut-play-cells`.
- `c-2-5` - clicking the cell with data-index 0 on screen /boards/field updates
  data-revealed to true on exactly 14 cells, leaves the cell with data-index 7 at
  data-revealed false, and displays the text 1 in the cell with data-index 6 and
  empty text in the cell with data-index 0. Cuts: `cut-neighbour-counts`,
  `cut-reveal-from`, `cut-play-cells`, `cut-play-click`.
- `c-2-6` - clicking the cell with data-index 3 on screen /boards/intro updates
  data-revealed to true on exactly 1 cell, a following click on the cell with
  data-index 20 updates data-revealed to true on exactly 7 cells, and a second
  click on the cell with data-index 3 leaves data-revealed true on exactly 7
  cells. Cuts: `cut-neighbour-counts`, `cut-reveal-from`, `cut-play-cells`,
  `cut-play-click`.

**Cut points.**

- `cut-reveal-from` in `lib/reveal.ts` - the flood fill. Hint: fill `opened`
  with every index that a single click on `index` opens. A mine cell, or a cell
  whose entry in `counts` is above 0, opens only itself. A cell whose count is 0
  opens itself, every zero-count cell reachable from it through the 8 neighbour
  offsets, and every cell bordering that region - but a cell whose count is above
  0 is added and never walked out of, which is the rule that stops the fill at
  the numbers. Keep a visited set so the walk ends. Traversal order is free: the
  code below the markers sorts `opened` ascending and drops duplicates.
- `cut-play-cells` in `app/boards/[id]/page.tsx` - the face-down grid. Hint:
  fill `cells` with one element per index of `board`, in index order, each
  carrying `data-testid` `cell`, `data-index` set to that index, `data-revealed`
  set to the string `true` when `revealed` holds the index and the string `false`
  when it does not, `data-flagged` set the same way from `flagged`, and an
  `onClick` that calls `onCellClick` with that index. A cell that is not revealed
  shows the text `F` when it is flagged and empty text when it is not. A revealed
  cell shows `*` when `board.mines` holds its index, empty text when its entry in
  `counts` is 0, and its count otherwise.
- `cut-play-click` in `app/boards/[id]/page.tsx` - the reveal branch of the
  click handler. Hint: this block is the reveal branch of `onCellClick`, reached
  when flag mode is off. Set the `revealed` state to a new array holding every
  index already in `revealed` together with every index in
  `revealFrom(board, index)`, with no index appearing twice, so a click on an
  already-open cell changes nothing. Leave the `flagged` state as it was.

The three cuts carry different criteria. `c-2-4` is the only criterion that
grades `cut-play-cells` without the fill or the handler: it counts 64 face-down
cells before any click, so an empty `cut-play-cells` is red there while an empty
`cut-reveal-from` is green. `c-2-1` and `c-2-2` go the other way, reaching
`revealFrom` through the replay endpoint with no DOM at all. `cut-play-click` is
named only where a click has to change the page, and it cannot hide inside
`cut-play-cells`: with the handler empty the 64 cells still render and `c-2-4`
still passes, while `c-2-5` and `c-2-6` stay red.

`c-2-1` is the criterion that pins the boundary rule. On `field` the correct
click on index 0 opens 14 cells and a fill that expands through numbered cells
opens 54, so the two answers differ by 40 and the count alone separates them.
Index 7 is the fringe case in miniature: it touches only numbered cells and a
mine, never a zero, so it stays shut - `c-2-5` checks exactly that on screen.
`c-2-2` adds a second zero region on a second board, a click on a numbered cell
that opens only itself, and a click straight onto a mine, so a fill that always
expands and a fill that never expands are both red. `c-2-6` clicks the same cell
twice and demands the open count stay at 7, which is what separates a union from
an append.

### Session 3 - Flags, status, and replay

**Goal.** Add the flag-mode toggle, the mines-left counter and `gameStatus`, and
expose the board index at `GET /api/boards` so a whole game can be driven through
`POST /api/boards/[id]/replay`.

**Teaches.** Expressing the win rule as revealed count equals cells minus mines;
a mode toggle that changes what one click means; folding an ordered list of
clicks into one final state on the server.

**Builds.** `ep-boards-list`.

**Acceptance criteria.**

- `c-3-1` - GET /api/boards returns 200 with a JSON array of exactly 3 entries
  whose id values are intro, field and corner in that order and whose mineCount
  values are 4, 10 and 3. Cuts: none.
- `c-3-2` - POST /api/boards/corner/replay returns 200 with status won and a
  revealed array of exactly 13 entries reading 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
  12, 13 for body `{"clicks": [0]}`, and returns 200 with status playing and a
  revealed array of exactly 1 entry reading 6 for body `{"clicks": [6]}`.
  Cuts: `cut-neighbour-counts`, `cut-reveal-from`, `cut-game-status`.
- `c-3-3` - POST /api/boards/corner/replay with body `{"clicks": [0, 15]}`
  returns 200 with status lost and a revealed array of exactly 14 entries, and
  POST /api/boards/intro/replay with body `{"clicks": [0, 20]}` returns 200 with
  status playing and a revealed array of exactly 14 entries.
  Cuts: `cut-neighbour-counts`, `cut-reveal-from`, `cut-game-status`.
- `c-3-4` - POST /api/boards/corner/replay with body
  `{"clicks": [6], "flags": [11, 14, 15]}` returns 200 with status playing, a
  revealed array of exactly 1 entry reading 6 and a flagged array reading 11, 14,
  15. Cuts: `cut-neighbour-counts`, `cut-reveal-from`, `cut-game-status`.
- `c-3-5` - on screen /boards/corner, clicking the element with data-testid
  flag-mode and then the cell with data-index 15 updates that cell to
  data-flagged true and data-revealed false and updates the data-testid
  mines-left element to the text `Mines left: 2`, a following click on the cell
  with data-index 14 updates mines-left to the text `Mines left: 1`, and a second
  click on the cell with data-index 15 updates that cell to data-flagged false
  and mines-left to the text `Mines left: 2`.
  Cuts: `cut-play-cells`, `cut-flag-toggle`, `cut-play-status`.
- `c-3-6` - clicking the cell with data-index 0 on screen /boards/corner updates
  data-revealed to true on exactly 13 cells and updates the data-testid
  game-status element to the text `Won`, and clicking the cell with data-index 9
  on screen /boards/intro updates data-revealed to true on exactly 1 cell and
  updates the data-testid game-status element to the text `Lost`.
  Cuts: `cut-neighbour-counts`, `cut-reveal-from`, `cut-play-cells`,
  `cut-play-click`, `cut-game-status`, `cut-play-status`.

**Cut points.**

- `cut-game-status` in `lib/status.ts` - the win and lose rule. Hint: set
  `status` to `lost` when any index in `revealed` is also in `board.mines`.
  Otherwise set `status` to `won` when the number of distinct indices in
  `revealed` equals `board.width * board.height` minus the number of entries in
  `board.mines`, and to `playing` in every other case. Flags are no part of this
  rule: a board with every mine flagged and 1 cell open is still `playing`.
- `cut-flag-toggle` in `app/boards/[id]/page.tsx` - the flag branch of the click
  handler. Hint: this block is the flag branch of `onCellClick`, reached when
  flag mode is on. Set the `flagged` state to a new array holding `flagged` with
  `index` added when it is absent and dropped when it is already present. Leave
  the `revealed` state as it was, so a click in flag mode never opens a cell.
- `cut-play-status` in `app/boards/[id]/page.tsx` - the two readouts. Hint: set
  `minesLeft` to the number of entries in `board.mines` minus the number of
  entries in `flagged`, which is allowed to go below 0. Set `statusText` from
  `gameStatus(board, revealed)` to the string `Playing`, `Won` or `Lost`, mapping
  the three `playing`, `won` and `lost` values one for one.

The three cuts carry different criteria. `c-3-5` is the only criterion that
names `cut-flag-toggle`, and it is the only one that touches flag mode at all, so
nothing else can stand in for it; it drives three clicks - plant, plant, remove -
so a handler that only adds and a handler that only removes are both red, and it
reads the counter at 2, then 1, then 2, so a constant is red as well.
`cut-play-status` is named by `c-3-5` and `c-3-6`, one for the counter and one
for the status line, and `c-3-5` is red with `cut-play-status` empty even though
`cut-game-status` is untouched by it. `cut-game-status` is named by the three
replay criteria and by `c-3-6`, and it is the only session-3 cut with a grading
path that never opens a browser.

None of the four `cut-game-status` criteria can be passed by a constant. `c-3-2`
asks for `won` and `playing` in one criterion, `c-3-3` for `lost` and `playing`
across two boards, `c-3-6` for `Won` and then `Lost` on screen, and `c-3-4` asks
for `playing` on a board whose three mines are all flagged - which is the whole
point of the rule, since a student who writes "won when every mine is flagged"
gets `won` there and is red. `c-3-4` is also the criterion that proves flags are
carried through the replay response without touching the outcome.

`corner` is the win board because 13 of its 16 cells are one connected zero
region: `c-3-2` wins it in a single click and `c-3-3` loses it by adding one
click on the mine at index 15, so both endings are reachable in two moves and
both are replayable from a list. `intro` supplies the counterexample in `c-3-3`,
where two clicks open 14 of 21 non-mine cells and the game is still `playing`.
