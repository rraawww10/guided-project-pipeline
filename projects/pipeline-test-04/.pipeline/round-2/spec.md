# Tenpin - spec

Ten-pin bowling scorecard. Four seeded games, given as flat roll lists, are split
into frames and rendered as frame grids in session 1; session 2 adds the running
total, where a strike or a spare reaches forward into the rolls that come after it
and a frame whose bonus rolls have not been rolled has no score at all.

Stack: Next.js (App Router), React, TypeScript. Two sessions of 40 minutes.
Track: fullstack. Source material: none - this is house format, no reading is cited.

## Outcome

A student who finishes both sessions has:

- `lib/frames.ts` - `frames(rolls: number[]): number[][]`, splitting a flat roll
  list into frames: two rolls per frame, one when the first is a 10, and a tenth
  frame holding whatever is left. A game whose rolls stop early yields fewer than
  ten frames.
- `lib/score.ts` - `scoreGame(rolls: number[]): (number | null)[]`, a cumulative
  total per frame; `pendingFrame(...)`, the test for "the rolls this frame needs
  do not exist yet"; and `gameTotal(...)`, the score of the last frame that has
  one.
- `GET /api/games` returning the four seeded games with their frames.
- `POST /api/games/score` returning the per-frame cumulative array and the game
  total for any roll list in the request body.
- `/games/[id]` rendering the frame grid, the roll symbols, the cumulative score
  per frame and the game total.

The thing this project teaches, and no shipped project in the track does: an
item's value depends on items that come **later**, and "not computable yet" is a
value distinct from zero. TypeScript makes the student spell that out as
`number | null`.

## Out of scope

- Entering rolls by clicking pins. Rolls arrive from the seed or from the POST body.
- Validating impossible games - twelve pins in one frame, a negative roll, more
  than 21 rolls. The seed is legal and the POST body is trusted once it is an
  array of numbers. The one input check that exists is the 400 in c-2-5.
- More than one player, handicaps, leagues, no-tap or other variants.
- Saving a scored game back to the store. Scoring is a pure read; nothing in this
  project writes a file, so no test has to reset one and `data/games.json` ships
  as a tracked seed.
- Any client-side interaction. `/games/[id]` is a server component; there is no
  `useState` in this project and no session teaches one.

### Constraints nothing checks

There is no date arithmetic and no reading of the clock anywhere in this project,
so `spec.json` declares no `code_checks` entry. Every constraint this spec states
is behaviour a criterion pins, with one exception, stated plainly for the person
at Gate 1: **the frame-box and score-cell markup ships written in both sessions**,
so no criterion asks a student to type it. That is deliberate (see Session load
below) and the only thing lost is that a student never writes the grid markup.

## Data model

`lib/types.ts`, all shipped written:

```
Game       = { id: string, name: string, rolls: number[] }
Frame      = number[]           // 1, 2 or 3 rolls
FrameScore = number | null      // null = the bonus rolls do not exist yet
```

`data/games.json` holds exactly these four games, shipped written. The arrays
below are the whole seed; every criterion's expected values are derived from them.

| id | name | rolls |
|---|---|---|
| `g-gutter` | All Gutters | twenty `0` rolls |
| `g-perfect` | Perfect Game | twelve `10` rolls |
| `g-mixed` | Spare Heavy | `1,4,4,5,6,4,5,5,10,0,1,7,3,6,4,10,2,8,6` (19 rolls) |
| `g-partial` | Stopped at Six | `3,4,7,2,9,0,8,1,10,10` (10 rolls) |

Derived values, worked out here so the Test Writer and the Builder agree:

| game | frames | cumulative scores | total |
|---|---|---|---|
| `g-gutter` | ten frames of `[0,0]` | `[0,0,0,0,0,0,0,0,0,0]` | `0` |
| `g-perfect` | nine `[10]` then `[10,10,10]` | `[30,60,90,120,150,180,210,240,270,300]` | `300` |
| `g-mixed` | `[[1,4],[4,5],[6,4],[5,5],[10],[0,1],[7,3],[6,4],[10],[2,8,6]]` | `[5,14,29,49,60,61,77,97,117,133]` | `133` |
| `g-partial` | `[[3,4],[7,2],[9,0],[8,1],[10],[10]]` | `[7,16,25,34,null,null]` | `34` |

Why `g-mixed` is load-bearing: `g-perfect` alone is satisfied by `30 * frame` and
`g-gutter` alone is satisfied by `0`, so criteria pin the **whole cumulative
array** for `g-perfect`, `g-mixed` and `g-partial`, not just a final total. Two
errors that cancel cannot go green against the mixed array.

Why `g-partial` has exactly two blank frames: its last two frames are both
strikes, so frame 5 wants rolls 10 and 11 and frame 6 wants rolls 11 and 12, and
the list has only 10 rolls. Frames 1 to 4 are scored, frames 5 and 6 are `null`,
and there are six frames rather than five - a naive pair-chunking scan produces
five, which is what makes this the scan's edge-case fixture.

The scoring rules, stated once:

- A frame whose first roll is 10 is worth `10` plus the next **two** rolls in the
  roll list.
- A frame whose two rolls add to 10 is worth `10` plus the next **one** roll.
- Any other frame is worth its own two rolls.
- The tenth frame needs no special rule, because the bonus rolls a strike or a
  spare there reaches for are the tenth frame's own extra rolls. Indexing into
  the roll list rather than the frame list is what makes that true, and it is the
  reframing session 2 exists to teach.

Roll symbols, shipped written in `lib/symbols.ts`: a roll of 10 is `X`; the second
roll of a frame whose first two rolls add to 10 is `/`; a roll of 0 is `-`;
anything else is its digit. A frame box holds its symbols joined by one space, so
`[2,8,6]` reads `2 / 6` and `[0,0]` reads `- -`.

## Endpoints

**`ep-games-list` - `GET /api/games` -> 200**

No request body. Returns a JSON array of four objects, one per seeded game, each
`{ id, name, rolls, frames }`, in the seed's order: `g-gutter`, `g-perfect`,
`g-mixed`, `g-partial`. `frames` is `frames(rolls)`. Built in session 1.

**`ep-games-score` - `POST /api/games/score` -> 200, 400**

Request body `{ "rolls": number[] }`.

- `rolls` is an array of numbers: 200 with
  `{ "frames": FrameScore[], "total": number }`, where `frames` is
  `scoreGame(rolls)` and `total` is `gameTotal(scoreGame(rolls))`.
- `rolls` is absent, or is not an array of numbers: 400 with
  `{ "error": "rolls must be an array of numbers" }`.
- `rolls` is `[]`: 200 with `{ "frames": [], "total": 0 }`. An empty game is a
  legal input, not an error.

Built in session 2. The handler does not read the store; it scores whatever it is
given, which is why session 2 can be graded without a second seed.

## Screens

**`sc-game` - `/games/[id]`**, a server component, built in session 1.

It reads the seed through `lib/store.ts` directly rather than fetching
`/api/games`, so session 1's page does not depend on its own HTTP route.

Elements, every one with a `data-testid` because class names are hashed and a test
must have a stable hook:

| element | `data-testid` | holds |
|---|---|---|
| frame box | `frame-1` .. `frame-10` | that frame's roll symbols, joined by one space |
| score cell | `total-1` .. `total-10` | the cumulative score as a decimal string, or nothing when that frame's score is `null` |
| game total | `game-total` | `gameTotal` as a decimal string |
| not-found message | `no-game` | `No game with id <id>` |

One frame box and one score cell are rendered per entry `frames()` returned, so
`g-partial` renders six of each and no element with `data-testid` `frame-7`.

States:

- **frames without scores** - session 1's end state: boxes and symbols, no score
  cells and no total.
- **fully scored** - every frame has a number; `g-gutter`, `g-perfect` and
  `g-mixed`.
- **trailing frames pending** - `g-partial`: `total-5` and `total-6` are empty
  while `game-total` reads `34`.
- **unknown game id** - the route responds 404 and renders the `no-game` text and
  no frame boxes.

## Sessions

### Session 1 - Setup, the games, and the frames

**Goal.** Split each seeded game's flat roll list into frames and render the four
games as frame grids with no scores yet.

**Teaches.** Scanning an array with a step that changes each iteration; a server
component reading a JSON seed through one store module.

**Builds.** `ep-games-list`, `sc-game`. This session also carries the project
setup: the Next.js app, `lib/types.ts`, `data/games.json`, `lib/store.ts`,
`lib/symbols.ts` and the page markup - which is why it holds two cut points
against session 2's three.

**Runs at the end.** All four games render as correctly divided frame grids with
their roll symbols, and no totals anywhere.

**Acceptance criteria.**

- **c-1-1** - `GET /api/games` returns 200 with a JSON array of 4 games, each
  carrying `id`, `name`, `rolls` and `frames`. No cut: the route and the store
  ship written, so this is green on the skeleton and tells the student the
  scaffolding is intact.
- **c-1-2** - `GET /api/games` returns the `g-mixed` game with `frames` equal to
  `[[1,4],[4,5],[6,4],[5,5],[10],[0,1],[7,3],[6,4],[10],[2,8,6]]`.
  Cuts: `cut-frames-scan`, `cut-frames-tenth`.
- **c-1-3** - `GET /api/games` returns the `g-partial` game with `frames` equal to
  `[[3,4],[7,2],[9,0],[8,1],[10],[10]]`. Cuts: `cut-frames-scan`. This is the
  criterion that grades the scan on its own: `g-partial`'s rolls run out before a
  tenth frame, so `cut-frames-tenth` contributes nothing to it.
- **c-1-4** - `/games/g-perfect` renders 10 elements with `data-testid` `frame-1`
  through `frame-10` and displays the exact text `X X X` in the element with
  `data-testid` `frame-10`. Cuts: `cut-frames-scan`, `cut-frames-tenth`.
- **c-1-5** - `/games/g-mixed` displays the exact text `1 4` in the element with
  `data-testid` `frame-1`, `6 /` in `frame-3`, `X` in `frame-5` and `2 / 6` in
  `frame-10`. Cuts: `cut-frames-scan`, `cut-frames-tenth`.
- **c-1-6** - `/games/no-such-game` responds 404 and displays the exact text
  `No game with id no-such-game`. No cut: shipped written.

**Cut points.**

- **`cut-frames-scan`** in `lib/frames.ts`. Hint: *Walk `rolls` from index 0 and
  append the first nine frames to `frames`, taking two rolls per frame unless the
  first of them is 10, in which case the frame holds that one roll and the index
  advances by one. Stop as soon as `rolls` runs out, so a 10-roll game leaves
  `frames` with 6 entries.*
  The declared fallback above the markers is an empty `frames` array, so the
  skeleton renders no boxes and c-1-2, c-1-3, c-1-4 and c-1-5 all go red.
- **`cut-frames-tenth`** in `lib/frames.ts`. Hint: *Append one last entry to
  `frames` holding every roll still left in `rolls` after those nine frames - two
  rolls for an open tenth frame and three for a tenth that earned bonus rolls -
  and append nothing at all for a game whose rolls ran out earlier.*
  The tenth frame is the one place with three rules in it, and the idea's own risk
  note said to isolate it rather than fold it into the scan. It is its own cut for
  that reason. It stays in session 1 because `frames()` has to be whole for the
  grid to render at all - session 2 does not need a tenth-frame rule, since
  indexing into the roll list handles it.

`frames()` keeps its `return` outside both marker pairs: a typed
`const out: number[][] = []` is declared above `cut-frames-scan` and returned
below `cut-frames-tenth`, so an open skeleton still compiles.

### Session 2 - Scoring and the running total

**Goal.** Score every frame from the rolls that follow it, leave a frame blank
while its bonus rolls do not exist, and answer the running total over HTTP and on
the page.

**Teaches.** Lookahead into the roll list instead of the frame list; `null` as a
value distinct from `0` in a TypeScript union; reading and validating a JSON POST
body in a route handler.

**Builds.** `ep-games-score`. The score cells and the `game-total` element are
added to `sc-game` in this session as shipped markup, not as a cut. The page calls
`scoreGame` and `gameTotal` from `lib/score.ts` directly, the way session 1's page
calls `frames`; it never fetches `/api/games/score`, which exists only for the HTTP
criteria.

**Runs at the end.** `g-perfect` reads 300, `g-gutter` reads 0, `g-mixed` reads
133, and `g-partial` leaves exactly its last two frames blank while still showing
a total of 34.

**Acceptance criteria.**

- **c-2-1** - `POST /api/games/score` returns 200 with `frames` equal to
  `[30,60,90,120,150,180,210,240,270,300]` for the 12 rolls of `g-perfect`.
  Cuts: `cut-score-lookahead`.
- **c-2-2** - `POST /api/games/score` returns `frames` equal to
  `[5,14,29,49,60,61,77,97,117,133]` for the 19 rolls of `g-mixed`.
  Cuts: `cut-score-lookahead`. This is the array that `30 * frame` cannot fake and
  the one to read first when session 2 goes red.
- **c-2-3** - `POST /api/games/score` returns `frames` equal to
  `[7,16,25,34,null,null]` for the 10 rolls of `g-partial`.
  Cuts: `cut-score-lookahead`, `cut-pending-frame`. Note what this criterion does
  *not* prove: an unguarded lookahead past the end of `rolls` produces `NaN`,
  `JSON.stringify(NaN)` is `null`, so this body can match byte for byte with
  `cut-pending-frame` still empty. `c-2-4` and `c-2-6` are the two that catch an
  empty `cut-pending-frame`.
- **c-2-4** - `POST /api/games/score` returns `total` 34 for the 10 rolls of
  `g-partial` and `total` 0 for the 20 rolls of `g-gutter`.
  Cuts: `cut-score-lookahead`, `cut-pending-frame`, `cut-game-total`.
- **c-2-5** - `POST /api/games/score` rejects a body whose `rolls` is not an array
  of numbers with 400 and the JSON body
  `{"error": "rolls must be an array of numbers"}`, and returns 200 with `frames`
  `[]` and `total` 0 for an empty `rolls` array. Cuts: `cut-game-total`. The 400
  half ships written; the empty-array half is what ties this criterion to the cut,
  because `gameTotal([])` is 0 and the declared fallback is -1.
- **c-2-6** - `/games/g-partial` displays the exact text `7`, `16`, `25` and `34`
  in the elements with `data-testid` `total-1` through `total-4`, the exact text
  `34` in the element with `data-testid` `game-total`, and leaves the elements with
  `data-testid` `total-5` and `total-6` empty. Cuts: `cut-score-lookahead`,
  `cut-pending-frame`, `cut-game-total`. This is the only criterion that drives all
  three cuts through the page rather than the endpoint, and the only one that reads
  a score cell with a number in it - the populated column and the empty column are
  graded by the same test, so a page that renders every score cell empty, or
  renders `null`, or renders the frame's own score instead of the cumulative one,
  fails here.

**Cut points.**

- **`cut-score-lookahead`** in `lib/score.ts`. Hint: *Set `frameScore` to what
  this frame is worth: 10 plus the next two entries of `rolls` for a frame that
  opens with a 10, 10 plus the single entry after the pair for a frame whose two
  rolls add to 10, and the frame's own two rolls added together for anything else.
  Index into `rolls` at `i`, never into `frames`.*
  The declared fallback is `let frameScore: number | null = null`, and the
  shipped accumulator adds 0 for a null, so an open skeleton returns all zeros and
  c-2-1 through c-2-4 and c-2-6 go red. This is the heaviest block in the project.
- **`cut-pending-frame`** in `lib/score.ts`. Hint: *Set `pending` to true while the
  rolls this frame needs are still missing from `rolls`: a frame that opens with a
  10 needs the two entries after it, a frame whose two rolls add to 10 needs the
  one entry after them, and an open frame needs nothing beyond its own two rolls.*
  The declared fallback is `let pending = false`, which is wrong for `g-partial`
  and right for the three complete games - so it fails c-2-4 and c-2-6 and leaves
  c-2-1 and c-2-2 alone. It fails c-2-3 only when the lookahead guards the end of
  `rolls`; an unguarded one yields `NaN`, which serialises to `null` and matches
  c-2-3's expected body.
- **`cut-game-total`** in `lib/score.ts`. Hint: *Set `total` to the score of the
  last frame that has one: the final entry of `frameScores` that is not null, and
  0 for a game where not one frame has a score yet.*
  The declared fallback must be `let total = -1`, **not** 0. A fallback of 0 would
  make c-2-5's empty-game case and c-2-4's `g-gutter` case pass on an empty
  skeleton, which is the "fallback that accidentally passes" defect.

Both route handlers and `gameTotal` keep their `return` below the markers, with a
typed value declared above, so every cut is an assignment.

## Grading integrity

Every cut is graded by a criterion set no other cut shares, so none of them can be
left empty with the suite green:

| cut | graded by | fails alone on |
|---|---|---|
| `cut-frames-scan` | c-1-2, c-1-3, c-1-4, c-1-5 | c-1-3 |
| `cut-frames-tenth` | c-1-2, c-1-4, c-1-5 | c-1-2 |
| `cut-score-lookahead` | c-2-1, c-2-2, c-2-3, c-2-4, c-2-6 | c-2-1 |
| `cut-pending-frame` | c-2-3, c-2-4, c-2-6 | c-2-4 |
| `cut-game-total` | c-2-4, c-2-5, c-2-6 | c-2-5 |

The last column is the answer to "which criterion fails if only this cut is left
empty" - checked by hand for every cut, because the skeleton check only sees the
all-open and no-cuts states.

One multi-cut criterion is satisfied by a proper subset of its cuts, and it is
named here rather than left to be discovered: **c-2-3 can pass with
`cut-pending-frame` empty**, because an unguarded lookahead past the end of `rolls`
gives `NaN` and `JSON.stringify(NaN)` is `null`, so `[7,16,25,34,null,null]` comes
back either way. Over HTTP, `NaN` and "not computable yet" are the same three
characters - worth saying out loud in a project whose whole point is that the
second one is a real value. Grading integrity does not depend on c-2-3: c-2-4
compares `total`, where `NaN` is not 34, and c-2-6 reads the page, where `NaN` is
not an empty cell. The other multi-cut criteria hold: c-1-2, c-1-4 and c-1-5 need
both frame cuts, because nine frames is not ten, and c-2-4 and c-2-6 need all
three, because -1 is not 34 and a number is not an empty cell.

Each pure function is graded against at least two fixtures, one of them an edge
case, so no cut can be answered with a hardcoded constant: `frames()` against
`g-mixed`, `g-partial` (rolls run out early) and `g-perfect` (a three-roll tenth);
`scoreGame()` against `g-perfect`, `g-mixed` and `g-partial`; `gameTotal()`
against `g-partial` (34, not the last entry) and the empty game (0).

## Session load

Estimated against the linter's own model, decisions counted from the hints as
written:

| session | cuts | builds | concepts | setup | estimate |
|---|---|---|---|---|---|
| 1 | 2 (7.7 + 6.0) | 2 | 2 | yes | 38.7 min |
| 2 | 3 (7.9 + 6.0 + 6.0) | 1 | 3 | no | 37.4 min |

Both are under the 40 minute cap and the largest cut in session 2 is 40% of its
cut minutes, under the 45% share cap. Session 1 carries the setup and two cuts
against session 2's three.

Read this as a signal, not a measurement. Five consecutive projects have overrun,
the model's worst known error is about 5 minutes, and it under-reads
`cut-score-lookahead`: three mutually exclusive rules live in that block and the
regex sees one stated decision. Session 2 also edits the page markup, which the
model does not price at all - call it 3 minutes. Nothing before the step 13 dry
run measures teaching time.

**Drop candidates, each a block a student would otherwise type live:**

- Session 1: hand out `cut-frames-tenth` pre-written and walk through it instead.
  Recovers about 6 minutes. Cost: the student does not type the tenth frame,
  which is the session's second idea, so pull this only if the scan overruns.
- Session 2: hand out `cut-game-total` pre-written. Recovers about 6 minutes and
  costs the least, because "the last frame that has a score" follows directly from
  `cut-pending-frame` once that one is understood.

Do not relieve session 2 by moving a cut into session 1 - session 1 carries the
setup and must hold strictly fewer cuts.
