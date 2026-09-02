# Session 1 - Setup, the games, and the frames

**Time:** the plan below runs to 46 minutes against the 40-minute cap. That is
an overrun of six, disclosed at the bottom with what to trim. `spec.md` priced
this session at 38.8.

**Students start from:** a skeleton that installs, builds and serves.
`/games/g-mixed` shows the heading `Spare Heavy`, **no frame boxes at all**, and
`total: -1`. `GET /api/games` answers 200 with four games whose `frames` are
every one of them `[]`. Of the twelve criteria, c-1-1 and c-1-6 are already
green - the route, the store and the unknown-id message ship written - and the
other ten are red.

**Students end with:** all four games drawing a correct frame grid with their
roll symbols. `g-perfect` has ten boxes ending in `X X X`; `g-mixed` has ten
ending in `2 / 6`; `g-partial` has **six** boxes and no seventh; `g-gutter` has
ten boxes of `- -`. Every score cell is still empty and `game-total` still reads
`-1`, because `lib/score.ts` is session 2's work. c-1-1 through c-1-6 green.

## What they learn

1. **A flat list is not the shape the problem has.** Twenty numbers arrive in
   one array; the scorecard needs them grouped. Nothing in the seed says where a
   frame ends - the rolls themselves decide.
2. **Scanning an array with a step that changes each iteration.** This is the
   session's real idea. A `for (let i = 0; i < n; i += 2)` cannot express it,
   because a strike consumes one roll and everything else consumes two. So the
   index is moved by hand inside the loop body, and the loop is a `while`.
3. **Two stopping conditions, not one.** The scan stops after nine frames *or*
   when the rolls run out, whichever comes first. Forget the second and the loop
   walks off the end of the array; forget the first and there is no tenth frame
   left to build.
4. **The tenth frame is whatever is left.** One `slice` answers all three of its
   cases - two rolls, three rolls, or no tenth frame at all.
5. **A server component reading a JSON seed through one store module.** Nobody
   fetches anything. The page calls a function, the function reads a file.

## Before you start

- One tree per student, installed and running: `npm ci` then `npm run dev` in
  `skeleton/`. Do this before the session, not in it - the install is minutes of
  dead air.
- Everyone on `http://localhost:3000/games/g-mixed`. There is no `/` route in
  this project; a student who opens the root will get a 404 and think the app is
  broken.
- Have open: `lib/frames.ts` (the file they will work in), `lib/symbols.ts` and
  `app/games/[id]/page.tsx` (both read-only today).
- On the board, before you say anything: the `g-partial` rolls and the six
  frames they make.

  ```text
  3 4 | 7 2 | 9 0 | 8 1 | 10 | 10          ten rolls, six frames
  ```

- Also on the board, the four ids: `g-gutter`, `g-perfect`, `g-mixed`,
  `g-partial`, and the frame table from `README.md`. Leave them up all session.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | What we are building. Open `/games/g-mixed` in the skeleton: a heading, no boxes, `total: -1`. Then `/api/games` in another tab: four games, every `frames` an empty array. Say where the empty array comes from and open `lib/frames.ts`. |
| 4-11 | Read the shipped code, in this order: `data/games.json`, `lib/types.ts`, `lib/store.ts`, `lib/symbols.ts`, then the page. Point at the one line in the page that draws a box, and say that everything on screen today is already written - their work is one file. |
| 11-15 | The frame idea on the board. Count `g-mixed` out loud roll by roll. Then `g-partial`: ten rolls, and ask the room how many frames. Most will say five. Show why it is six. |
| 15-27 | Live: `cut-frames-scan`. Reload after it compiles - `g-mixed` draws **nine** boxes, `g-partial` draws six. Run the suite: c-1-3 goes green on its own. |
| 27-34 | Live: `cut-frames-tenth`. Reload - `g-mixed` gets its tenth box reading `2 / 6`, `g-perfect` reads `X X X`, `g-partial` is unchanged at six. |
| 34-42 | Students catch up. Circulate. Everyone checks all four games against the frame table on the board. |
| 42-46 | Run the suite together - c-1-1 to c-1-6 green. Then point at the empty score column and the `-1`: that is session 2, and it is the interesting half. |

## Cut points in this session

Both live in `lib/frames.ts`, and this is the whole file as the student receives
it - copied out of `skeleton/lib/frames.ts`, header comment and all:

```ts
/** Split a flat roll list into frames. */
export function frames(rolls: number[]): number[][] {
  const out: number[][] = []
  let i = 0
  // TODO(cut-frames-scan): Walk `rolls` from the start and append the first nine frames to `out`, advancing `i` by two rolls per frame unless the first of them is 10, in which case the frame holds that one roll and `i` advances by one. Stop as soon as `rolls` runs out, so a 10-roll game leaves `out` with 6 entries.
  // TODO(cut-frames-tenth): Append one last entry to `out` holding every roll still left in `rolls` from `i` onwards - two rolls for an open tenth frame and three for a tenth that earned bonus rolls - and append nothing at all for a game whose rolls ran out earlier.
  return out
}
```

Three things to say about that shape before anyone types, because they apply to
all five cuts in the project:

- `out` and `i` are **already declared**. Their job is to fill `out` and move
  `i`; they do not declare anything new at the top and they do not touch the
  `return`.
- The `return out` below both TODOs is why the file compiles right now with
  nothing written. Nobody has to make the app build - it already builds.
- The two TODOs are two tasks in the same function, in order. The second one
  reads `i` where the first one left it.

### cut-frames-scan - `lib/frames.ts:15`

**What students see:** the first TODO line above, quoted exactly.

**What they write.** A `while` loop with two conditions - fewer than nine frames
in `out`, and `i` still inside `rolls`. Inside it, one `if`: when the roll at `i`
is 10, push a one-roll frame and move `i` on by one; otherwise push the roll at
`i` and the roll after it, and move `i` on by two.

**Teach it like this.** "Read the rolls left to right, once. Every frame you
finish, write it down. The only question at each step is *how far do I move* -
and that is what a strike changes. A `for` loop with `i += 2` in the header
decides that once, at the top, forever. We have to decide it every time round,
so the step goes in the body."

Make these four points while you type, in this order:

1. **Why nine and not ten.** The scan builds frames 1 to 9. The tenth is a
   different rule and is its own task next. Nine is in the loop condition, so
   there is no counter to keep.
2. **Why `i < rolls.length` is in the condition too.** `g-partial` runs out of
   rolls after six frames. Without that half of the condition, the loop keeps
   going, `rolls[i]` is `undefined`, and it happily pushes frames of `undefined`
   until it has nine of them. Show it if you have the nerve - it is a good
   thirty seconds - and see the point below about TypeScript.
3. **`out.push([rolls[i]])` for a strike, and nothing else.** One roll in that
   frame. This is what makes `frames()` and the score column line up in session
   2: a strike frame is one roll wide in the roll list too.
4. **TypeScript will not save them here.** `rolls[i + 1]` on a list that has run
   out is typed `number` and is `undefined` at runtime. There is no red squiggle
   and no exception - the numbers just quietly become `NaN` or the boxes read
   `undefined undefined`. Say it out loud: today the browser is the type checker.

**Reference solution** - instructor's copy, from `app/lib/frames.ts`:

```ts
  while (out.length < 9 && i < rolls.length) {
    if (rolls[i] === 10) {
      out.push([rolls[i]])
      i = i + 1
    } else {
      out.push([rolls[i], rolls[i + 1]])
      i = i + 2
    }
  }
```

**Passes when:** c-1-3 goes green - `GET /api/games` gives `g-partial` exactly
`[[3,4],[7,2],[9,0],[8,1],[10],[10]]`. That criterion is this cut on its own,
because `g-partial` never reaches a tenth frame. c-1-2, c-1-4 and c-1-5 are
still red at this point and that is correct: nine boxes is not ten.

**On screen after this block, and warn the room first:** `g-mixed` has nine
boxes and `g-perfect` has nine. Half the class will assume they have broken
something and start editing. Tell them the tenth box is the next task.

### cut-frames-tenth - `lib/frames.ts:16`

**What students see:** the second TODO line above, quoted exactly.

**What they write.** One `if` and one `push`: if `i` is still inside `rolls`,
append everything from `i` to the end as one frame. No loop, no arithmetic, no
counting to three.

**Teach it like this.** "The tenth frame is three cases - two rolls, or two rolls
plus a bonus, or three strikes. Do not write three cases. The rolls that are left
over *are* the tenth frame, whatever there are of them. And if nothing is left
over, the game stopped early and there is no tenth frame to write."

The reason this is its own task and not part of the scan is worth one sentence to
the class: the loop above answers "where does this frame end", and the tenth
frame is the one frame where the answer is "wherever the rolls do".

Two things students get wrong here, both worth pre-empting:

- **Appending unconditionally.** `g-partial` then grows a seventh frame that is
  an empty array, the page draws an empty seventh box, and c-1-3 - which was
  green a minute ago - goes red. The `if` is the "append nothing at all" clause
  of the hint.
- **Slicing a fixed width.** `rolls.slice(i, i + 3)` happens to pass every
  criterion in this project, and it is the wrong idea: it says the tenth frame is
  three rolls, when what is true is that it is the rest of them. Ask what it
  would do to a game with 21 rolls.

**Reference solution** - instructor's copy, from `app/lib/frames.ts`:

```ts
  if (i < rolls.length) {
    out.push(rolls.slice(i))
  }
```

**Passes when:** c-1-2 goes green - `g-mixed` frames equal
`[[1,4],[4,5],[6,4],[5,5],[10],[0,1],[7,3],[6,4],[10],[2,8,6]]` - and c-1-4 and
c-1-5 with it, which is the grid and the symbols on the page. All six session-1
criteria are green at this point.

## The code that ships written, and that you read on screen

You are reading these on screen in the 4-11 block. Nobody types them. Keep it to
the lines below; the styling and the layout are not worth a minute today.

The seed reader - the only thing in the project that knows where the file is,
from `app/lib/store.ts`:

```ts
/** The four seeded games, in the order the file lists them. */
export function allGames(): Game[] {
  const text = readFileSync(path.join(process.cwd(), "data", "games.json"), "utf8")
  return JSON.parse(text) as Game[]
}

/** The game carrying this id, or `undefined` when the id is not in the seed. */
export function findGame(id: string): Game | undefined {
  return allGames().find((game) => game.id === id)
}
```

The symbol rules, from `app/lib/symbols.ts`. Read the four lines in order and
the room can predict every box on screen for the rest of the session:

```ts
/** The symbol for the roll at `index` of this frame. */
export function rollSymbol(frame: Frame, index: number): string {
  if (index === 1 && frame[0] + frame[1] === 10) return "/"
  if (frame[index] === 10) return "X"
  if (frame[index] === 0) return "-"
  return String(frame[index])
}
```

The one line of the page that draws a box, from
`app/app/games/[id]/page.tsx`. Point at `frameList.map` and say it: one box per
entry `frames()` returned - so the number of boxes on screen is their answer,
not a fixed ten:

```tsx
        {frameList.map((frame, index) => (
          <li className="frame" key={index}>
            <span className="frame-number">{index + 1}</span>
            <span className="rolls" data-testid={`frame-${index + 1}`}>{frameSymbols(frame)}</span>
            <span className="score" data-testid={`total-${index + 1}`}>{scores[index] === null ? null : scores[index]}</span>
          </li>
        ))}
```

Two asides you may need, but do not go looking for them:

- The `data-testid` attributes are how the graded tests find anything, because
  class names get hashed. `frame-1` upwards for the boxes, `total-1` upwards for
  the score cells.
- The score cell on that third line is session 2's. It renders nothing at all
  today, which is why the column is blank rather than showing zeroes.

The endpoint, from `app/app/api/games/route.ts` - one call to the function they
are about to write, which is why `frames` is `[]` everywhere right now:

```ts
export async function GET(): Promise<Response> {
  const games = allGames().map((game) => ({
    id: game.id,
    name: game.name,
    rolls: game.rolls,
    frames: frames(game.rolls),
  }))
  return Response.json(games)
}
```

And the unknown-id half of the page, which is why c-1-6 is green before anyone
starts. Worth ten seconds at the end of the session if you have them - it is the
only place in the project where the page decides between two shapes:

```tsx
  if (game === undefined) {
    return (
      <main className="page">
        <h1>Tenpin</h1>
        <p className="missing" data-testid="no-game">{`No game with id ${id}`}</p>
      </main>
    )
  }
```

## Where students get stuck

- **"There are no boxes at all and the total says `-1`."** - Nothing is wrong.
  That is the skeleton before `cut-frames-scan` is written: `frames()` returns an
  empty array, so the page maps over nothing, and `-1` is `gameTotal`'s
  placeholder until session 2. - "That is where everybody starts. The grid is
  your first job."
- **"The page hangs / the tab is stuck loading / my laptop fan came on."** - A
  `while` loop that never advances `i`, or one whose only condition is
  `out.length < 9` while `i` never reaches a frame boundary. Nothing renders
  because the server is still in the loop. - Stop the dev server with Ctrl-C.
  "What moves `i` on? Say it out loud for a strike and for an open frame."
- **"`g-partial` shows nine boxes and the last three read `undefined
  undefined`."** - The loop condition is missing `i < rolls.length`, so the scan
  kept going past the end of the roll list and pushed frames of `undefined`.
  c-1-3 reads `g-partial split into 9 frames, expected 6`. - "The game stopped.
  Your loop did not."
- **"`g-partial` shows five boxes, and the fifth reads `X X`."** - Pair
  chunking: two rolls per frame with no strike case, so the two closing strikes
  got packed into one frame. This is the mistake the fixture exists to catch. -
  "A strike is one roll. The frame is over - there is no second ball."
- **"`g-mixed` has eleven boxes and `frame-10` reads `2 /`."** - The scan
  condition is `out.length < 10` instead of `< 9`, so the scan built the tenth
  frame as a pair and the tenth-frame block appended the leftover as an
  eleventh. - "The scan builds nine. The tenth is the other block's job."
- **"`g-partial` has a seventh box and it is empty, and c-1-3 just went red."** -
  `cut-frames-tenth` appends without checking `i < rolls.length`, so it pushed
  `rolls.slice(10)`, which is `[]`. - "That game has no tenth frame at all. Your
  block has to be allowed to do nothing."
- **"One giant box holding the whole game."** - `cut-frames-tenth` is written
  and `cut-frames-scan` is still a TODO, so `i` is 0 and the slice takes
  everything. Common in anyone who does the easy task first. - "Fill the scan and
  this fixes itself."
- **"`frame-10` reads `X X X X` on `g-perfect`."** - A tenth frame built by
  slicing four rolls, or the scan advancing by one on a non-strike. Count the
  rolls consumed: nine frames of one roll each is nine, leaving three.
- **"The tenth frame shows `X X /` instead of `X X X`."** - Not their bug, and
  not possible from `lib/frames.ts` - if you see it, someone edited
  `lib/symbols.ts`. `10 + 10` is 20, not 10, so no `/`. Put the file back.
- **"I saved and the page did not change."** - Look at the terminal running
  `npm run dev`. A TypeScript error stops the rebuild and the last good bundle
  keeps being served. The browser is telling you the truth about five minutes
  ago.
- **"`Module not found: Can't resolve '@/lib/frames'`."** - The dev server was
  started from the wrong directory. `@/*` maps to the tree holding
  `package.json`. Restart it from `skeleton/`.

## Check before moving on

`/games/g-mixed` draws ten boxes reading
`1 4`, `4 5`, `6 /`, `5 /`, `X`, `- 1`, `7 /`, `6 /`, `X`, `2 / 6`.
`/games/g-perfect` draws ten, the tenth reading `X X X`.
`/games/g-partial` draws **six** - `3 4`, `7 2`, `9 -`, `8 1`, `X`, `X` - and
there is no seventh box.
`/games/no-such-game` says `No game with id no-such-game`.

Then run `python3 -m pipeline test pipeline-test-04 --target skeleton` if you
want the numbers: c-1-1 to c-1-6 pass, and the six session-2 criteria fail.
Anyone whose grid is wrong must be fixed before session 2 starts - `scoreGame`
calls `frames(rolls)`, so a broken scan makes every session-2 criterion
unreachable.

## Timing - the overrun and what to trim

The plan above is 46 minutes against the 40 cap. Where the six extra minutes
are: `cut-frames-scan` is priced here at 12 live minutes, not the 7.8 the linter
charges, because the block states three decisions - the strike case, the open
case, and two stopping conditions - and the moving step is the session's whole
idea rather than a detail. `cut-frames-tenth` is 7 against 6.0, because "append
nothing at all" has to be argued for. The rest is the setup this session
carries: five shipped files to read and an install to nurse.

Trim in this order. Nothing here removes anything a criterion grades.

1. **The spec's own trim: hand out `cut-frames-tenth` written.** The trigger is
   already decided - if `g-mixed` is not rendering a nine-frame grid by minute
   28, paste the three lines in and read them aloud instead of having them
   typed. Saves 6, and brings the plan to 40 on its own. It costs the most of
   the three, because the tenth frame is the session's second idea, which is why
   it is the trim of last resort in the spec and the first one here only when
   the clock has already gone.
2. **Cut the 11-15 board work to two minutes.** Draw `g-partial` and count it.
   Drop `g-mixed` - it is on the board already. Saves 2.
3. **Read only `lib/store.ts` and the one `frameList.map` line.** Name
   `types.ts`, `symbols.ts` and the route, and let anyone curious read them
   later. Saves 3.

Trims 2 and 3 together bring the plan to 41 without touching a cut point, which
is the order I would actually use. All three bring it to 35.
