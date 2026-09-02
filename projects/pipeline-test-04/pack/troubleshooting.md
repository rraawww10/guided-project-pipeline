# Troubleshooting

Every entry below has a cause and a sentence you can say. Ordered by when in the
two sessions you will hit it.

## Getting it running

**`npm ci` fails with `EUSAGE` or complains about the lock file.** Use
`npm install` in that tree instead. `skeleton/` and `app/` each have their own
`package-lock.json` and their own `node_modules`; installing in one does nothing
for the other.

**`npm ci` prints a security advisory for `next`.** Read it and carry on for the
session. It does not stop the build. Worth noting because a green deploy check
has hidden a CVE line in this pipeline before.

**`Cannot find module 'next'`.** No `node_modules` in *this* tree. Install here.

**`Error: listen EADDRINUSE :::3000`.** Something is already on port 3000, very
often a `next` server left behind by a run that was closed with the window
rather than with Ctrl-C. Kill it, or run `npm run dev -- -p 3001` and tell the
room the new port.

**`Module not found: Can't resolve '@/lib/frames'`** (or `@/lib/score`,
`@/lib/store`). `@/*` is mapped to the tree root in `tsconfig.json`, so it only
resolves when the dev server was started from the directory holding
`package.json`. Someone ran `npm run dev` one level up, or opened the editor on
the repository root. Restart the server from `skeleton/`.

**`/` is a 404.** Correct. There is no index page in this project. The routes
are `/games/g-gutter`, `/games/g-perfect`, `/games/g-mixed` and
`/games/g-partial`, plus `/api/games` and `/api/games/score`.

**Any other id, like `/games/mixed`, says `No game with id mixed`.** Also
correct - that is the shipped unknown-id branch and the criterion c-1-6 grades.
The ids all begin with `g-`.

**The page never changes, no matter what is saved.** Look at the terminal
running `npm run dev`. A TypeScript error stops the rebuild and the last good
bundle keeps being served. The browser is telling you the truth about five
minutes ago. This is the single most common false alarm in both sessions - check
the terminal before you believe anything on screen.

**An edit to `data/games.json` does nothing.** You are on `npm run start`
against a build made before the edit. The page and both routes are
`force-dynamic`, so `npm run dev` re-reads the file on every request. (Nothing
in either session needs the seed edited. If a student has edited it, put it
back - every expected value in the suite comes from those four games.)

## What the skeleton is supposed to look like

Three of these get reported as bugs every time. They are all correct.

**Before session 1: no frame boxes at all, and `total: -1`.** `frames()` returns
an empty array, so the page maps over nothing, and `-1` is the placeholder in
`gameTotal` until session 2. `GET /api/games` answers 200 with four games whose
`frames` are all `[]`. The graded suite is 2 pass / 10 fail - c-1-1 and c-1-6
are the two, because the route, the store and the unknown-id message ship
written.

**Halfway through session 1: nine boxes on `g-mixed` and nine on `g-perfect`.**
`cut-frames-scan` builds frames 1 to 9 and `cut-frames-tenth` is a separate
task. Warn the room before they reload, or half of them will start undoing good
work.

**Start of session 2: a full grid with an empty score column and `total: -1`.**
Every score cell is empty because `scoreGame` pushes `null` for every frame
while `cut-score-lookahead` is unwritten, and `-1` is `gameTotal`'s placeholder.
No session-1 criterion reads a score cell or the total, which is why session 1
can be green in this state.

## Session 1 - the frames

**The tab hangs, nothing renders, the laptop fan comes on.** An infinite loop in
`cut-frames-scan`: either `i` is never advanced, or the only stopping condition
is `out.length < 9` and the loop can no longer reach a frame boundary. The
server is stuck inside `frames()`, so there is no error to see - just no
response. Ctrl-C the dev server. "What moves `i` on? Say it for a strike, then
say it for an open frame."

**`g-partial` renders nine boxes and the last three read
`undefined undefined`.** The loop condition is missing `i < rolls.length`, so
the scan kept walking past the end of the roll list and pushed frames of
`undefined`. Over HTTP those come back as `null`, and c-1-3 fails with
`g-partial split into 9 frames, expected 6`. "The game stopped. Your loop did
not."

**`g-partial` renders five boxes and the fifth reads `X X`.** Pair chunking -
two rolls per frame, no strike case - so the two closing strikes were packed
into one frame. This is exactly the mistake `g-partial` exists to catch. "A
strike is one roll. The frame is over; there is no second ball."

**`g-mixed` renders eleven boxes, `frame-10` reads `2 /` and `frame-11` reads
`6`.** The scan condition is `out.length < 10` instead of `< 9`, so the scan
built a tenth frame as a pair and the tenth-frame block appended the leftover as
an eleventh. "The scan builds nine. The tenth frame is the other block's job."

**`g-partial` grows an empty seventh box, and c-1-3 goes red after it was
green.** `cut-frames-tenth` appends without checking `i < rolls.length`, so it
pushed `rolls.slice(10)`, which is `[]`. "That game has no tenth frame at all.
Your block has to be allowed to do nothing."

**One enormous box holding the whole game.** `cut-frames-tenth` is filled and
`cut-frames-scan` is still a TODO, so `i` is 0 and the slice takes everything.
Common in whoever did the easy task first. Fill the scan and it fixes itself.

**`frame-10` on `g-perfect` reads `X X X X`, or `X X`.** The tenth frame is
whatever is left after nine frames, and nine strikes consume nine rolls of
twelve. Either the scan advanced by the wrong amount on a strike, or the tenth
block sliced a fixed width from the wrong place. Count the rolls consumed out
loud.

**`frame-10` on `g-perfect` reads `X X /`.** Not reachable from `lib/frames.ts`.
Somebody edited `lib/symbols.ts`. `10 + 10` is 20, not 10, so there is no `/`
anywhere in that box. Put the file back.

**A box reads `9 0` where the board says `9 -`.** Also `lib/symbols.ts`, also
not theirs to edit: a roll of 0 renders as `-`. c-1-5 grades that glyph on
`g-mixed`'s sixth frame, `- 1`.

**c-1-4 fails with `Locator expected to have count '10'` and
`Actual value: 0`.** No boxes on the page at all, so this is `cut-frames-scan`
unwritten (or not compiling). Look at the page before you look at the code.

**"The hint says a 10-roll game gives 6 frames and mine gives 5."** Both can be
right - it depends on the game. Six is a property of `g-partial`, whose last two
frames are strikes and therefore one roll each. Ten rolls of open frames make
five frames. The hint's sentence is loose; the spec knows (`ambiguity.md` B4).
"Read it as: `g-partial`'s ten rolls leave six frames."

## Session 2 - the scoring

**`total-5` and `total-6` read `NaN`.** `cut-pending-frame` is still a TODO, so
`pending` is always `false` and nothing stops the lookahead reading past the
last roll: `10 + 10 + undefined` is `NaN`. This is the expected state after the
first block, and it is the best thing on screen all session. "There is no roll
11. So what should frame 5 be worth?"

**Everything is green and `cut-pending-frame` is still a TODO.** The one to
watch for, and the reason to read the file rather than the test output. They put
a length test inside `cut-score-lookahead`, `frameScore` goes `null` there, and
`pendingFrame` never gets a say. c-2-4 and c-2-6 pass anyway. The suite cannot
see this (`ambiguity.md` B1) and neither can any checker in the pipeline. "Your
arithmetic is deciding whether a frame counts. Move the decision into the
function whose whole job it is."

**c-2-4 fails with `g-partial total is None, expected 34`.** `total` came back
`NaN`; `JSON.stringify(NaN)` is `null`, and the test reads that as Python
`None`. Same root cause as the `NaN` cells - `pendingFrame` is unwritten. "Your
total is not a number. Look at frame 5."

**c-2-4 fails with `g-partial total is -1, expected 34`.** Different cause, and
nothing is broken: `cut-game-total` is still a TODO and `-1` is its placeholder.
One task left.

**c-2-5 fails with `an empty game totalled -1, expected 0`.** Same cause. An
empty roll list has no frames, so no branch of `gameTotal` ever ran - which is
why the block has to start by setting `total` to 0.

**c-2-3 is green and the page still shows `NaN`.** Not a contradiction, and
worth ninety seconds of the room's time. Over HTTP, `NaN` serialises to `null`,
so `[7,16,25,34,null,null]` comes back byte for byte whether the frames are
pending or the arithmetic ran off the end. c-2-4 compares a total and c-2-6
reads the page, and those two can tell the difference. "The endpoint cannot see
the bug. The page can."

**Every score cell is empty and the total is `-1` after filling the lookahead
block.** `frameScore` never got assigned: either the branches assign to a new
variable of their own (`const score = ...`) instead of the declared
`frameScore`, or the file is not compiling. Check the dev-server terminal first.

**The column shows 7, 9, 9, 9 instead of 7, 16, 25, 34.** Per-frame scores, not
cumulative. The accumulation is shipped written below the TODO -
`running = running + frameScore` - so this means the shipped lines were edited.
c-2-6 is the criterion that catches it. "Put the loop back as it shipped. Your
block only sets `frameScore`."

**Frames 1 to 4 are right and everything from frame 5 on is wrong.** Frame 5 of
both `g-mixed` and `g-partial` is the first strike. Either the lookahead indexed
into `frameList` instead of `rolls`, or a second index of their own is being
advanced by two on a one-roll frame. `i = i + frame.length` is shipped and
correct. "How wide is a strike frame in the roll list?"

**c-2-2 is red while c-2-1 is green.** The perfect game is satisfied by
`30 * frame`, and `g-mixed` is not satisfied by anything except the real rules.
Read the array against the board - 5, 14, 29, 49, 60, 61, 77, 97, 117, 133 - and
the first number that disagrees names the frame and the rule that is wrong.
Frame 3 wrong is the spare rule; frame 5 wrong is the strike rule.

**A spare scores 10 plus two rolls.** They wrote
`10 + rolls[i + 1] + rolls[i + 2]` in the spare branch. A spare's bonus is one
roll, the one after the pair. `g-mixed`'s column then reads
5, 14, 33, 58, 69, 70, 89, 113, 133, 157 - frame 3 is the first one wrong, and
133 turning up in the wrong cell is a good red herring to point out.

**`error TS2322: Type 'FrameScore' is not assignable to type 'number'.`** In
`gameTotal`: they assigned the last entry of `frameScores` to `total`, and that
entry may be `null`. Walk the array and keep the last non-null instead. "The
type is telling you the truth - the last entry might not be a score."

**`error TS2367` or a warning that a comparison is always false.** They compared
`frameScore` to something after narrowing it, or compared a `number` to `null`
in a branch where it cannot be. Read what the compiler says the type is at that
point; it is usually right and the code is usually redundant rather than wrong.

**`g-gutter` totals 0 and a student thinks that is a bug.** Twenty gutter balls
score zero, and zero is a score. It is also why `gameTotal`'s placeholder is
`-1` and not 0: with 0 as the placeholder, an unwritten block would pass this
case by accident.

**`POST /api/games/score` answers 400 and nobody knows why.** The body.
`{"rolls": "1,2,3"}` is a string; `{"rolls": [1, 4, "seven"]}` has a string in
it; a missing `rolls` key and an unparseable body are the same 400. All of that
is by design, with `{"error": "rolls must be an array of numbers"}`, and nobody
edits that route today.

**`POST /api/games/score` answers 500.** Then the route was edited - the shipped
handler wraps `request.json()` in a `try` precisely so an unparseable body
cannot reach a 500. Restore the file from the skeleton.

## Running the graded suite

**Run it through the pipeline, not by hand.**

```text
python3 -m pipeline test pipeline-test-04 --target skeleton
python3 -m pipeline test pipeline-test-04 --target app
```

It installs, builds, starts the server on a free port, exports `BASE_URL`, runs
pytest with Playwright and writes `skeleton-results.json` / `results.json`.

**`KeyError: 'BASE_URL'`.** pytest was run by hand without the app running. The
suite deliberately boots nothing and picks no port. Use the command above.

**Playwright errors about a missing browser.** The chromium download did not
happen in the venv the runner made. Re-run the command above; it sets the venv
up. If it keeps failing, the failure is in the harness and not in the student's
code - say so rather than debugging their `lib/`.

**A UI test fails with `Locator expected to have count '1'` and
`Actual value: 0`.** The element does not exist at all, which almost always
means the page rendered fewer boxes or cells than the test expects, not that a
text is wrong. Open the page and count.

**Two tests fail and the app looks right in the browser.** Check which tree the
runner used. `--target app` grades the reference build; `--target skeleton`
grades the student tree. They are separate installs and separate
`node_modules`.
