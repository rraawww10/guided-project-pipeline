# Tenpin - spec

Ten-pin bowling scorecard. Four seeded games, given as flat roll lists, are split
into frames and rendered as frame grids in session 1; session 2 adds the running
total, where a strike or a spare reaches forward into the rolls that come after it
and a frame whose bonus rolls have not been rolled has no score at all.

Stack: Next.js (App Router), React, TypeScript. Two sessions of 40 minutes.
Track: fullstack. Source material: none - this is house format, no reading is cited.

This is round 4. Rounds 1, 2 and 3 were rejected at Gate 1; the last section of
this file lists every finding from round 3 and what was done with it. Round 3 was
rejected on one finding, and this round changes exactly what that finding asked
for: prose saying where the end-of-`rolls` test lives. `spec.json` is unchanged
from round 3, so every criterion, cut, hint and minute estimate is the one round 3
recorded.

## Outcome

A student who finishes both sessions has:

- `lib/frames.ts` - `frames(rolls: number[]): number[][]`, splitting a flat roll
  list into frames: two rolls per frame, one when the first is a 10, and a tenth
  frame holding whatever is left. A game whose rolls stop early yields fewer than
  ten frames. Inside it, a typed accumulator `out` and a scan index `i` are
  declared above the cut markers; both cut blocks in this file append to `out` and
  advance `i`, and the `return out` sits below both.
- `lib/score.ts` - three exported functions:
  - `scoreGame(rolls: number[]): (number | null)[]`, the cumulative total per
    frame;
  - `pendingFrame(rolls: number[], i: number, frame: number[]): boolean`, the test
    for "the rolls this frame needs do not exist yet", called by `scoreGame` once
    per frame;
  - `gameTotal(frameScores: (number | null)[]): number`, the score of the last
    frame that has one.
- `scoreGame` obtains its frames by calling `frames(rolls)` from `lib/frames.ts`
  and walking the list it returns as `frameList`, carrying a parallel index `i`
  into `rolls`; the frame-splitting scan exists only in `lib/frames.ts`, and
  `lib/score.ts` must not chunk `rolls` itself.
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
  array of numbers. The only input checking that exists is the 400 in c-2-5.
- More than one player, handicaps, leagues, no-tap or other variants.
- Saving a scored game back to the store. Scoring is a pure read; nothing in this
  project writes a file, so no test has to reset one and `data/games.json` ships
  as a tracked seed.
- Any client-side interaction. `/games/[id]` is a server component; there is no
  `useState` in this project and no session teaches one.
- **An HTTP status for an unknown game id.** `/games/[id]` answers 200 for every
  id, including one that is not in the seed, and renders a message element instead
  of a grid. A server component cannot set its own status code, and the only way
  to get 404 *and* the id in the message is a `not-found.tsx` reading the id from
  a client hook, which the line above rules out. c-1-6 therefore asserts the
  message and not a status. This is a decision, not an omission: nothing in this
  project distinguishes "missing" from "present" by status code.

### Constraints nothing checks

There is no date arithmetic and no reading of the clock anywhere in this project,
so `spec.json` declares no `code_checks` entry and `code-check` runs nothing.
Every other constraint this spec states is behaviour some criterion pins, with one
exception, stated plainly for the person at Gate 1: **all page markup ships
written in both sessions** - the frame boxes, the score cells and `game-total` -
so no student types markup in this project and every cut is in `lib/`. That is
deliberate (see Session load), and what is lost is that a student never writes the
grid. It is also why both drop candidates named under Session load are cut points
rather than markup: a trim that costs no live minutes is not a trim.

## Data model

`lib/types.ts`, all shipped written:

```
Game       = { id: string, name: string, rolls: number[] }
Frame      = number[]           // 1, 2 or 3 rolls
FrameScore = number | null      // null = the bonus rolls do not exist yet
```

`data/games.json` holds exactly these four games, shipped written, in this order.
The arrays below are the whole seed; every criterion's expected values are derived
from them.

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
- The cumulative array is `null` from the first frame whose bonus rolls are
  missing onwards. `g-partial` shows this: once frame 5 is `null`, frame 6 is
  `null` too, and `gameTotal` is 34, the last frame that has a score.

There is exactly one frame-splitting scan in this project and it lives in
`lib/frames.ts`. `lib/score.ts` calls `frames(rolls)` and walks the result; it
never chunks `rolls` into frames itself, so the answer to `cut-frames-scan` is not
written down anywhere else in the tree.

Roll symbols, shipped written in `lib/symbols.ts`: a roll of 10 is `X`; the second
roll of a frame whose first two rolls add to 10 is `/`; a roll of 0 is `-`;
anything else is its digit. A frame box holds its symbols joined by one space, so
`[2,8,6]` reads `2 / 6`, `[0,1]` reads `- 1` and `[0,0]` reads `- -`. The tenth
frame of `g-perfect` is `[10,10,10]`, whose first two rolls add to 20 rather than
10, so it reads `X X X`.

## Endpoints

**`ep-games-list` - `GET /api/games` -> 200**

No request body. Returns a JSON array of four objects, one per seeded game, each
`{ id, name, rolls, frames }`, in the seed's order: `g-gutter`, `g-perfect`,
`g-mixed`, `g-partial`. That order is graded by c-1-1. `frames` is
`frames(rolls)`. Built in session 1.

**`ep-games-score` - `POST /api/games/score` -> 200, 400**

Request body `{ "rolls": number[] }`.

- `rolls` is an array of numbers: 200 with
  `{ "frames": FrameScore[], "total": number }`, where `frames` is
  `scoreGame(rolls)` and `total` is `gameTotal(scoreGame(rolls))`.
- `rolls` is absent, or is not an array of numbers: 400 with
  `{ "error": "rolls must be an array of numbers" }`.
- The body is absent, empty, or not valid JSON: treated the same as an absent
  `rolls` - 400 with `{ "error": "rolls must be an array of numbers" }`. The
  handler wraps the body parse, so no input reaches the 500 the endpoint does not
  declare. Graded by c-2-5.
- `rolls` is `[]`: 200 with `{ "frames": [], "total": 0 }`. An empty game is a
  legal input, not an error.

Built in session 2. The handler does not read the store; it scores whatever it is
given, which is why session 2 can be graded without a second seed.

## Screens

**`sc-game` - `/games/[id]`**, a server component, built in session 1.

It reads the seed through `lib/store.ts` directly rather than fetching
`/api/games`, so session 1's page does not depend on its own HTTP route. Session
2's score column is fed the same way: the page calls `scoreGame` and `gameTotal`
from `lib/score.ts` in process and never fetches `/api/games/score`, which exists
only for the HTTP criteria.

Elements, every one with a `data-testid` because class names are hashed and a test
must have a stable hook:

| element | `data-testid` | holds |
|---|---|---|
| frame box | `frame-1` .. `frame-10` | that frame's roll symbols, joined by one space |
| score cell | `total-1` .. `total-10` | the cumulative score as a decimal string, or no text at all when that frame's score is `null` |
| game total | `game-total` | `gameTotal` as a decimal string |
| message | `no-game` | `No game with id <id>` |

One frame box and one score cell are rendered per entry `frames()` returned, so
`g-partial` renders six of each and no element with `data-testid` `frame-7`.

A score cell for a frame whose score is `null` contains **no text**: its
`textContent` is the empty string. It is not a placeholder character, not
`&nbsp;`, not an em dash and not the `-` gutter glyph. c-2-6 reads a populated
cell and an empty cell in the same test, and the Grading integrity section leans
on that twice, so the emptiness is a requirement rather than a styling choice.

States:

- **scores not yet computed** - `lib/score.ts` unfilled: boxes and symbols render,
  every score cell is empty, and `game-total` reads `-1`. This is what session 1
  ends on, and the paragraph below explains why the `-1` is there.
- **fully scored** - every frame has a number; `g-gutter`, `g-perfect` and
  `g-mixed`.
- **trailing frames pending** - `g-partial`: `total-5` and `total-6` hold no text
  while `game-total` reads `34`.
- **unknown game id** - the page answers 200 and renders the `no-game` element
  with the interpolated text and no frame boxes.

`cutter.py` generates one skeleton for the whole project, so the score cells and
`game-total` are in the page markup from the first minute of session 1, wired to
`lib/score.ts` with every cut still open. At that point `scoreGame` returns `null`
for every frame - the declared fallback for `cut-score-lookahead` is `null` - so
every score cell is empty, and `gameTotal` returns its declared fallback of `-1`,
so `game-total` reads `-1`. Session 1 ignores both. The grid, the roll symbols and
the frame count are what session 1 is judged on, and no session-1 criterion reads
a score cell or `game-total`.

## Sessions

### Session 1 - Setup, the games, and the frames

**Goal.** Split each seeded flat roll list into frames and render the four games
as frame grids with no scores yet.

**Teaches.** Scanning an array with a step that changes each iteration; a server
component reading a JSON seed through one store module.

**Builds.** `ep-games-list`, `sc-game`. This session also carries the project
setup: the Next.js app, `lib/types.ts`, `data/games.json`, `lib/store.ts`,
`lib/symbols.ts` and the whole page markup - which is why it holds two cut points
against session 2's three.

**Runs at the end.** All four games render as correctly divided frame grids with
their roll symbols. The score cells are empty and `game-total` reads `-1`, because
`lib/score.ts` is session 2's work.

**Acceptance criteria.**

- **c-1-1** - `GET /api/games` returns 200 with a JSON array of 4 games whose `id`
  values are `g-gutter`, `g-perfect`, `g-mixed` and `g-partial` in that order,
  each carrying `id`, `name`, `rolls` and `frames`. No cut: the route and the
  store ship written, so this is green on the skeleton and tells the student the
  scaffolding is intact. It is also what grades the seed order.
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
  `data-testid` `frame-1`, `6 /` in `frame-3`, `X` in `frame-5`, `- 1` in
  `frame-6` and `2 / 6` in `frame-10`. Cuts: `cut-frames-scan`,
  `cut-frames-tenth`. `frame-6` is `[0,1]`, which is what grades the `-` glyph for
  a gutter roll.
- **c-1-6** - `/games/no-such-game` displays the exact text
  `No game with id no-such-game` in the element with `data-testid` `no-game` and
  renders no element with `data-testid` `frame-1`. No cut: shipped written. There
  is no status assertion here, for the reason given in Out of scope.

**Cut points.**

Both cuts live in `lib/frames.ts`. A typed `const out: number[][] = []` and a
`let i = 0` are declared above `cut-frames-scan`; both cut blocks append to `out`
and advance `i`; `return out` sits below `cut-frames-tenth`, outside both marker
pairs, so an open skeleton still compiles. `out` is the symbol both hints name,
and it is each cut's `writes_into` in `spec.json`.

- **`cut-frames-scan`** in `lib/frames.ts`, writes into `out`. Hint: *Walk `rolls`
  from the start and append the first nine frames to `out`, advancing `i` by two
  rolls per frame unless the first of them is 10, in which case the frame holds
  that one roll and `i` advances by one. Stop as soon as `rolls` runs out, so a
  10-roll game leaves `out` with 6 entries.*
  With this block open, `out` is empty, the page renders no boxes, and c-1-2,
  c-1-3, c-1-4 and c-1-5 all go red.
- **`cut-frames-tenth`** in `lib/frames.ts`, writes into `out`. Hint: *Append one
  last entry to `out` holding every roll still left in `rolls` from `i` onwards -
  two rolls for an open tenth frame and three for a tenth that earned bonus rolls
  - and append nothing at all for a game whose rolls ran out earlier.*
  The tenth frame is the one place with three rules in it, and the idea's own risk
  note said to isolate it rather than fold it into the scan. It is its own cut for
  that reason. It stays in session 1 because `frames()` has to be whole for the
  grid to render at all - session 2 does not need a tenth-frame rule, since
  indexing into the roll list handles it.

### Session 2 - Scoring and the running total

**Goal.** Score every frame from the rolls that follow it, leave a frame blank
while its bonus rolls do not exist, and answer the running total over HTTP and on
the page.

**Teaches.** Lookahead into the roll list instead of the frame list; `null` as a
value distinct from `0` in a TypeScript union; reading and validating a JSON POST
body in a route handler.

**Builds.** `ep-games-score`. `scoreGame` opens by calling `frames(rolls)` and
holds the result in `frameList`; it walks `frameList`, keeps a parallel index `i`
into `rolls`, and advances `i` by the length of each frame. No frame chunking is
written in `lib/score.ts`. The score cells and `game-total` are already in the
page markup from session 1; this session wires them to `lib/score.ts` and types no
markup.

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
  `{"error": "rolls must be an array of numbers"}`, rejects a request whose body
  is not valid JSON with that same 400 body, and returns 200 with `frames` `[]`
  and `total` 0 for an empty `rolls` array. Cuts: `cut-game-total`. Both 400
  halves ship written; the empty-array half is what ties this criterion to the
  cut, because `gameTotal([])` is 0 and the declared fallback is `-1`.
- **c-2-6** - `/games/g-partial` displays the exact text `7`, `16`, `25` and `34`
  in the elements with `data-testid` `total-1` through `total-4`, the exact text
  `34` in the element with `data-testid` `game-total`, and the elements with
  `data-testid` `total-5` and `total-6` contain no text at all. Cuts:
  `cut-score-lookahead`, `cut-pending-frame`, `cut-game-total`. This is the only
  criterion that drives all three cuts through the page rather than the endpoint,
  and the only one that reads a score cell with a number in it - the populated
  column and the empty column are graded by the same test, so a page that renders
  every score cell empty, or renders `null`, or renders `NaN`, or renders the
  frame's own score instead of the cumulative one, fails here.

**Cut points.**

All three live in `lib/score.ts`, and each is an assignment to a value declared
above its markers, with the `return` below.

- **`cut-score-lookahead`**, writes into `frameScore`. It sits in `scoreGame`'s
  loop over `frameList`, under a declared
  `let frameScore: number | null = null`. Hint: *Set `frameScore` to what this
  frame is worth: 10 plus the next two entries of `rolls` for a frame that opens
  with a 10, 10 plus the single entry after the pair for a frame whose two rolls
  add to 10, and the frame's own two rolls added together for anything else. Index
  into `rolls` at `i`, never into `frameList`.*
  **The block applies the three arithmetic rules unconditionally and never tests
  the length of `rolls`.** `pendingFrame` is the only place the end of `rolls` is
  checked, and `scoreGame` pushes `null` for a frame it reports pending. So a
  lookahead that reaches past the last roll produces `NaN` here, not a `null`
  from a guard: this block scores, `pendingFrame` decides whether the score is
  allowed to exist, and neither job moves into the other block.
  With this block open, every frame scores `null`, so the whole cumulative array
  is `null` and c-2-1, c-2-2, c-2-3, c-2-4 and c-2-6 go red. This is the heaviest
  block in the project.
- **`cut-pending-frame`**, writes into `pending`. It is the body of
  `pendingFrame`, under a declared `let pending = false`, with `return pending`
  below the markers. Hint: *Set `pending` to true while the rolls this frame needs
  are still missing from `rolls`: a frame that opens with a 10 needs the two
  entries after it, a frame whose two rolls add to 10 needs the one entry after
  them, and an open frame needs nothing beyond its own two rolls.*
  The fallback `false` is wrong for `g-partial` and right for the three complete
  games - so it fails c-2-4 and c-2-6 and leaves c-2-1 and c-2-2 alone. It does
  **not** fail c-2-3: the lookahead never guards the end of `rolls`, so with
  `pending` stuck at `false` frames 5 and 6 come back as `NaN`, which serialises
  to `null` and matches c-2-3's expected body byte for byte.
- **`cut-game-total`**, writes into `total`. It is the body of `gameTotal`, under a
  declared `let total = -1`, with `return total` below the markers. Hint: *Set
  `total` to the score of the last frame that has one: the final entry of
  `frameScores` that is not null, and 0 for a game where not one frame has a score
  yet.*
  The fallback must be `-1` and **not** 0. A fallback of 0 would make c-2-5's
  empty-game case and c-2-4's `g-gutter` case pass on an empty skeleton, which is
  the "fallback that accidentally passes" defect.

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
not an empty cell.

That guarantee rests on the cut point above: `cut-score-lookahead` never tests
the length of `rolls`, so `cut-pending-frame` is the only block that can stop a
missing bonus roll becoming a number, **and that is what makes c-2-4 and c-2-6
fail when `cut-pending-frame` is empty** - `pending` stays `false`, `g-partial`'s
frames 5 and 6 score `NaN`, `gameTotal` returns `NaN` rather than 34, and the page
renders `NaN` rather than two empty cells. Were the guard written into
`cut-score-lookahead` instead - legal for a Builder if this spec did not decide
it, since `frameScore` is declared `number | null` - `g-partial` would come back
`[7,16,25,34,null,null]` with `cut-pending-frame` still empty, `total` would be 34
and the cells would be empty, and all three of c-2-3, c-2-4 and c-2-6 would pass
on an unwritten cut. The spec decides it: the guard lives in `pendingFrame`, which
is the function `cut-pending-frame` is the body of. The other multi-cut criteria hold: c-1-2, c-1-4 and c-1-5 need
both frame cuts, because nine frames is not ten, and c-2-4 and c-2-6 need all
three, because `-1` is not 34 and a number is not an empty cell.

**Cross-session dependency, stated because it is not in the `cuts` lists.**
`scoreGame` calls `frames(rolls)`, so every session-2 criterion except the two 400
halves of c-2-5 also needs `cut-frames-scan` and `cut-frames-tenth` filled. Those
two cuts are listed only against session-1 criteria, because that is where they
are taught and graded; by the time session 2 starts, the student has filled them.
On the fully open skeleton every session-2 criterion is red on its own cuts as
well, so the skeleton check sees what it expects either way.

Each pure function is graded against at least two fixtures, one of them an edge
case, so no cut can be answered with a hardcoded constant: `frames()` against
`g-mixed`, `g-partial` (rolls run out early) and `g-perfect` (a three-roll tenth);
`scoreGame()` against `g-perfect`, `g-mixed` and `g-partial`; `gameTotal()`
against `g-partial` (34, not the last entry) and the empty game (0).

## Session load

Estimated against the linter's own model, decisions counted from the hints as
written. These numbers reproduce exactly from `lint.json`:

| session | cuts | builds | concepts | setup | estimate |
|---|---|---|---|---|---|
| 1 | 2 (`cut-frames-scan` 7.8 + `cut-frames-tenth` 6.0) | 2 | 2 | yes | 38.8 min |
| 2 | 3 (`cut-score-lookahead` 7.9 + `cut-pending-frame` 6.0 + `cut-game-total` 6.0) | 1 | 3 | no | 37.4 min |

Both are under the 40 minute cap. The largest cut in session 2 is 40% of its cut
minutes, under the 45% share cap; session 1 has two cuts, where a share is
arithmetic rather than skew. Session 1 carries the setup and two cuts against
session 2's three, which is the rule E113 enforces.

**There is no unpriced work on top of these numbers.** Round 2 of this spec added
3 minutes to session 2 by hand for page markup and then claimed the session fitted
anyway; that adjustment is gone, because all page markup ships written and neither
session types any. Both sessions are `lib/` work plus a walk-through of shipped
files, and the walk-through is what the 3 minutes per build already pays for.

Read the estimate as a signal, not a measurement. Five consecutive projects have
overrun, pipeline-test-03 measured 47 minutes on a session the model priced at
38.5, and the model's worst known error is about 5 minutes. It under-reads
`cut-score-lookahead` in particular: three mutually exclusive rules live in that
block and the regex sees one stated decision. So the trims below are decided here,
in advance, rather than left to whoever is teaching:

- **Session 2 - `cut-game-total` is the block that goes.** If `cut-pending-frame`
  is not green by minute 30, the instructor hands `gameTotal` out written and
  reads it aloud instead of having it typed. It recovers about 6 minutes and costs
  the least of the three, because "the last frame that has a score" follows
  directly from `cut-pending-frame` once that one is understood. It is still a cut
  in `spec.json`, still in the skeleton, and still graded by c-2-4, c-2-5 and
  c-2-6 - what changes is who types it.
- **Session 1 - `cut-frames-tenth` is the block that goes.** If `g-mixed` is not
  rendering a nine-frame grid by minute 28, the tenth frame is handed out written
  and walked through. It recovers about 6 minutes. It costs more than session 2's
  trim, because the tenth frame is the session's second idea, which is why the
  trigger is later and this is the trim of last resort.

Both triggers are a clock check the instructor applies without judgement, and both
blocks are code a student would otherwise type, so both recover real minutes.
Whether either was pulled belongs in the step-13 dry-run note
(`pipeline dryrun <slug> --session N --minutes M --by <who> -m "..."`): two
consecutive dry runs could not say, and a measured overrun cannot be read without
it.

Do not relieve session 2 by moving a cut into session 1 - session 1 carries the
setup and must hold strictly fewer cuts.

## What changed in round 4

Round 3's report had 1 blocking finding and 5 worth a look, and round 3's
rejection brief asked for the blocking one and nothing else. That is what this
round does.

| finding | what was done |
|---|---|
| **A1** (blocking, owner `nothing`) - `cut-pending-frame` could be left empty with c-2-3, c-2-4 and c-2-6 all green, because nothing said whether the end-of-`rolls` test lived in the lookahead block or in `pendingFrame` | Resolved by deciding it. `cut-score-lookahead`'s bullet now states that the block applies the three arithmetic rules unconditionally and never tests the length of `rolls`, that `pendingFrame` is the only place the end of `rolls` is checked, and that `scoreGame` pushes `null` for a frame it reports pending. Grading integrity states the dependency where the guarantee is made, names the alternative implementation that would have made the cut ungradable, and says which function owns the guard. `cut-pending-frame`'s own bullet drops the conditional "only when the lookahead guards" and says outright that it does not fail c-2-3. |

Nothing else moved. No criterion was added or changed, no cut was added, moved or
reworded, and `spec.json` is byte-identical to round 3's - so `lint.json`'s two
session estimates (38.8 and 37.4), the five cut prices and the E110, E113 and W114
verdicts are the same numbers a person read at round 3.

Round 3's five worth-a-look findings are **deliberately kept**, as round 3's
rejection brief recorded:

| finding | owner | why it is kept |
|---|---|---|
| **B1** - the `i` convention is stated in the Outcome but not in either session-2 hint | `test-runner` | The two hints disagreeing on the convention makes `g-mixed`'s array wrong from frame 3, which c-2-2 catches at step 6 in the Builder loop. The Outcome states "carries a parallel index `i` into `rolls`, and advances `i` by the length of each frame", which is only consistent with `i` being the frame's first roll. |
| **B2** - a roll list stopping part-way through a frame is undefined behaviour behind the declared 200 | `nothing` | No graded value depends on it: all four seeded games end on a whole frame, and both readings answer 200. Kept rather than fixed so the Out of scope list is not extended for an input no criterion and no seed exercises. |
| **B3** - the unknown-id page does not say what the score cells and `game-total` do | `nothing` | c-1-6 asserts the message and the absence of `frame-1`, and both readings pass it. The cost is a cosmetic `-1` on a page that says the game does not exist. |
| **B4** - the minute model reads 0 decisions on `cut-frames-tenth` and `cut-pending-frame` while both state three cases | `pack-writer` | Read 38.8 and 37.4 as floors. The Pack Writer prices both sessions at step 9 from the plan it has written and a person reads that number at Gate 3; the two trims below Session load are already decided in advance for exactly this reason. Nothing in the spec changes. |
| **B5** - "scores not yet computed" is a state of the skeleton listed among the screen's states | `pack-writer` | The paragraph under Screens says what it is and why it exists (one skeleton is generated for the whole project), and no criterion reads it. It lands in session 1's guide as what the instructor should see on screen. |

Round 2's report had 3 blocking findings and 7 worth a look. Every one is
accounted for below, and none of it is undone.

| finding | what was done |
|---|---|
| **A1** - the frames hints named `frames`, the declared value was `out` | Resolved. All five cuts declare `writes_into` in `spec.json` (`out`, `out`, `frameScore`, `pending`, `total`) and every hint names that same symbol in backticks. The accumulator is `out` in prose and in both hints. E121 now checks this rather than a reader. |
| **A2** - nothing said how `scoreGame` got its frames | Resolved. The Outcome, the Data model and session 2's Builds all state that `scoreGame` calls `frames(rolls)`, holds it as `frameList`, and that `lib/score.ts` never chunks `rolls` itself. The lookahead hint now says "never into `frameList`", the symbol that actually exists. |
| **A3** - c-1-6 wanted a 404 and an id-interpolated message from a server component | Resolved by deciding the scope question: c-1-6 asserts the message text and that no `frame-1` element renders, and asserts no status. Out of scope now says `/games/[id]` answers 200 for every id and says why 404 was dropped rather than the server-only constraint. |
| **B1** - `pendingFrame` promised with no signature | Resolved. `pendingFrame(rolls: number[], i: number, frame: number[]): boolean` is in the Outcome, is called by `scoreGame` once per frame, and is where `cut-pending-frame` lives, over `let pending = false` / `return pending`. |
| **B2** - the scan index `cut-frames-tenth` needs was never declared | Resolved. `let i = 0` is declared above `cut-frames-scan` alongside `out`, both hints name `i`, and both blocks advance it. |
| **B3** - session 1's declared end state could not exist | Resolved. Session 1 ends with empty score cells and `game-total` reading `-1`, stated in Screens, in the session and in "Runs at the end". The state is renamed "scores not yet computed", and the reason is spelled out: one skeleton is generated for the whole project. |
| **B4** - the `-` gutter glyph and the seed order were stated and ungraded | Resolved without a new criterion. c-1-5 now pins `- 1` in `frame-6`, and c-1-1 pins the four ids in the seed's order. |
| **B5** - session 2 was over the cap once the spec's own adjustment applied | Resolved. The 3-minute markup adjustment is gone with a reason (no markup is typed in either session), and both trims are decided in advance with a named block and a clock trigger, instead of being offered as options. |
| **B6** - "empty" was not pinned against the markup | Resolved. A pending score cell contains no text: `textContent` is the empty string, and not a placeholder character. Stated in Screens and asserted in c-2-6, which is the criterion the integrity argument leans on. |
| **B7** - a non-JSON POST body had no declared status | Resolved. The endpoint treats an absent, empty or unparseable body as an absent `rolls` and answers the same 400, and c-2-5 grades it, so the undeclared 500 has no path. |

Round 1's three fixes are kept and not undone: c-2-6 still grades the rendered
score column, the page's data source is still stated for both sessions, and the
c-2-3 integrity claim still says plainly that it can pass with
`cut-pending-frame` empty - now unconditionally, which is round 4's fix rather
than a retreat from round 1's.
