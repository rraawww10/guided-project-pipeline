# Ambiguity report - pipeline-test-02

**Verdict:** 3 blocking, 4 worth a look

The spec is unusually tight: the seeds and the three clue tables agree cell for
cell (I re-derived all six), the status rule is genuinely closed, every cut has
at least two grading fixtures with an edge case, no two cuts share a criteria
set, and I checked every multi-cut criterion by hand against each proper subset
of its cuts - none of them goes green early. What is left is two grading holes
that no checker downstream can see, one ordering question the test loop will
find, and four smaller things.

## Blocking

### B1 - `boardSolved` passes every criterion while ignoring the columns

- **Where:** spec.md, Session 2, cut-board-solved; criteria c-2-1, c-2-2, c-2-6
- **Owner:** nothing
- **The line:** "Set `solved` to true only when `lineStatus` answers `satisfied`
  for every row of `grid` against the matching entry of `rowClues` and for every
  column of `grid` against the matching entry of `colClues`. Reach the columns
  through `transpose`"
- **Reading one:** both axes, as written.
- **Reading two:** rows only - `rowClues.every((clue, r) => lineStatus(grid[r],
  clue) === "satisfied")`, with the column loop never written.
- **Why it matters:** every criterion that touches `solved` passes under reading
  two. c-2-1 posts the `boat` solution and c-2-6 clicks the `blanks` solution, so
  both axes are satisfied and a rows-only check answers `true` correctly. c-2-2
  posts an all-empty `blanks` board, where the rows are already not all
  satisfied, so a rows-only check answers `false` correctly. c-2-3 asserts
  nothing about `solved`. No criterion posts a grid whose rows are all satisfied
  while a column is not, which is the only shape that separates the two
  readings - and the column half is the whole point of the cut, since it is the
  second place `transpose` earns its keep. A student who writes the rows-only
  version gets 11/11 green and an app that shouts `Solved` at a board that is
  wrong down every column. `skeleton-check` does not see it (the cut still fails
  c-2-1 when it is open), `cutter` and `typecheck` do not see it, and no test
  exists to see it. Same shape as the round-2 `cut-week-dates` lesson: a cut
  graded only by inputs where the wrong implementation happens to agree.
- **Suggested wording:** add to c-2-2, or as a new c-2-7: "`POST
  /api/puzzles/boat/check` with the `boat` solution changed so that row 0 has its
  single filled cell at column 0 instead of column 2 returns 200 with every entry
  of `rows` `satisfied`, `cols[0]` `violated` and `solved` false. Cuts:
  `cut-transpose`, `cut-line-status`, `cut-board-solved`." (Row 0's clue `[1]` is
  still satisfied by one filled cell anywhere; column 0 becomes `[1,1]` against a
  clue of `[1]`.)

### B2 - The clue strips are specified by count, but their data can be shorter

- **Where:** spec.md, Screens, `sc-puzzle`; spec.json `screens[0].elements`
- **Owner:** nothing
- **The line:** "`size` elements with `data-testid="row-clue-<r>"` down the left
  and `size` with `data-testid="col-clue-<c>"` across the top."
- **Reading one:** render the strips by mapping the clue arrays -
  `puzzle.colClues.map((clue, c) => ...)`. In the finished app that is exactly
  `size` elements, so the sentence is satisfied.
- **Reading two:** render exactly `size` elements, as the sentence says -
  `Array.from({ length: puzzle.size }, (_, c) => ...)` - and index
  `puzzle.colClues[c]` for the text.
- **Why it matters:** the two readings are identical in `app/` and different in
  `skeleton/`, which is the artifact the student actually opens. With
  `cut-transpose` open its fallback leaves `out` as `[]`, so `puzzleFor` computes
  `colClues = transpose(...).map(runsOf)` as `[]` and `/api/puzzles` serves
  `colClues: []` for all three puzzles. Under reading one the top strip is simply
  absent until the student writes `transpose` - a good first-hour experience.
  Under reading two `colClues[c]` is `undefined` and `undefined.join(" ")` throws
  on render, so every board route white-screens before the student has written a
  line. That is precisely the failure spec.md says it designed around ("would
  leave session 1's skeleton throwing", Out of scope) and the lesson "Every fetch
  needs an owner" warns about, arriving by a different route. Nothing catches it:
  the skeleton still fails exactly the criteria whose cuts were removed (c-1-4,
  c-2-5 and c-2-6 are all expected red, and c-1-5 runs on `/puzzles/nope` where
  no strip renders, so it stays green), so `skeleton-check` is satisfied;
  `typecheck` sees `number[][]` and no error without
  `noUncheckedIndexedAccess`; `test-runner` only ever runs against `app/`, where
  the arrays are full length. `cut-runs-of` is safe here by luck - it shortens
  the inner arrays, not the outer one, and `[].join(" ")` is `""`.
- **Suggested wording:** in Screens, replace the count with the source: "one
  `row-clue-<r>` element per entry of `rowClues` and one `col-clue-<c>` per entry
  of `colClues`, indexed from 0 - in the finished app that is `size` of each. A
  strip whose clue array is missing an entry renders no element for it and must
  not throw."

### B3 - "the value from the last check response" does not say which response wins

- **Where:** spec.md, Screens, `sc-puzzle`; criterion c-2-6
- **Owner:** test-runner
- **The line:** "Each carries `data-status` set to `satisfied`, `open` or
  `violated` - the value from the last check response, and `open` on every strip
  before the first click."
- **Reading one:** the last response *received* - `const r = await
  fetch(...); setResult(await r.json())` in each click handler, whichever
  settles last.
- **Reading two:** the response to the last click *sent* - stamp each POST with a
  sequence number and drop a response that is not for the newest click.
- **Why it matters:** c-2-6 fires 13 POSTs from 13 clicks. Under reading one, one
  response arriving out of order leaves the strips showing the statuses of an
  earlier, incomplete board and the `solved-banner` absent, so c-2-6 fails - and
  it fails intermittently, which is worse than failing, because it can pass at
  step 6 and go red in the nightly watchdog where no one is holding the retry
  budget. c-2-5 will not surface it: it only reads `data-state`, which the click
  handler sets locally. The Builder has to pick a policy and the spec does not
  name one. It lands in the Builder/test-runner loop at step 6, so it costs
  retries rather than a rebuild.
- **Suggested wording:** "`data-status` shows the response to the most recent
  click; a response that arrives after a later click has already been sent is
  discarded."

## Worth a look

### W1 - `crossed` "grades exactly like `empty`" contradicts the closed rule

- **Where:** spec.md, Out of scope and "What nothing checks", against "The status
  rule, closed" clause 2 and the `cut-line-status` hint
- **Owner:** nothing
- **The line:** "`crossed` is the student's own note that a cell is blank, and it
  grades exactly like `empty`."
- **Reading one:** `crossed` is blank for run-length purposes only. Clause 2's
  third condition means what it says - "no cell in `cells` is still `empty`" is
  `!cells.includes("empty")`, and a `crossed` cell counts as decided, so it does
  not hold the line open.
- **Reading two:** `crossed` grades identically to `empty` everywhere, including
  clause 2, so the third condition becomes `cells.every(c => c === "filled")` and
  effectively never fires on a real board.
- **Why it matters:** the two ship different apps. `boat` row 1, clue `[3]`, with
  cells `filled, filled, crossed, crossed, crossed` reads `violated` under
  reading one and `open` under reading two - a red clue strip versus a neutral
  one, on the most common way a person plays a nonogram. The spec already
  discloses that no criterion posts a grid containing a `crossed` cell, so
  nothing downstream separates them. I am not re-raising that disclosed gap; I am
  flagging that the spec states both readings as fact in different sections. The
  closed rule and the cut hint both say `empty` literally, so a Builder can
  proceed - which is why this is not blocking - but the two prose sentences
  should stop claiming the other thing.
- **Suggested wording:** in Out of scope: "`crossed` is the student's own note
  that a cell is blank; it breaks a run exactly as `empty` does, but unlike
  `empty` it marks the cell as decided, so a line with no `empty` cell left can
  be `violated` (see the status rule, clause 2)."

### W2 - spec.json's `sc-puzzle` entry drops two facts spec.md states

- **Where:** spec.json, `screens[0].elements`, against spec.md Screens
- **Owner:** test-runner
- **The line:** "one element with data-testid puzzle-missing and text Puzzle not
  found, drawn in place of the grid and both clue strips when no puzzle in the
  response has the route id"
- **Reading one:** spec.md's version - `puzzle-missing` replaces "the title, the
  grid and both clue strips", so `puzzle-title` is absent in the not-found state.
- **Reading two:** spec.json's version - only the grid and the strips are
  replaced, so a `puzzle-title` element (empty, or reading the route id) is still
  rendered.
- **Why it matters:** c-1-5 requires that `/puzzles/nope` renders no element with
  `data-testid` `puzzle-title`, so a Builder working from spec.json alone ships
  the losing reading and takes a red test at step 6. The same entry also drops
  "`open` on every strip before the first click", which c-1-4 pins. Both are
  cheap red tests rather than rebuilds, but spec.json is the file the contract
  calls "the only file downstream scripts parse", and the linter is supposed to
  find the two files disagreeing.
- **Suggested wording:** in spec.json, make the element read "...drawn in place
  of the title, the grid and both clue strips...", and append to the two clue
  entries "...and `open` on every strip before the first click".

### W3 - Session 2's three cuts are not three equal cuts

- **Where:** spec.md, Session 2 cut points; idea.md "What the student types"
- **Owner:** pack-writer
- **The line:** "Session 1 carries the project setup - the Next.js app, the
  types, the seed, the list endpoint and the whole screen - so it carries two cut
  points where session 2 carries three."
- **Reading one:** the balance is right - the setup session carries fewer cuts,
  exactly as the tip-split lesson prescribes, and three cuts against 40 minutes
  is comfortable.
- **Reading two:** the count is balanced and the minutes are not.
  `cut-line-status` is a four-branch rule (an ordered equality test, three
  violation conditions and a `[0]` special case whose meaning differs from a
  literal `[0]`) and is the one cut the idea's own Risks section calls arguable;
  `cut-board-solved` needs both axes and a `transpose` call; `cut-cell-cycle` is
  an immutable nested-array update in React, which is its own teaching moment.
  The idea planned three functions for the student to type across both sessions
  (`runsOf`, `transpose`, `lineStatus`); the spec cuts five.
- **Why it matters:** this is the exact shape the habit-tracker lesson names -
  "the model is within ~3 minutes except where one cut is much larger than the
  others, which is precisely the case that overruns" - and the linter's flat
  per-cut cost will estimate session 2 at roughly 18 minutes plus overhead and
  wave it through. Three consecutive projects have overrun. It surfaces when the
  Pack Writer times the session at step 9, after the spec, the code, the tests
  and the skeleton are built.
- **Suggested wording:** either state a per-cut weight in the session prose
  ("`cut-line-status` is the session's large cut, budget 18 of the 40 minutes"),
  or move `cut-cell-cycle` into session 1, where the screen it lives on is
  already being built and c-2-5 would become c-1-6.

### W4 - The `/` redirect exists only in spec.md

- **Where:** spec.md, Out of scope, against spec.json `screens`
- **Owner:** deploy-check
- **The line:** "`app/page.tsx` is a two-line server component that redirects `/`
  to `/puzzles/boat` so the preview link opens on a board."
- **Reading one:** build it, as spec.md says.
- **Reading two:** spec.json declares one screen at `/puzzles/[id]` and no route
  at `/`, and it is the only file downstream scripts parse, so `app/page.tsx` is
  never written and Next.js answers `/` with its own 404.
- **Why it matters:** small, and the spec names its own worst case honestly
  ("its worst case is a preview link that opens on a 404"). Recording it because
  it is a real gap between the two files, and because the person at Gate 3 who
  clicks a 404 has no way to tell a missing redirect from a broken build. The
  step-10 preview is what surfaces it.
- **Suggested wording:** nothing in spec.md needs to change; add the redirect to
  spec.json so the Builder's parsed contract carries it - either as a second
  screen entry with `"states": []`, or as a sentence appended to the `sc-puzzle`
  entry: "`/` is a server-component redirect to `/puzzles/boat`; it is not a
  graded screen."
