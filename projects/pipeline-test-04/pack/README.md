# Tenpin - instructor pack

Four ten-pin bowling games arrive as flat lists of numbers. `data/games.json`
holds nothing but an id, a name and the rolls in the order they were bowled.
Session 1 turns each flat list into frames and draws it as a scorecard - one box
per frame, the roll symbols inside it. Session 2 scores it: a strike or a spare
reaches **forward** into the rolls that come after it, so a frame whose bonus
rolls have not been bowled yet has no score at all, and the page leaves that
cell blank while still showing a total.

The idea being taught is that **an item's value can depend on items that come
later**, and that "not computable yet" is a real value, distinct from zero.
TypeScript makes a student spell that out: `FrameScore = number | null`.

**Stack:** Next.js 15.5.24 App Router, React 19, TypeScript 5.7 strict.
No database, no writes to disk at runtime, no clock, no API key, no client
state - there is no `useState` anywhere in this project. The seed file is read
on every request and never modified, so the app answers the same on the tenth
run as on the first.

**Shape:** 2 sessions, 5 cut points, 12 acceptance criteria. Every cut is in
`lib/`.

---

## Read this before you schedule the sessions

`spec.md` prices session 1 at 38.8 minutes and session 2 at 37.4, against a
40-minute cap. **This pack does not agree.** Timed block by block against the
real code, the plans come out at:

| session | spec estimate | this pack | over the cap by |
|---|---|---|---|
| 1 - Setup, the games, and the frames | 38.8 | **46** | 6 |
| 2 - Scoring and the running total | 37.4 | **48** | 8 |

Three things the person at Gate 3 should know about that gap.

**The spec says to read its own numbers as floors, and names why.** Session
load: "It under-reads `cut-score-lookahead` in particular: three mutually
exclusive rules live in that block and the regex sees one stated decision."
`lint.json` scores 0 decisions on `cut-frames-tenth` and `cut-pending-frame`
while both hints state three cases each - that is finding B4 in `ambiguity.md`,
owned by this agent, and the table above is the answer to it.

**Both of this spec's named trims are real.** Unlike the last project, they are
not page markup that ships written: `cut-frames-tenth` and `cut-game-total` are
blocks a student would otherwise type, so handing one out written recovers live
minutes. Each session file names its trigger, its saving, and two further trims
of my own. Session 1 reaches 40 with the spec's trim alone. Session 2 needs the
spec's trim plus one of mine.

**This is the sixth consecutive project to land over the cap.** `lessons.md`
already says the estimate is not the fix, and that no run so far has confirmed a
trim was actually pulled in a live room. So: whoever teaches this, record which
trims you pulled in the step-13 dry-run note, or the measurement cannot be read.

---

## What the student is handed

The skeleton is the finished app with five function bodies removed. Everything
else ships written - the scaffold, the types, the seed, the store, the roll
symbols, both API routes and the whole page.

```text
skeleton/
  app/
    layout.tsx                     (ships written)
    globals.css                    (ships written)
    api/games/route.ts             ep-games-list   (ships written)
    api/games/score/route.ts       ep-games-score  (ships written)
    games/[id]/page.tsx            sc-game, a server component (ships written)
  lib/
    types.ts                       (ships written)
    store.ts                       the one reader of the seed (ships written)
    symbols.ts                     X, /, - and the digits (ships written)
    frames.ts                      2 TODOs - session 1
    score.ts                       3 TODOs - session 2
  data/games.json                  the seed, read-only (ships written)
```

**No student types a line of JSX or a line of routing in this project.** Say
that on day one, because someone will go looking for their work in `app/` and
will not find it. All five cuts are in two files: `lib/frames.ts` and
`lib/score.ts`.

On the untouched skeleton the graded suite is **2 pass, 10 fail**: c-1-1 and
c-1-6 are green, because the route, the store and the unknown-id message all
ship written. That is the intended starting state, not a broken install.

## The five cut points

| cut | skeleton file:line | session | graded by | fails alone on |
|---|---|---|---|---|
| `cut-frames-scan` | `lib/frames.ts:15` | 1 | c-1-2, c-1-3, c-1-4, c-1-5 | c-1-3 |
| `cut-frames-tenth` | `lib/frames.ts:16` | 1 | c-1-2, c-1-4, c-1-5 | c-1-2 |
| `cut-pending-frame` | `lib/score.ts:24` | 2 | c-2-3, c-2-4, c-2-6 | c-2-4 |
| `cut-score-lookahead` | `lib/score.ts:38` | 2 | c-2-1, c-2-2, c-2-3, c-2-4, c-2-6 | c-2-1 |
| `cut-game-total` | `lib/score.ts:55` | 2 | c-2-4, c-2-5, c-2-6 | c-2-5 |

"Fails alone on" is the criterion that goes red when *only* that cut is left
empty, so it is the one to point a stuck student at. Those columns are not
guesses - `mutation.json` removed each block on its own and recorded which
criteria went red. Two rows are worth reading before you teach session 2.

- `cut-pending-frame` removed on its own turns **c-2-4 and c-2-6** red and
  leaves **c-2-3 green**. That is not a hole in the suite; it is this project's
  own lesson stated in reverse, and session 2 explains it where it lands.
- Every one of the five turns at least one of its own criteria red, so no cut in
  this project grades nothing.

**Cross-session dependency.** `scoreGame` calls `frames(rolls)`. So every
session-2 criterion except the two 400 halves of c-2-5 also needs both session-1
cuts filled. A student who arrives at session 2 with `lib/frames.ts` unfinished
cannot pass anything in session 2 - pair them up before you start.

## The twelve criteria

| id | session | what it reads | test file |
|---|---|---|---|
| c-1-1 | 1 | `GET /api/games` - four games, the seed's order, four keys each | `verify/test_api_games.py` |
| c-1-2 | 1 | `g-mixed` splits into ten frames with a three-roll tenth | `verify/test_api_games.py` |
| c-1-3 | 1 | `g-partial` stops after **six** frames when the rolls run out | `verify/test_api_games.py` |
| c-1-4 | 1 | `/games/g-perfect` - ten boxes, `frame-10` reads `X X X` | `verify/test_ui_game.py` |
| c-1-5 | 1 | `/games/g-mixed` - five boxes, one per symbol rule | `verify/test_ui_game.py` |
| c-1-6 | 1 | `/games/no-such-game` - the message, and no `frame-1` | `verify/test_ui_game.py` |
| c-2-1 | 2 | `POST /api/games/score` - the perfect game to 300 | `verify/test_api_score.py` |
| c-2-2 | 2 | the mixed game's whole cumulative array | `verify/test_api_score.py` |
| c-2-3 | 2 | the partial game's last two frames as `null` | `verify/test_api_score.py` |
| c-2-4 | 2 | `total` 34 for `g-partial`, `total` 0 for `g-gutter` | `verify/test_api_score.py` |
| c-2-5 | 2 | two 400s with the same body, and the empty game | `verify/test_api_score.py` |
| c-2-6 | 2 | `/games/g-partial` - four numbers, two empty cells, `34` | `verify/test_ui_game.py` |

All twelve pass on `app/` - `results.json`, 12 pass / 0 fail, and the Builder
used no retries.

## The seed, and every number the sessions check against

Put the tables below on the board and leave them there. Students check their own
work against them all session, and every expected value in the suite comes from
them.

The two games you will actually demonstrate on, copied out of `data/games.json`:

```json
  {
    "id": "g-mixed",
    "name": "Spare Heavy",
    "rolls": [1, 4, 4, 5, 6, 4, 5, 5, 10, 0, 1, 7, 3, 6, 4, 10, 2, 8, 6]
  },
  {
    "id": "g-partial",
    "name": "Stopped at Six",
    "rolls": [3, 4, 7, 2, 9, 0, 8, 1, 10, 10]
  }
```

| id | name | rolls |
|---|---|---|
| `g-gutter` | All Gutters | twenty `0` rolls |
| `g-perfect` | Perfect Game | twelve `10` rolls |
| `g-mixed` | Spare Heavy | the 19 rolls above |
| `g-partial` | Stopped at Six | the 10 rolls above |

| game | frames | cumulative scores | total |
|---|---|---|---|
| `g-gutter` | ten frames of `[0,0]` | `[0,0,0,0,0,0,0,0,0,0]` | `0` |
| `g-perfect` | nine `[10]` then `[10,10,10]` | `[30,60,90,120,150,180,210,240,270,300]` | `300` |
| `g-mixed` | `[[1,4],[4,5],[6,4],[5,5],[10],[0,1],[7,3],[6,4],[10],[2,8,6]]` | `[5,14,29,49,60,61,77,97,117,133]` | `133` |
| `g-partial` | `[[3,4],[7,2],[9,0],[8,1],[10],[10]]` | `[7,16,25,34,null,null]` | `34` |

Two of these four games are traps for the teacher as much as the student:
`g-perfect` alone is satisfied by `30 * frame` and `g-gutter` alone is satisfied
by `0`. **`g-mixed` is the game to demonstrate on**, because two mistakes that
cancel cannot survive `[5,14,29,49,60,61,77,97,117,133]`. `g-partial` is the
edge case: its rolls run out mid-game, which is what forces six frames instead
of ten and two blank score cells instead of two zeroes.

## Roll symbols

Shipped written in `lib/symbols.ts`. A roll of 10 is `X`; the second roll of a
frame whose first two rolls add to 10 is `/`; a roll of 0 is `-`; anything else
is its digit. A box holds its symbols joined by one space.

| frame | reads |
|---|---|
| `[1,4]` | `1 4` |
| `[6,4]` | `6 /` |
| `[10]` | `X` |
| `[0,1]` | `- 1` |
| `[0,0]` | `- -` |
| `[2,8,6]` | `2 / 6` |
| `[10,10,10]` | `X X X` |

The last row catches people out, so know the answer before you are asked: the
tenth frame of `g-perfect` is three strikes, and `10 + 10` is 20, not 10, so no
`/` appears anywhere in it.

## How to run it

Each tree has its own `node_modules`. Install in whichever one you are opening.

```text
cd projects/pipeline-test-04/skeleton     # or .../app for the finished build
npm ci
npm run dev
```

Then open `http://localhost:3000/games/g-mixed`. There is no index page in this
project - `/` is not a route. Every URL is `/games/<id>`, and the four ids are
`g-gutter`, `g-perfect`, `g-mixed` and `g-partial`.

Use `npm run dev`, not `npm run start`: the page and both routes are
`force-dynamic`, and a stale production build will not pick up an edit to
`lib/`.

To run the graded suite yourself, let the pipeline boot the app:

```text
python3 -m pipeline test pipeline-test-04 --target skeleton
python3 -m pipeline test pipeline-test-04 --target app
```

It builds, starts the server on a free port, sets `BASE_URL`, runs pytest with
Playwright, and writes `skeleton-results.json` / `results.json`. Do not start a
server yourself first.

## Four things about this spec you should know before you teach it

All four were raised at Gate 1 and left in deliberately. They land in the
teaching, so they are handled here.

**1. The hint for `cut-score-lookahead` is missing the one rule that decides
whether a student finishes session 2 honestly.** The spec decides, in prose a
student never reads, that the scoring block applies its three arithmetic rules
*unconditionally* and never tests the length of `rolls` - `pendingFrame` is the
only place the end of the roll list is checked. The hint in the skeleton does not
say so. A student who fills the scoring block, sees c-2-4 fail, and then puts a
length guard in the block they happen to be looking at will turn c-2-4 and c-2-6
green **with `cut-pending-frame`'s TODO still in the file** - and the tests will
have told them they are finished with a task they never wrote. This is
`ambiguity.md` B1, and no downstream checker owns it. Session 2 tells you when to
say the missing sentence out loud. Say it before they type, not after.

**2. The scan hint states a consequence that is false in general.** It reads
"Stop as soon as `rolls` runs out, so a 10-roll game leaves `out` with 6
entries." Six is a property of *`g-partial`*, whose last two frames are strikes.
Ten rolls of open frames leave five entries, and the POST endpoint accepts any
array of numbers, so a student can send exactly such a game in session 2 and be
told the hint lied to them. Teach the sentence as "`g-partial`'s ten rolls leave
`out` with 6 entries". `ambiguity.md` B4.

**3. A padded ten-box grid would pass all twelve criteria.** The spec says one
box and one score cell per entry `frames()` returned - so `g-partial` renders
six of each and no `frame-7` - and no criterion grades it. The shipped app is
correct, and nothing would catch a regression; nothing asserts that `no-game` is
absent on a valid game's page either. Do not tell a class the tests would catch
a padded grid. `ambiguity.md` B3, hand-checked at Gate 2.

**4. Two things here are correct-but-ungraded, so correct them by explaining and
not by pointing at a red test.** Both hand-checked against all four seeded games
while writing this pack:

- In `cut-score-lookahead`, testing for a **spare before** a strike still passes
  every one of the twelve criteria. It should not: a strike followed by a gutter
  roll matches `rolls[i] + rolls[i + 1] === 10`. It survives here only because
  `g-mixed`'s frame 5 is exactly that case and both readings happen to produce
  11. Teach strike first because it is right, and know that the suite does not
  care.
- In `cut-pending-frame`, the strike branch and the spare branch reduce to the
  same test, `rolls.length < i + 3`. A student who merges them into one branch is
  correct. The shipped code keeps them apart because the hint states three cases
  and the three cases are the lesson.

## Files in this pack

- `session-1.md` - Setup, the games, and the frames
- `session-2.md` - Scoring and the running total
- `troubleshooting.md` - the errors students actually hit, and what to say
