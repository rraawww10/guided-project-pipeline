# Session 2 - Scoring and the running total

**Time:** the plan below runs to 48 minutes against the 40-minute cap. That is
an overrun of eight, disclosed at the bottom with what to trim. `spec.md` priced
this session at 37.4, and says itself that it under-reads
`cut-score-lookahead`. It does.

**Students start from:** session 1 finished. All four games draw their frame
grid with the right roll symbols - `/games/g-partial` shows six boxes reading
`3 4`, `7 2`, `9 -`, `8 1`, `X`, `X`. Every score cell is empty and the line
under the grid reads `total: -1`. c-1-1 to c-1-6 are green; all six session-2
criteria are red. `lib/score.ts` is three functions with three TODOs in them.

**Students end with:** `g-perfect` reading 300, `g-gutter` reading 0, `g-mixed`
reading 133, and `g-partial` showing `7`, `16`, `25`, `34` in its first four
score cells, **nothing at all** in the last two, and `34` as the game total.
`POST /api/games/score` answers all of that over HTTP, and answers 400 for a
body it cannot read. c-2-1 to c-2-6 green, and with them the whole project.

## What they learn

1. **Lookahead: a value that depends on items that come later.** A strike is
   worth 10 plus the next two rolls. Those rolls belong to the frames *after*
   it. This is the idea the project exists for, and no shipped project in the
   track has it.
2. **Look ahead in the roll list, never in the frame list.** The frames are
   already built; they are for drawing boxes. Scoring walks `frameList` to know
   how wide each frame is, and reads `rolls[i]`, `rolls[i + 1]`, `rolls[i + 2]`
   to know what it is worth. Two indexes, two jobs.
3. **The tenth frame needs no rule of its own.** A tenth-frame strike reaches
   forward for the two rolls after it, and those rolls are the tenth frame's own
   bonus rolls. It works out only because the lookahead is in the roll list. If
   somebody asks "where is the tenth-frame case?", the answer is: there is not
   one, and that is the payoff of point 2.
4. **`null` is a value, and it is not 0.** A frame whose bonus rolls have not
   been bowled has *no score*. `FrameScore = number | null` says so in the type,
   the page renders an empty cell for it, and the total skips it.
5. **Two jobs stay in two functions.** The scoring block does arithmetic and
   never asks whether the rolls exist. `pendingFrame` asks whether the rolls
   exist and never does arithmetic. Keeping them apart is what makes the
   pending frame a decision rather than an accident.
6. **Reading and validating a JSON POST body** - shipped written, read on
   screen at the end.

## Before you start

- **Check every student's grid before you teach anything.** `scoreGame` calls
  `frames(rolls)`, so a student whose session-1 work is unfinished cannot pass a
  single criterion today. Everyone must have six boxes on `/games/g-partial` and
  ten on `/games/g-mixed`. Pair up anyone who does not.
- Have open: `lib/score.ts`, and the browser on `/games/g-partial`.
- On the board, `g-mixed`'s first five frames with their rolls, and the answers,
  because you will walk them in the 4-9 block:

  ```text
  1 4 | 4 5 | 6 4 | 5 5 | 10        rolls
    5    14    29    49    60       cumulative
  ```

- Next to them, `g-partial`, which is where the session ends up:

  ```text
  3 4 | 7 2 | 9 0 | 8 1 | 10 | 10   ten rolls, six frames
    7    16    25    34    ?    ?
  ```

  Leave the two question marks on the board. Do not fill them in yet - that is
  the 22-25 block, and the whole session turns on them.

## The plan

| Minutes | What you do |
|---|---|
| 0-4 | Recap the grid. Open `/games/g-partial`: six boxes, an empty score column, `total: -1`. Say where `-1` comes from - a placeholder in `gameTotal` - and open `lib/score.ts`. Read the three function signatures out loud and nothing else. |
| 4-9 | The lookahead idea on the board. Score `g-mixed` frames 1 to 5 by hand: 5, 14, 29, 49, 60. Frame 3 is a spare, so it borrows roll 7. Frame 5 is a strike, so it borrows rolls 10 and 11. Ask where those rolls live: in the next frames. So scoring cannot walk the frame list. |
| 9-22 | Live: `cut-score-lookahead`. Before typing, say the sentence the hint leaves out (see below). Then reload: `g-partial` shows 7, 16, 25, 34 and then `NaN`, `NaN`. Run the suite - c-2-1, c-2-2 and c-2-3 go green, c-2-4, c-2-5 and c-2-6 stay red. |
| 22-25 | Fill in the two question marks on the board - with nothing. Frame 5 needs rolls 10 and 11; the game has ten rolls. `NaN` is the wrong answer to the right question, and `pendingFrame` is where the question gets asked. |
| 25-33 | Live: `cut-pending-frame`. Reload - the last two cells go blank. c-2-3 was already green and stays green: point that out and say why. |
| 33-38 | Live: `cut-game-total`. Reload - `total: 34` under a column whose last two cells are empty. |
| 38-44 | Students catch up. Circulate. Everyone checks all four games: 300, 0, 133, 34. Run the suite. |
| 44-48 | Read the shipped `POST /api/games/score` on screen: where `scoreGame` is called, and the one 400 body. Post an empty roll list from the terminal if you have a minute. Then the project is done. |

## Cut points in this session

All three are in `lib/score.ts`. Each is an assignment to a value declared above
it, with the `return` below - the same shape as session 1.

### cut-score-lookahead - `lib/score.ts:38`

**What students see**, copied out of `skeleton/lib/score.ts` - the loop is
shipped written and only the middle line is theirs:

```ts
  for (const frame of frameList) {
    const pending = pendingFrame(rolls, i, frame)
    let frameScore: number | null = null
    // TODO(cut-score-lookahead): Set `frameScore` to what this frame is worth: 10 plus the next two entries of `rolls` for a frame that opens with a 10, 10 plus the single entry after the pair for a frame whose two rolls add to 10, and the frame's own two rolls added together for anything else. Index into `rolls` at `i`, never into `frameList`.

    if (pending || frameScore === null) {
      scores.push(null)
    } else {
      running = running + frameScore
      scores.push(running)
    }
    i = i + frame.length
  }
```

**What they write.** Three exclusive branches, in this order: if the roll at `i`
is 10, the frame is worth 10 plus the next two rolls; else if the roll at `i` and
the one after it add to 10, it is worth 10 plus the roll after those two; else it
is worth those two rolls added together. No loop, no length test, no `null`.

**Say this before anyone types. It is the most important sentence in the
session:**

> "Do not test the length of `rolls` in this block. This block only does
> arithmetic. Deciding whether a score is allowed to exist at all is the next
> task, in `pendingFrame`."

The hint in the skeleton does not say it, the spec decides it in prose the
students never see, and nothing downstream catches a student who ignores it -
this is `ambiguity.md` B1. What happens if you skip the sentence: they will fill
this block, see c-2-4 and c-2-6 red with `NaN` on screen, correctly diagnose
"my arithmetic ran off the end of the array", and add a length guard *here*.
That turns c-2-4 and c-2-6 green with `cut-pending-frame`'s TODO still sitting
in the file, and the test suite will congratulate them for a task they never
did. The whole point of the project is in that task.

**Teach it like this.** "A frame is worth what you knocked down, plus what a
strike or a spare earns you next. So the score of frame 3 is not a fact about
frame 3 - it is a fact about the rolls that come after it. We are standing at
roll `i` and reading forward: `rolls[i + 1]`, `rolls[i + 2]`. The frame list
tells us how wide each frame is, so `i` knows where to stand. It never tells us
what anything is worth."

Four points to make while you type:

1. **`i` is the index of this frame's first roll**, and the shipped last line of
   the loop, `i = i + frame.length`, is what keeps it that way. A strike frame is
   one roll wide, so `i` moves by one. Show the two indexes side by side on
   `g-mixed`: frame 5 is `frameList[4]` and starts at `rolls[8]`.
2. **Strike first, then spare.** Order matters: a strike followed by a gutter
   roll also satisfies "the two rolls add to 10". Say that out loud, because the
   suite does not catch it - I checked every fixture, and swapping the two
   branches passes all twelve criteria. It is right, not graded.
3. **The tenth frame.** After the ninth frame, `i` is standing on the tenth
   frame's first roll and the bonus rolls it reaches for are the tenth frame's
   own second and third rolls. Nothing special happens. This is the moment the
   design pays off; do not skip it.
4. **`10 + rolls[i + 2]` for a spare, not `10 + rolls[i + 1] + rolls[i + 2]`.**
   The frame's own two rolls already add to 10, so writing `10` is the same as
   adding them - and the bonus is one roll, the next one after the pair.

**Reference solution** - instructor's copy, from `app/lib/score.ts`:

```ts
    if (rolls[i] === 10) {
      frameScore = 10 + rolls[i + 1] + rolls[i + 2]
    } else if (rolls[i] + rolls[i + 1] === 10) {
      frameScore = 10 + rolls[i + 2]
    } else {
      frameScore = rolls[i] + rolls[i + 1]
    }
```

**Passes when:** c-2-1 goes green - `[30,60,90,120,150,180,210,240,270,300]` for
the perfect game - and c-2-2 with it, which is `g-mixed`'s
`[5,14,29,49,60,61,77,97,117,133]`, the array that a wrong-but-plausible
`30 * frame` cannot fake. **c-2-3 also goes green here, and it should not be
believed.** With `pendingFrame` still returning `false`, `g-partial`'s last two
frames come out as `NaN`, `JSON.stringify(NaN)` is `null`, and the criterion's
expected body `[7,16,25,34,null,null]` matches byte for byte. Over HTTP, "not
computable yet" and "your arithmetic broke" are the same three characters. Say
that to the room - it is a better lesson than anything on the board - and then
point at the page, where `NaN` is very much not an empty cell.

### cut-pending-frame - `lib/score.ts:24`

**What students see**, copied out of `skeleton/lib/score.ts`:

```ts
export function pendingFrame(rolls: number[], i: number, frame: Frame): boolean {
  let pending = false
  // TODO(cut-pending-frame): Set `pending` to true while the rolls this frame needs are still missing from `rolls`: a frame that opens with a 10 needs the two entries after it, a frame whose two rolls add to 10 needs the one entry after them, and an open frame needs nothing beyond its own two rolls.
  return pending
}
```

**What they write.** The same three branches as the block before it, but each
one asks a question about `rolls.length` instead of doing arithmetic: is the
highest roll index this frame needs actually there? A strike needs `rolls[i + 2]`
to exist; a spare needs `rolls[i + 2]` to exist; an open frame needs
`rolls[i + 1]` to exist.

**Teach it like this.** "Frame 5 of `g-partial` is a strike at roll 9. It is
worth 10 plus rolls 10 and 11. There is no roll 11 - the game stopped. So frame
5 is not worth zero, and it is not worth 10: it is not worth *anything yet*.
This function is the one place in the project that knows the game might not be
finished."

Three points while you type:

1. **`rolls.length < i + 3` twice.** The strike branch and the spare branch turn
   out to be the same test - a strike needs the two rolls after `i`, a spare
   needs the one roll after the pair, and both of those are `rolls[i + 2]`. Let
   the room notice it. A student who merges the two branches is correct; the
   shipped code keeps them apart because the three cases are the lesson.
2. **Why `< i + 3` and not `<= i + 2`.** Both are right. Say whichever you find
   easier to read out loud and stick to it - the useful habit is "name the
   highest index I need, then ask whether the array is that long".
3. **The blanks spread forward.** Once frame 5 is pending, frame 6 is too, and
   the spec calls that a property of the algorithm rather than an extra rule -
   a later frame never needs an earlier roll. Nobody writes "and everything
   after it as well".

**Reference solution** - instructor's copy, from `app/lib/score.ts`:

```ts
  if (frame[0] === 10) {
    pending = rolls.length < i + 3
  } else if (frame[0] + frame[1] === 10) {
    pending = rolls.length < i + 3
  } else {
    pending = rolls.length < i + 2
  }
```

Note this block reads `frame`, not `rolls`, to decide which case it is in - it
is the one place in the file that is allowed to, because `frame` is what says
how the frame was bowled. The lookahead block reads `rolls[i]`. Both work; do
not let the room think the two blocks disagree.

**Passes when:** c-2-4 goes green - `total` 34 for `g-partial` and 0 for
`g-gutter` - *once `cut-game-total` is written too*. On its own, this block turns
the two `NaN` cells on the page into empty cells, which is visible immediately
and is the check to use in the room. c-2-3 was already green and stays green:
that is expected, and `mutation.json` records it.

### cut-game-total - `lib/score.ts:55`

**What students see**, copied out of `skeleton/lib/score.ts`:

```ts
/** The score of the last frame that has one. */
export function gameTotal(frameScores: FrameScore[]): number {
  let total = -1
  // TODO(cut-game-total): Set `total` to the score of the last frame that has one: the final entry of `frameScores` that is not null, and 0 for a game where not one frame has a score yet.
  return total
}
```

**What they write.** Start at 0, walk the array, and remember every entry that
is not `null`. Whatever is left in `total` at the end is the last real score.

**Teach it like this.** "The total is not the last number in the array - for
`g-partial` the last two entries are `null`. It is the last number *that
exists*. And a game where nothing has a score at all totals 0, not `-1`: `-1` is
the placeholder we have been staring at all session, and it has to be gone."

Two points, both of which are graded:

1. **Overwrite `total = 0` first.** The declared placeholder is `-1`, and the
   empty game must answer 0. c-2-5 posts `rolls: []` and asserts `total` is 0.
   If they leave `-1` in place for the empty case, that criterion stays red with
   `an empty game totalled -1, expected 0`.
2. **The obvious wrong answer does not compile**, which is a nice thing to show
   for ten seconds. `total = frameScores[frameScores.length - 1]` gets
   `error TS2322: Type 'FrameScore' is not assignable to type 'number'.` -
   TypeScript is telling them that the last entry may not exist as a number,
   which is exactly the fact this whole session is about.

**Reference solution** - instructor's copy, from `app/lib/score.ts`:

```ts
  total = 0
  for (const score of frameScores) {
    if (score !== null) {
      total = score
    }
  }
```

**Passes when:** c-2-5 goes green - the empty game totals 0 - and with the two
blocks before it, c-2-4 (34 and 0) and c-2-6 (the page: `7`, `16`, `25`, `34`,
two empty cells, and `34` as the game total). That is the whole project green.

## The code that ships written, and that you read on screen

The score cell, from `app/app/games/[id]/page.tsx`. This is the line that turns
`null` into no text at all, and c-2-6 asserts that the cell's text is exactly
empty - not a dash, not a space, not `null`:

```tsx
            <span className="score" data-testid={`total-${index + 1}`}>{scores[index] === null ? null : scores[index]}</span>
```

The page calls the two functions in process - it does not fetch its own API:

```tsx
  const frameList = frames(game.rolls)
  const scores = scoreGame(game.rolls)
  const total = gameTotal(scores)
```

The endpoint, from `app/app/api/games/score/route.ts`. Read the two guards and
the last two lines; the room has just written everything they call:

```ts
export async function POST(request: Request): Promise<Response> {
  let body: unknown = null
  try {
    body = await request.json()
  } catch {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const rolls = readRolls(body)
  if (rolls === null) {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const scores: FrameScore[] = scoreGame(rolls)
  return Response.json({ frames: scores, total: gameTotal(scores) })
}
```

Three things worth naming as you read it, in about a minute:

- **The `try` around `request.json()`.** A body that is not JSON throws. Without
  the `try` the route answers 500, which this endpoint never declared. c-2-5
  posts the literal text `{this is not json` and requires a 400.
- **One error body, declared once.** `const ERROR_BODY = { error: "rolls must be an array of numbers" }`
  is at the top of the file, and both 400 paths return it. c-2-5 asserts the two
  paths answer the *same* body.
- **An empty roll list is a legal game, not an error.** `[]` scores `[]` and
  totals 0. Also c-2-5.

If you have a spare thirty seconds, post something from the terminal so the room
sees the endpoint answer:

```text
curl -s -X POST http://localhost:3000/api/games/score \
  -H 'Content-Type: application/json' \
  -d '{"rolls":[3,4,7,2,9,0,8,1,10,10]}'
```

That prints `{"frames":[7,16,25,34,null,null],"total":34}` - and the two `null`s
are the ones that were `NaN` twenty minutes ago.

## Where students get stuck

- **"`total-5` and `total-6` read `NaN`."** - `cut-pending-frame` is still a
  TODO, so nothing stops the lookahead reading past the last roll. This is the
  expected state after the first block and it is the best thing on screen all
  session - use it. - "There is no roll 11. What should frame 5 be worth?"
- **"Everything is green but I never wrote `cut-pending-frame`."** - The one to
  watch for. They put a length test inside `cut-score-lookahead`, so
  `frameScore` goes `null` there and `pendingFrame` never gets a say. The suite
  cannot see it; you can, by looking at the file. - "Your arithmetic is deciding
  whether a frame counts. Move that decision to the function whose whole job it
  is, and let this block do arithmetic only."
- **"c-2-4 says `g-partial total is None, expected 34`."** - `total` came back
  `NaN` and JSON turned it into `null`, which arrives in the test as Python
  `None`. Same cause as the `NaN` cells: `pendingFrame` is unwritten. - "Your
  total is not a number. Look at frame 5."
- **"c-2-4 says `g-partial total is -1, expected 34`."** - Different cause:
  `cut-game-total` is still a TODO and `-1` is its placeholder. Nothing is
  broken; there is one task left.
- **"The score column shows the frame's own score, not the running total."** -
  They pushed `frameScore` instead of the accumulated `running`, which means
  they edited the shipped lines below the TODO. c-2-6 is the criterion that
  catches it: `g-partial` reads 7, 9, 9, 9 instead of 7, 16, 25, 34. - "Put the
  loop back the way it shipped. Your block only sets `frameScore`."
- **"Every score cell is empty and the total is `-1`, but I filled the
  block."** - `frameScore` is still `null` on every frame: either the branches
  assign to a new local variable instead of the declared `frameScore`, or the
  file has not compiled. Check the dev-server terminal first.
- **"c-2-2 is red and my perfect game is right."** - The `30 * frame` shape, or
  a spare that adds the wrong roll. `g-mixed` is the fixture that catches both.
  Read the array against the board: 5, 14, 29, 49, 60. The first wrong number
  names the frame and the rule. - "Which frame is the first one that disagrees?
  What kind of frame is it?"
- **"Frames 1 to 4 are right, everything after frame 5 is wrong."** - A strike
  frame advanced `i` by two. `i = i + frame.length` is shipped and correct, so
  this means they indexed into `frameList` rather than `rolls`, or added a
  second index of their own. - "How wide is a strike frame in the roll list?"
- **"`error TS2322: Type 'FrameScore' is not assignable to type 'number'.`"** -
  In `gameTotal`, they assigned the last array entry to `total`. That entry may
  be `null`. Filter first, or walk the array and keep the last non-null. - "The
  type is telling you the truth: the last entry might not be a score."
- **"`g-gutter` totals 0 and I think that is wrong."** - It is right, and it is
  why the spec insists the placeholder is `-1` rather than 0: an empty skeleton
  must not pass by accident. Twenty gutter balls score zero, and zero is a
  score.
- **"`POST /api/games/score` answers 400 and I do not know why."** - The body.
  `{"rolls": "1,2,3"}` is a string, not an array of numbers, and
  `{"rolls": [1, 4, "seven"]}` has a string in it. Both are 400 by design, with
  `{"error": "rolls must be an array of numbers"}`. Nobody edits that route
  today.
- **"I saved and the page did not change."** - The dev-server terminal has a
  TypeScript error and is still serving the last good build. Same as session 1.

## Check before moving on

This is the end of the project, so check all four games on the page, not just
the graded one:

- `/games/g-perfect` - ten boxes, `game-total` reads `300`, `total-10` reads
  `300`.
- `/games/g-gutter` - ten boxes of `- -`, every score cell `0`, `game-total`
  reads `0`.
- `/games/g-mixed` - `game-total` reads `133`, and the score column reads
  5, 14, 29, 49, 60, 61, 77, 97, 117, 133. That is the array to read out loud;
  the first number is `5`, which is frame 1's own two rolls and nothing else.
- `/games/g-partial` - `total-1` to `total-4` read `7`, `16`, `25`, `34`,
  `total-5` and `total-6` are **empty**, and `game-total` reads `34`.

Then `python3 -m pipeline test pipeline-test-04 --target skeleton` against a
finished student tree: 12 pass, 0 fail. And before anyone leaves, open
`lib/score.ts` and confirm there is no `TODO(` left in it - the one failure mode
this suite cannot see is the honest-looking green described above.

## Timing - the overrun and what to trim

The plan above is 48 minutes against the 40 cap. Where the eight extra minutes
are, block by block:

- `cut-score-lookahead` is priced here at 13 live minutes against the linter's
  7.9. It states three exclusive rules, an ordering rule between two of them, a
  rule about which array to index, and - if it is taught honestly - the rule the
  hint leaves out about not testing the length of `rolls`. `spec.md` says
  outright that its own model under-reads this block; it does, by about five.
- `cut-pending-frame` is 8 against 6.0. Three cases again, plus the discovery
  that two of them are the same test, plus the reason the blanks spread forward.
- `cut-game-total` is 5, near the linter's 6.0. It is the one honest number here.
- The remaining four minutes are the recap and the board work, which this
  session genuinely needs because everything in it stands on session 1's grid.

Trim in this order. Nothing here removes anything a criterion grades.

1. **The spec's own trim: hand out `cut-game-total` written.** The trigger is
   already decided - if `cut-pending-frame` is not green by minute 30, paste the
   five lines in and read them aloud instead of having them typed. Saves 5. It
   costs the least of the three, because "the last frame that has a score"
   follows directly from `cut-pending-frame` once that one has landed. It is
   still a cut in the skeleton and still graded by c-2-4, c-2-5 and c-2-6; what
   changes is who types it.
2. **Do not read the POST route.** Cut the 44-48 block to one minute: run the
   `curl`, say "this route calls the two functions you just wrote, and answers
   400 for a body it cannot parse", and stop. Saves 3. What is lost is the third
   concept the spec lists for this session, so if you pull this one, say so in
   the dry-run note - it is the trim that changes what the session teaches
   rather than how long it takes.
3. **Cut the 4-9 board work to three minutes.** Walk `g-mixed` frames 3 and 5
   only - one spare, one strike - and leave the open frames to the room. Saves 2.

Trim 1 alone brings the plan to 43. Trims 1 and 3 bring it to 41. All three
bring it to 40.

**Do not relieve this session by moving a cut into session 1.** The spec says
so and the linter enforces it: the session carrying the setup must hold strictly
fewer cuts than the others.
