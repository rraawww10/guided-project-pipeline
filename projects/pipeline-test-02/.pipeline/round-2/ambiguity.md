# Ambiguity report - pipeline-test-02

**Verdict:** 1 blocking, 5 worth a look

This spec is unusually tight. I re-derived all three clue tables from the seed,
walked every criterion's arithmetic through the status rule by hand, and checked
each cut's grading signature: all five signatures are distinct (E110 clean), each
criterion's declared `cuts` list is exactly its dependency set in both directions,
and the fully-open skeleton fails all nine cut-bearing criteria while `c-1-5` and
`c-2-4` still pass. I also checked the harness before writing anything up:
`test_runner.PYTEST_DEPS` installs `playwright` and `chromium`, so the four
client-rendered criteria are testable. The findings below are what is left.

## Blocking

### B1 - Whether the check request survives an open `cut-cell-cycle` is not pinned

- **Where:** spec.md, Data model, "Skeleton fallbacks" table; and Session 2 cut
  points, `cut-cell-cycle`
- **Owner:** nothing
- **The line:** "`cut-cell-cycle` | `updated` starts as `grid`, so a click changes
  nothing"
- **Reading one:** `let updated = grid` sits above the marker; the markers hold
  only the cycle assignment; `setGrid(updated)` and the
  `POST /api/puzzles/<id>/check` sit below the closing marker. A student who fills
  the cut exactly as the hint reads gets cycling cells *and* a check on every
  click, so `c-2-5` and `c-2-6` both come alive.
- **Reading two:** the markers hold the cycle assignment *and* the `setGrid` /
  check call, because that is the block of work a click does. `updated` still
  starts as `grid` and a click still "changes nothing", so every stated constraint
  is satisfied - the fallback still fails both criteria that name the cut, the
  function has no `return` to strand, and `app/` is identical either way.
- **Why it matters:** under reading two the hint is insufficient for the criterion
  it grades. The hint says only "Set `updated` to a fresh copy of `grid` in which
  only the cell at row `r` and column `c` moves one step" - it never mentions
  sending a request. A student who writes exactly that gets `c-2-5` green and
  `c-2-6` permanently red, and the whole payoff of session 2 ("watch each clue
  turn green as its line comes right") never fires. Nothing downstream sees the
  difference: `cutter` checks marker balance and placement, not contents;
  `return-safety` has no return to look at; `test-runner` runs against `app/`,
  where the Builder's own code inside the markers sends the POST and everything is
  green; and `skeleton-check` only ever asserts that `c-2-5` and `c-2-6` fail with
  all cuts open, which they do under both readings. The spec already recognised
  exactly this class of defect one paragraph earlier - "The two readings are
  identical in `app/` and different in `skeleton/`, which is the artifact the
  student opens first" - and then left this one open.
- **Suggested wording:** add to the fallback table's preamble: "For
  `cut-cell-cycle` the `setGrid` call and the `POST /api/puzzles/<id>/check` both
  sit below the closing marker, so filling the cut is enough to make a click both
  cycle the cell and send a check."

## Worth a look

### W1 - The "closed" status rule is not total for `clue = []`, which the spec's own skeleton produces

- **Where:** spec.md, Data model, "The status rule, closed."
- **Owner:** nothing
- **The line:** "This is the whole rule and there is no other clause. Read
  `runsOf(cells)` as the blocks of consecutive `filled` cells, in order, and read
  the one-entry list `[0]` - whether it comes from `runsOf` or from a clue - as no
  blocks and a largest block of 0."
- **Reading one:** `clue` is always at least `[0]`, so "the largest number in
  `clue`" is always defined and the rule is total. True of `app/`.
- **Reading two:** `clue` can be `[]`. The spec's own design makes it so: with
  `cut-runs-of` open, `rowClues` derives to `[[],[],...]`, and the spec relies on
  that state at line 309 to explain why `c-2-6` does not name `cut-runs-of`. The
  rule says nothing about the largest number of an empty clue.
- **Why it matters:** a student who has filled `cut-line-status` but not
  `cut-runs-of` is the case. The obvious `Math.max(...clue)` gives `-Infinity`, so
  condition 2 fires on every line and the whole board reads `violated` - a
  confusing intermediate state, though not a crash and not a wrong answer in
  `app/`. No checker sees a partial skeleton, so this ships as written.
- **Suggested wording:** add to the preamble: "A clue with no numbers at all is a
  state only a partly-filled skeleton produces; treat it as no blocks and a
  largest of 0, exactly as `[0]`."

### W2 - Session 2's own minute budget leaves nothing for intro, recap or scaffolding the endpoint

- **Where:** spec.md, Sessions, "The cuts are not equal minutes, so the sessions
  budget them."
- **Owner:** pack-writer
- **The line:** "`cut-line-status` ... gets 16 of the 40 minutes. `cut-cell-cycle`
  ... gets 10. `cut-board-solved` ... gets 8. The remaining 6 are the
  end-of-session run-through."
- **Reading one:** 16 + 10 + 8 + 6 = 40, so session 2 fits.
- **Reading two:** that 40 is entirely cut work plus a run-through. It budgets
  zero minutes for the intro and recap the linter charges 10 for
  (`BASE_MINUTES`), and zero for scaffolding `ep-puzzle-check`
  (`MINUTES_PER_BUILD`). On the linter's own model session 2 comes in at 37, but
  the linter charges 6 per cut where this spec declares 16, 10 and 8 - so the
  spec is describing a heavier session than the model scores, and 34 minutes of
  declared cut work plus a build plus the base is 47 against a 40 cap.
- **Why it matters:** this is the fourth consecutive project in this shape, and
  the lesson on record says the flat per-cut model misses exactly the case where
  one cut is much larger than the others - which is what `cut-line-status` at 16
  minutes is. The spec did the right thing by declaring per-cut weights; the sum
  just does not close. The Pack Writer times it at step 9 against these numbers,
  so it is owned, but it is owned at the most expensive place to fix it.
- **Suggested wording:** state what the 40 covers - e.g. "16 + 10 + 8 for the
  three cuts and 6 for the run-through, with the intro and the `ep-puzzle-check`
  scaffold coming out of the recap of session 1" - or move a cut.

### W3 - "Three boards on screen" contradicts "there is no screen that lists the three puzzles"

- **Where:** spec.md, Session 1, "Runs at the end"; against Out of scope
- **Owner:** pack-writer
- **The line:** "Three boards on screen, each showing correct clues on both
  strips, derived rather than stored, with every cell empty and clickable-looking
  but inert."
- **Reading one:** three boards, reached one at a time by typing `/puzzles/boat`,
  `/puzzles/blanks` and `/puzzles/house` into the address bar. This is the only
  reading the rest of the spec allows.
- **Reading two:** a page showing three boards - which Out of scope forbids: "A
  puzzle index page. There is no screen that lists the three puzzles; a puzzle is
  reached by typing its id into the URL."
- **Why it matters:** the "Runs at the end" line is the demo script the Pack
  Writer turns into the end-of-session walkthrough at step 9. Written from
  reading two it describes a screen that does not exist, and the person reading
  the guide at Gate 3 is the one who finds out.
- **Suggested wording:** "Three boards, one at a time at `/puzzles/boat`,
  `/puzzles/blanks` and `/puzzles/house`, each showing ..."

### W4 - `spec.json` is not self-contained for `c-2-1` and `c-2-6`

- **Where:** spec.json, `c-2-1` and `c-2-6`
- **Owner:** test-runner
- **The line:** "POST /api/puzzles/boat/check with the boat solution as the grid
  returns 200 with solved true" and "one click on each of the 13 cells filled in
  the blanks solution"
- **Reading one:** the Verifier reads spec.md as well, finds the seed block and
  the sentence "The 13 cells are the five of row 1, columns 0 and 4 of row 2,
  columns 1, 2 and 3 of row 3, and columns 0, 2 and 4 of row 4", and writes the
  right fixtures.
- **Reading two:** the Verifier works from spec.json, which CONTRACT.md calls
  "the only file downstream scripts parse". Neither the seed grids nor the 13-cell
  enumeration appear anywhere in spec.json - the enumeration is in spec.md's
  `c-2-6` and is dropped from the JSON `check` string - so the fixture has to be
  guessed.
- **Why it matters:** a wrong grid in either test produces a red criterion the
  Builder cannot fix, because the Builder cannot edit `verify/`. It surfaces at
  step 6 in the Builder/test-runner loop rather than shipping, so it costs
  retries rather than correctness.
- **Suggested wording:** carry the 13-cell enumeration into the spec.json `check`
  string for `c-2-6`, and spell the boat solution out in `c-2-1` as the five row
  strings `..#..`, `.###.`, `#####`, `.#.#.`, `.#.#.`.

### W5 - `c-2-6`'s dependency on `cut-transpose` rests on an assertion the criterion does not require

- **Where:** spec.md and spec.json, Session 2, `c-2-6`
- **Owner:** nothing
- **The line:** "gives each of `row-clue-0` through `row-clue-4` and `col-clue-0`
  through `col-clue-4` `data-status` `satisfied`. Cuts: `cut-cell-cycle`,
  `cut-transpose`, `cut-line-status`, `cut-board-solved`."
- **Reading one:** the test looks up each of `col-clue-0` .. `col-clue-4` by
  testid and asserts its `data-status`. A missing element fails the lookup, so
  `c-2-6` does fail with `cut-transpose` alone open, and the declared dependency
  holds.
- **Reading two:** the test collects the rendered col-clue elements and asserts
  each carries `satisfied`. With `cut-transpose` alone open, `colClues` is `[]`,
  so - by the spec's own rule that a short clue array "renders no element for the
  entries it does not have" - there are zero col-clue elements and the assertion
  passes vacuously. `boardSolved` also goes true in that state, because
  `transpose(grid)` is `[]` and its column loop is vacuously satisfied while every
  row is satisfied, so the `solved-banner` renders too. `c-2-6` goes green with
  `cut-transpose` empty.
- **Why it matters:** under reading two the spec's claim that a criterion's cuts
  list "names every cut that makes the criterion fail while that cut alone is left
  empty" is false for `c-2-6`. This is exactly the partial-subset blind spot in
  `cutter.partial_state_risks` - step 8 only ever sees the fully-open skeleton,
  where `c-2-6` fails on `cut-cell-cycle` anyway, so nothing catches it. It does
  not sink the build: `cut-transpose` is still independently graded by `c-1-2` and
  `c-1-4`, so the student cannot skip it. It just makes one declared dependency
  untrue.
- **Suggested wording:** add a count to the criterion - "renders 5 `col-clue`
  elements, `col-clue-0` through `col-clue-4`, each with `data-status`
  `satisfied`" - so absence cannot pass.
