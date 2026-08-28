# Ambiguity report - pipeline-test-01

**Verdict:** 2 blocking, 6 worth a look

Read against spec hash `64074255c3f7`, `lint.json` clean at 0 errors / 0 warnings.

This is an unusually tight spec. I recomputed all three `counts` arrays from the
mine lists, both ASCII drawings against them, every `revealFrom` result, every
`revealed` count and every status in all 18 criteria: **every number in the spec
is correct**, the two files agree, and nothing has drifted from the idea that the
spec does not name and justify (the third `gameStatus` parameter, `GET /api/boards`
moving to session 3, `/boards/[id]` becoming the play route). The linter's minute
estimates in the prose - 38.5, 32.5, 35.5 - are exactly what `spec_linter.py`
produces. The harness claims check out too: `code_check.py` really does run over
`app/` at step 6 and really does flag `new Date()` and `Date.now()`, and the test
runner really does install chromium, so the eight DOM criteria have a driver.

So the findings below are all about the seams, not the arithmetic.

## Blocking

### A1 - The given face-down grid never says what it iterates, and `c-2-4` must pass on the skeleton

- **Where:** spec.md, Session 2 "Cut points" (the paragraph after `cut-play-click`), and `c-2-4`, which declares `"cuts": []`
- **Owner:** skeleton-check
- **The line:** "One `data-testid="cell"` element per index, in index order, each carrying `data-index`, `data-revealed`, `data-flagged` and an `onClick` that calls `onCellClick` with its index, plus the cell text rule from the Screens section, is written live in `app/boards/[id]/page.tsx` and is not a cut point"
- **Reading one:** the grid iterates the index range `0 .. board.width * board.height - 1` and looks `counts[i]` up only for the text of an open cell.
- **Reading two:** the grid iterates the `counts` array it got from `GET /api/boards/[id]` - `counts.map((count, i) => ...)` - which is the natural shape, because the cell text rule needs `count` per cell and `counts` is declared to have exactly `width * height` entries. `cut-solved-cells`' hint ("one element per index of `board`") pushes the same way, and `Board` has no array to iterate but `mines`.
- **Why it matters:** the two readings are identical in the finished app and differ on the skeleton. `cutter.expected_skeleton_results` requires every criterion with an empty `cuts` list to **pass** on the fully-cut skeleton. There `cut-neighbour-counts` is empty, so `neighbourCounts` returns `[]`, `ep-board-get` answers `counts: []`, and reading two renders **0 cells** on `/boards/field`. `c-2-4` asks for 64, and step 8 fails with `expected: pass, actual: fail` on a criterion the spec has deliberately built to be green from day one. The same choice is invisible on `sc-solved`, because `c-1-4` and `c-1-5` name both cuts and are expected red anyway - which is exactly why nobody would look at the play grid.
- **Suggested wording:** in the Screens section, add that both grids render one cell per index of the range `0 .. width * height - 1` taken from `board.width` and `board.height`, never from the length of `counts`, so the number of cells on the page does not depend on `cut-neighbour-counts`.

### A2 - "updates data-revealed to true on exactly N cells" is a running total in some clauses and reads as a delta

- **Where:** spec.md and spec.json, `c-2-6` (second clause) and `c-3-6` (third clause); the same phrasing is used with no ambiguity in `c-2-5` and `c-3-5`
- **Owner:** test-runner
- **The line:** "a following click on the cell with data-index 20 updates data-revealed to true on exactly 7 cells" (`c-2-6`), and "a following click on the cell with data-index 3 updates data-revealed to true on exactly 2 cells" (`c-3-6`)
- **Reading one:** after the click, the number of cells on the page carrying `data-revealed="true"` is 7 (respectively 2). This is the reading the board data supports: `revealFrom(intro, 20)` opens `{15,16,17,20,21,22}`, which added to the already-open `{3}` gives 7 in total.
- **Reading two:** the click flips exactly 7 (respectively 2) cells from false to true. The real deltas are 6 and 1, so a suite written this way is red against a correct implementation.
- **Why it matters:** the spec switches verbs mid-criterion - `c-2-6`'s third clause says "**leaves** data-revealed true on exactly 7 cells" for a total - which invites reading "updates ... on exactly N" as the other thing. `c-3-6` has no third clause to disambiguate it. A Verifier that pins the delta writes an assertion no correct build can satisfy, and this is the one flavour of step-6 failure the Builder/test-runner loop does *not* fix for free: `guard.py` forbids the Builder touching `verify/`, so the loop burns retries against `state.py`'s cap of 15 and ends in a ticket. It surfaces at step 6 in `results.json`, so it is caught - it is just not cheap.
- **Suggested wording:** use one verb for the whole spec - "leaves exactly N cells carrying `data-revealed` true" - and state once in the Screens section that every cell count in a criterion is the total on the page after the step, never the number that changed.

## Worth a look

### B1 - Every session is budgeted to exactly 40:00, and session 2 puts 20 of them in one cut

- **Where:** spec.md, the three "Minutes." paragraphs
- **Owner:** pack-writer
- **The line:** "20 for `cut-reveal-from` ... `cut-reveal-from` is the one block in the project that needs a third of its session, and the number is written here so the Pack Writer inherits it instead of discovering it at step 9. The linter's estimate for the session is 32.5."
- **Reading one:** the spec has pre-empted the timing risk by declaring the number early, so the Pack Writer plans around it.
- **Reading two:** the three guide budgets sum to 40.0, 40.0 and 40.0 - zero slack in any of them - and the linter's model charges a flat 6 minutes per cut, so its 32.5 for session 2 understates the spec's own budget for `cut-reveal-from` by 14 minutes.
- **Why it matters:** `learning/lessons.md` records that the flat per-cut model "is within ~3 minutes *except* where one cut is much larger than the others, which is precisely the case that overruns", and that habit-tracker's session 3 measured 47 against an estimate of 35.5. This spec has that exact shape, plus session 1 giving 10 minutes to a Next project, four types, three seeded boards, `findBoard` and a route handler. Nothing before step 9 measures it, and the two earlier overruns found there were shipped rather than fixed, because the fix is a Gate 1 rebalance.
- **Suggested wording:** none needed in the spec; this is a note for the person at Gate 1 - if session 2 is going to overrun, moving `cut-play-click` to session 3 (which has slack in reality, see B3) is cheaper now than at step 9.

### B2 - Nothing says who writes the `flag-mode` button's own click handler

- **Where:** spec.md, Screens `sc-play`; Session 2 "The face-down grid itself is handed over complete"; `cut-flag-toggle`
- **Owner:** test-runner
- **The line:** "a button with `data-testid="flag-mode"` whose text is `Flag mode: off` or `Flag mode: on`. It starts off"
- **Reading one:** the button and the `flagMode` state toggle are both given code, present from session 2 - which is what `c-2-4` (no cuts, reads the starting text) forces for the element and what `cut-flag-toggle`'s hint ("this block is the flag branch of `onCellClick`") forces for the scope of the cut.
- **Reading two:** the toggle is session-3 work and belongs inside `cut-flag-toggle`, since that is the only session-3 cut in that file that is about flag mode at all.
- **Why it matters:** under reading two the marker swallows code the hint never describes, and no checker sees it - `c-3-5` is still red on the skeleton either way, so skeleton-check is happy, and step 6 runs against the complete app. The likelier failure is simpler: the button is listed as an element in three places and as behaviour in none, so it is easy to ship a button whose label never changes, which `c-3-5`'s first assertion catches at step 6. A second-order effect worth a line in the guide: on the session-2 skeleton the button already toggles its label while both branches of `onCellClick` are empty, so a student who turns flag mode on gets a completely dead board and blames their `cut-play-click`.
- **Suggested wording:** add to the Screens section that the button's own `onClick` flips the `flagMode` state and is handed over with the grid in session 2, and that only the two branches of `onCellClick` are cut.

### B3 - `cut-game-status`' hint is the implementation, line for line, for 12 of session 3's 40 minutes

- **Where:** spec.md and spec.json, Session 3 cut point `cut-game-status`
- **Owner:** pack-writer
- **The line:** "Set `status` to `lost` when any index in `revealed` is also in `board.mines`. Otherwise set `status` to `won` when the number of distinct indices in `revealed` equals `board.width * board.height` minus the number of entries in `board.mines`, and to `playing` in every other case. Test the mine case first"
- **Reading one:** the hint states the goal precisely, as it must, because `c-3-3`'s third case grades the branch order and an unstated ordering would be a guess.
- **Reading two:** three sentences map one-to-one onto three lines of code, including the branch order, so the block is transcription. The reasoning the criterion is built to provoke - noticing that the win threshold counts a revealed mine too - is done for the student in the hint's last sentence.
- **Why it matters:** it is the session's headline cut at 12 minutes against `cut-flag-toggle`'s 7, and if it takes 3, session 3's budget is wrong in the other direction from B1. Compare `cut-reveal-from`, which states the rule and leaves the walk to the student.
- **Suggested wording:** keep the rule and drop the ordering instruction, leaving the consequence: "a list that opens the last safe cell and a mine together must read `lost`" already appears in the hint and is enough to force the order.

### B4 - "every cell bordering that region" never says which adjacency

- **Where:** spec.md, Library modules (`lib/reveal.ts`) and the `cut-reveal-from` hint
- **Owner:** test-runner
- **The line:** "a cell whose count is 0 opens itself, every zero-count cell reachable from it through the 8 neighbour offsets, and every cell bordering that region"
- **Reading one:** the fringe is 8-way, like the reachability rule in the same sentence.
- **Reading two:** the sentence names the 8 offsets for reachability and then switches to the undefined word "bordering" for the fringe, which reads as orthogonal.
- **Why it matters:** on `field` from index 0 the two answers are 14 cells and 13 - the difference is index 14, which is diagonal from the zero at index 5 and orthogonal to nothing in the region. `c-2-1` lists all 14 indices, so a Builder that picks 4-way is red at step 6 and fixed in the loop. The student is graded on the same wording with the same criterion, which is the intended lesson - but the hint should not be the place they discover the word is loose.
- **Suggested wording:** "...and every cell that is one of the 8 neighbours of any cell in that region".

### B5 - The "no cut in any list is redundant" claim does not hold for `c-3-4` and `c-3-5`

- **Where:** spec.md, "Cut dependencies and the one skeleton"
- **Owner:** nothing
- **The line:** "A criterion's `cuts` list is its full dependency set: it names every cut that makes the criterion fail while that cut alone is left empty, whichever session declared it. So a session-3 criterion names the session-1 and session-2 cuts its request passes through, and no cut in any list is redundant."
- **Reading one:** each named cut, left empty on its own, turns that criterion red.
- **Reading two:** for `c-3-4` (`clicks: [6]` on `corner`) and `c-3-5`'s tail (a click on cell 6), `cut-neighbour-counts` alone-empty leaves `counts` as `[]`, so `counts[6]` is `undefined`. A `revealFrom` written as "expand only while `counts[c] === 0`" then opens `{6}` and both criteria pass with session 1's cut still empty; one written as "stop expanding when `counts[c] > 0`" floods and they fail. The claim rests on which way the Builder phrases a comparison against `undefined`.
- **Why it matters:** honestly, not much, and I checked the direction that would matter. `learning/lessons.md` asks for a hand check that no proper subset of a criterion's cuts satisfies it; I ran it over all eleven multi-cut criteria and **no cut in this spec can be left empty with all of its own criteria green** - `cut-neighbour-counts` is pinned hard by `c-1-1`, and every other cut has a criterion that cannot be reached around it. `skeleton-check` only ever sees the all-open skeleton, so a redundant entry in a `cuts` list costs nothing there. What it costs is a session guide that tells a student a dependency that may not exist.
- **Suggested wording:** soften to "names every cut its request passes through", and drop the claim that each one alone makes the criterion fail.

### B6 - "eight more in sessions 2 and 3" is nine

- **Where:** spec.md, end of Session 1 "Cut points"
- **Owner:** nothing
- **The line:** "`cut-neighbour-counts` is named by `c-1-1`, `c-1-2`, `c-1-4` and `c-1-5` and by eight more in sessions 2 and 3"
- **Reading one:** a count of the criteria naming that cut.
- **Reading two:** spec.json names it in `c-2-1`, `c-2-2`, `c-2-5`, `c-2-6`, `c-3-2`, `c-3-3`, `c-3-4`, `c-3-5` and `c-3-6` - nine, not eight.
- **Why it matters:** only that it is the one place the prose and `spec.json` disagree on a fact, and the sentence exists to argue that the cut is not redundant - an argument the Pack Writer may repeat verbatim in the session 1 guide.
- **Suggested wording:** "and by nine more in sessions 2 and 3".
