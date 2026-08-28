# Sweeper - instructor pack

Minesweeper on three hand-authored boards. Next.js 15 App Router, React 19,
TypeScript, CSS Modules. No database, no API key, no network call out of the
app, and nothing random: the same click always opens the same squares, in class
and in the test suite.

Three sessions of 40 minutes. Seven student tasks (cut points). Eighteen
acceptance criteria, `c-1-1` to `c-3-6`, each one graded by exactly one test.

## Read this first - the timing

| Session | Title | This guide's plan | Fits the 40-minute cap? |
|---|---|---|---|
| 1 | Boards and the solved view | 40 minutes | yes |
| 2 | Reveal and flood fill | 46 minutes | **no - 6 over** |
| 3 | Flags, status, and replay | 40 minutes | yes |

Session 2 does not fit. The spec budgets 20 of its 40 minutes to one cut,
`cut-reveal-from`, and leaves zero slack for the class to write it, run it, and
fix the one wrong answer nearly everyone gets first (54 cells open instead of
14). Session 2's guide opens with the overrun and two trims. Session 3 has
roughly 4 minutes of real slack, because `cut-game-status` is a shorter block
than the spec's 12-minute budget assumed, so the cheapest rebalance is a Gate 1
one: move `cut-play-click` into session 3, or shrink `cut-reveal-from` by
handing over the queue frame.

## What the students build

| Route | What it is | Session |
|---|---|---|
| `/boards/[id]/solved` | the whole board face up - a `*` on every mine, a neighbour count everywhere else | 1 |
| `/boards/[id]` | the playable board, face down, with a flag toggle, a mines-left counter and a status line | 2 and 3 |
| `GET /api/boards` | the board index: id, name, size, mine count | 3 (given code) |
| `GET /api/boards/[id]` | one board plus its full `counts` array, or 404 | 1 |
| `POST /api/boards/[id]/replay` | folds a list of clicks into the final open set and status - API only, no screen uses it | 2 and 3 (given code) |

`/` is a static page with three links. No criterion reads it.

## The three boards

They are a `const`, written by hand, and they are the whole catalogue:

```ts
export const BOARDS: Board[] = [
  { id: 'intro', name: 'Intro', width: 5, height: 5, mines: [9, 11, 18, 23] },
  {
    id: 'field',
    name: 'Field',
    width: 8,
    height: 8,
    mines: [15, 17, 20, 42, 44, 46, 47, 49, 56, 63],
  },
  { id: 'corner', name: 'Corner', width: 4, height: 4, mines: [11, 14, 15] },
]
```

Drawn solved - `*` is a mine, every other square is its neighbour count. Keep
this on screen for all three sessions:

```text
intro (5x5, 4 mines, 21 safe cells)      field (8x8, 10 mines, 54 safe cells)
  0 0 0 1 1                                0 0 0 0 0 0 1 1
  1 1 1 1 *                                1 1 1 1 1 1 1 *
  1 * 2 2 2                                1 * 1 1 * 1 1 1
  1 1 3 * 2                                1 1 1 1 1 1 0 0
  0 0 2 * 2                                0 1 1 2 1 2 2 2
                                           1 2 * 2 * 2 * *
corner (4x4, 3 mines, 13 safe cells)       2 * 2 2 1 2 3 3
  0 0 0 0                                  * 2 1 0 0 0 1 *
  0 0 1 1
  0 1 3 *
  0 1 * *
```

Every cell is addressed by one integer, row-major: the cell at column `x`, row
`y` is index `y * width + x`. Every `data-index`, every entry of `mines`, every
number in a replay request body is that integer. Teach this in the first five
minutes of session 1 and never draw a two-dimensional array on the board.

Why each board is in the set:

- **`intro`** has two separate zero regions (indices 0-2 and 20-21), so one
  click never opens the whole board.
- **`field`** is the flood fill's headline case: one click on index 0 opens 14
  cells under the right rule and 54 under the wrong one.
- **`corner`** clusters its three mines, so one click on index 0 opens all 13
  safe cells and wins the game outright.

## What the student is handed

A complete Next project that builds and runs on the first `npm run dev`. Seven
blocks of it are replaced by a one-line `TODO(<task id>)` comment, and every
one of them sits under a fallback that keeps the file compiling:

| Task | File in the student tree | Line | Session |
|---|---|---|---|
| `cut-neighbour-counts` | `lib/board.ts` | 36 | 1 |
| `cut-solved-cells` | `app/boards/[id]/solved/page.tsx` | 64 | 1 |
| `cut-reveal-from` | `lib/reveal.ts` | 36 | 2 |
| `cut-play-click` | `app/boards/[id]/page.tsx` | 60 | 2 |
| `cut-game-status` | `lib/status.ts` | 21 | 3 |
| `cut-flag-toggle` | `app/boards/[id]/page.tsx` | 58 | 3 |
| `cut-play-status` | `app/boards/[id]/page.tsx` | 88 | 3 |

All seven TODOs are visible from day one. Say so in session 1: the later ones
are not broken, they are not this session's work.

Five criteria are **green before a student writes anything**, because they
grade handed-over code: `c-1-3` (the 404), `c-1-6` (the not-found screen),
`c-2-3` (the replay validation), `c-2-4` (the face-down grid) and `c-3-1` (the
board index). If one of those goes red, a student has edited given code - that
is the first thing to check, not their TODO.

## How to run it

In the student tree:

```bash
npm install
npm run dev
# http://localhost:3000/boards/intro/solved
# http://localhost:3000/boards/field
# http://localhost:3000/api/boards
```

Run `npm install` **before** the session, not in it. It is the single largest
timing risk in session 1 and it buys nothing pedagogically.

The full suite, the way the pipeline runs it (installs, builds, starts the app
on a free port, runs 18 tests, writes `skeleton-results.json`):

```bash
python3 -m pipeline test pipeline-test-01 --target skeleton
```

One criterion, fast, against the dev server the class already has running:

```bash
cd projects/pipeline-test-01
BASE_URL=http://localhost:3000 .pipeline/venv/bin/python -m pytest skeleton/verify -q -k c_1_1
# Windows: .pipeline\venv\Scripts\python.exe -m pytest skeleton\verify -q -k c_1_1
```

The suite never starts a server. It talks to one that is already running, and
it reads `BASE_URL` to find it.

## Rough edges worth knowing before you teach

Taken from `ambiguity.md`, the report written against this spec at Gate 1.

- **The flag-mode button is given code, not a student task.** It flips its own
  label from session 2 onwards, while both branches of `onCellClick` are still
  empty. A student who turns flag mode on in session 2 gets a board where
  nothing at all happens and blames `cut-play-click`. Warn them.
- **"Every cell bordering that region" means the 8 neighbours**, not the 4
  orthogonal ones. On `field` from index 0 the two readings give 14 cells and
  13 - the odd one out is index 14, which is diagonal from the zero at index 5.
  Say "8 neighbours" out loud; `c-2-1` grades it.
- **Every cell count in a criterion is a total on the page after the step**,
  never the number of cells that changed. "Opens 7 cells" after two clicks on
  `intro` means 7 cells are open in total.
- **A mine still gets its own neighbour count.** `field` index 63 is a mine and
  its count is 0; `corner` index 15 is a mine and its count is 2. The glyph
  never overwrites the count in `data-count`.
- **The board is not locked after `Won` or `Lost`.** A click after a terminal
  status opens or flags its cell exactly as before, and `c-3-6` checks that.
  Students who add a lock go red.

## The files in this pack

- `session-1.md` - boards, the neighbour scan, the solved view
- `session-2.md` - the flood fill and the playable board (**overruns by 6**)
- `session-3.md` - flags, the status line, the full game
- `troubleshooting.md` - every error a student in this project actually hits
