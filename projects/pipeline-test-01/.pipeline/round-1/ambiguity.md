# Ambiguity report - pipeline-test-01

**Verdict:** 2 blocking, 4 worth a look

Spec hash read: `58a12371e56eac62d50f3fa84b47efbe36f3e3ebd26d66d3f7a8167822a5fc36`
(matches `.pipeline/breaker-begin.json` and `lint.json`).

Before the findings, what held. I recomputed all three boards' `counts` arrays
cell by cell, and ran the flood fill by hand for every click any criterion
makes. Every number in this spec is correct: the 25 `intro` counts, the 16
`corner` counts, all 64 `field` counts, the 8 index/value pairs in `c-1-2`
(including the two zero-count mines at 15 and 63), the 14-cell fill from
`field` index 0, the 6-cell fill from `intro` index 20, the 13-cell fill from
`corner` index 0 and its `won`, and the 2/1/2 counter walk in `c-3-5`. I also
checked the partial-subset hole from `lessons.md`: for each of the eight
multi-cut criteria, no proper subset of its cuts turns it green. E110 is clean -
no two cuts share a criteria set. Every cut sits below its fallback, so no
typed function's only `return` is inside markers. The harness claims check out:
`test_runner.py:243` sets `BASE_URL`, and this project needs nothing else. The
findings below are about rules the spec states and never grades, and about
session 2's minutes - not about arithmetic.

## Blocking

### B1 - Five behaviours the spec decides explicitly and no criterion grades

- **Where:** spec.md "Library modules", "Endpoints", "Screens"; spec.json
  `c-2-3`, `c-3-3`, `c-3-5`
- **Owner:** nothing
- **The line:** "`lost` is tested first, so opening the last safe cell and a
  mine in the same list reads `lost`." - and four siblings in the same shape:
  "`Mines left: ` followed by the number of mines minus the number of flags,
  **which may go below 0**"; "An empty `clicks` array is valid and answers 200
  with an empty `revealed`"; "`ep-board-replay` resolves the board id first, so
  an unknown board answers 404 **even when the body is malformed**"; and
  "`flagged` (the submitted `flags` sorted ascending with duplicates dropped)".
- **Reading one:** the implementation follows each stated rule.
- **Reading two:** the implementation does the opposite of each, and every one
  of the 18 criteria still passes. I checked each:
  - **Order of `lost` vs `won`.** Test `won` first and all four
    `cut-game-status` criteria stay green. `c-3-3`'s `corner [0, 15]` reveals 14
    cells against a 13-cell win threshold, so the `won` branch never fires and
    both orders answer `lost`. `c-3-6`'s `intro` click on 9 reveals 1 against a
    threshold of 21 - same. No criterion ever puts a mine in `revealed` at
    exactly `width * height - mines.length` entries, which is the only input
    where the two orders differ. This is the session-3 headline cut, graded on a
    rule it never exercises.
  - **`minesLeft` below 0.** `c-3-5` walks 3 -> 2 -> 1 -> 2 on a 3-mine board
    and never plants a fourth flag, so `Math.max(0, ...)` is green.
  - **Empty `clicks`.** `c-2-3` tests `{}`, `{"clicks": "0"}` and
    `{"clicks": [25]}` - all 400. It never posts `{"clicks": []}`, so a handler
    that 400s on an empty array is green while the spec says 200.
  - **404 before 400.** `c-2-3` posts to `no-such-board` with the *valid* body
    `{"clicks": [0]}`. A handler that validates the body before resolving the id
    is green there and returns 400 where the spec demands 404.
  - **`flagged` deduped and defaulted.** `c-3-4`'s flags are already distinct
    and ascending; no criterion posts a duplicate flag or asserts
    `flagged: []` on an absent `flags`.
- **Why it matters:** these are not gaps a builder has to guess at - the spec is
  clear. They are rules with no grading surface, which is worse, because they
  ship. A student fills `cut-game-status` with the branches in the wrong order
  and the pipeline says 18/18. `skeleton-check` only proves the cut fails when
  empty; `test-runner` only runs what a criterion asks for; no `code_checks`
  entry sees any of this. Nothing downstream looks. Two of the five (`404`
  before `400`, empty `clicks`) sit in `c-2-3`, which has an empty `cuts` list,
  so fixing them costs no cut-dependency rework at all.
- **Suggested wording:** extend the existing criteria rather than adding new
  ones. In `c-2-3`, add "and POST /api/boards/no-such-board/replay with body
  `{"bogus": 1}` returns 404, and POST /api/boards/intro/replay with body
  `{"clicks": []}` returns 200 with an empty revealed array and an empty flagged
  array". In `c-3-3`, add a third case on `intro` whose clicks open 20 non-mine
  cells plus the mine at index 9 - 21 revealed entries against a 21-cell win
  threshold - and require `lost`. In `c-3-5`, add a fourth flag click and
  require the text `Mines left: -1`.

### B2 - Session 2 has 1.5 minutes of headroom and carries the one heavy cut

- **Where:** spec.md "Session 2 - Reveal and flood fill"; `lint.json`
  `session_minutes[1].minutes = 38.5`
- **Owner:** pack-writer
- **The line:** "**Teaches.** A breadth-first walk over a grid with an explicit
  queue and a visited set; the boundary rule that a numbered cell is opened but
  never walked out of; merging a returned index set into React state without
  duplicates."
- **Reading one:** three cuts at the linter's flat 6 minutes each fits inside
  40, as `lint.json` says at 38.5.
- **Reading two:** `cut-reveal-from` is a queue, a visited set, an eight-offset
  expansion and a fringe rule that is the single hardest thing in the project,
  and it is charged the same 6 minutes as `cut-play-click`, which is one array
  union. `lessons.md` records that the flat-per-cut model "is within ~3 minutes
  *except* where one cut is much larger than the others, which is precisely the
  case that overruns", and that habit-tracker's session 3 was estimated at 35.5
  and timed at 47. This session is estimated at 38.5. The idea file names the
  same risk in its own words: "Session 2 is the whole project's weight in one
  function."
- **Why it matters:** the overrun is not discovered until the Pack Writer times
  the guide at step 9 - after the spec, the app, the suite and the skeleton are
  all built and Gates 1 and 2 are passed. Three consecutive projects have
  overrun this way. The estimate is information, not a check, so the balancing
  has to happen here.
- **Suggested wording:** hand `cut-play-cells` over as given code and drop it
  from `c-2-4`, `c-2-5`, `c-2-6`, `c-3-5` and `c-3-6`, leaving session 2 with
  `cut-reveal-from` and `cut-play-click`. It is the cheapest cut to give away:
  its map-over-indices JSX repeats `cut-solved-cells` from session 1, its
  genuinely new content is three attributes and an `onClick`, and `c-2-4` - the
  only criterion that grades it alone - would then join `c-1-3`, `c-1-6`,
  `c-2-3` and `c-3-1` as a green-from-the-start criterion over handed-over code.
  If the cut stays, say in the session-2 section that its guide must budget
  `cut-reveal-from` at 20 minutes and the other two at 5 each, so the Pack
  Writer inherits the number instead of discovering it.

## Worth a look

### W1 - "A flagged cell can never be open" is false in both directions

- **Where:** spec.md "Screens", `sc-play` cell text rule
- **Owner:** nothing
- **The line:** "A flagged cell can never be open, because the flag branch never
  opens anything."
- **Reading one:** the invariant holds and the builder need not think about the
  overlap.
- **Reading two:** the invariant does not hold, in two ways the cut hints
  create. `cut-play-click`'s hint says only "Set the `revealed` state to a new
  array holding every index already in `revealed` together with every index in
  `revealFrom(board, index)`" - no guard - so a left click with flag mode off
  opens a flagged cell. `cut-flag-toggle`'s hint says only "`flagged` with
  `index` added when it is absent and dropped when it is already present" - no
  guard - so a click in flag mode flags an already-open cell and decrements
  `Mines left:` for it.
- **Why it matters:** not much, which is why it is here and not above. The cut
  hints and the replay fold together determine the behaviour unambiguously (no
  guard either way), so the builder is not guessing; the defect is one prose
  sentence that asserts an invariant the rest of the spec does not maintain. No
  criterion drives a reveal click after a flag, so `test-runner` never sees it,
  and the Pack Writer would only catch it by repeating the sentence in a guide.
  Worst case is a shipped game where a flag does not protect a cell and the
  counter can drift.
- **Suggested wording:** either delete the sentence, or add to `cut-play-click`'s
  hint "a click on a cell that is already in `flagged` changes nothing" and to
  `cut-flag-toggle`'s hint "a click on a cell that is already in `revealed`
  changes nothing" - and then grade one of them inside `c-3-5`.

### W2 - `code_checks` is empty while the spec states a code-shape constraint

- **Where:** spec.json `"code_checks": []`; spec.md "Out of scope"
- **Owner:** nothing
- **The line:** "Difficulty selection, timers, best scores, or anything that
  measures elapsed time. Nothing in the app reads the clock."
- **Reading one:** it is an out-of-scope note, and no builder would reach for
  the clock in a game with no timer.
- **Reading two:** it is a constraint on the shape of the code, and
  `pipeline/code_check.py`'s `utc-dates` check already owns exactly this half of
  it - `RE_CLOCK` at line 53 matches `new Date()` and `Date.now()`. Declared, it
  would run at step 6 against `app/` and land any violation in the
  Builder/test-runner loop. Undeclared, `code_checks: []` runs nothing and the
  sentence has no owner at all.
- **Why it matters:** low risk here - nothing in the 18 criteria wants a clock,
  and the sibling constraint ("Nothing is random") is fully owned by
  `test-runner`, since a random board fails `c-1-1` on its first assertion. But
  `lessons.md` is explicit: "Before writing `nothing`, ask whether the rule is
  about the *shape* of the code." This one is, and the check exists.
- **Suggested wording:** set `"code_checks": ["utc-dates"]` in spec.json and add
  one sentence to the Out of scope bullet saying the named check enforces it at
  step 6.

### W3 - The not-found state does not say which of the play screen's chrome renders

- **Where:** spec.md "Screens", `sc-play`; spec.json `sc-play.states`
- **Owner:** test-runner
- **The line:** "`data-testid="board-missing"` with the text `Board not found`,
  drawn in place of the grid when `GET /api/boards/[id]` answers 404, with 0
  cells on the page"
- **Reading one:** "in place of the grid" means only the grid is replaced, so
  `flag-mode`, `mines-left` and `game-status` still render - and then
  `mines-left`, which the spec defines as "the number of mines minus the number
  of flags", has no board to read `mines.length` from.
- **Reading two:** the component returns early and renders `board-missing`
  alone, so those three testids are absent in the not-found state.
- **Why it matters:** `c-2-4` asserts only the `board-missing` text and 0 cells,
  so either reading is green - unless the builder takes reading one and
  dereferences a null board, in which case the page throws, `board-missing`
  never renders and `c-2-4` goes red at step 6. That makes it a retry the
  Builder loop pays for once, not a shipped defect, so it stays here.
- **Suggested wording:** add to the `sc-play` not-found bullet: "in the
  not-found state the page renders `board-missing` and nothing else - no grid,
  no `flag-mode`, no `mines-left` and no `game-status`."

### W4 - The rationale paragraph misdescribes the criterion it is defending

- **Where:** spec.md, Session 1, "Cut points", closing paragraph
- **Owner:** nothing
- **The line:** "`c-1-2` reads all four corners of the 8x8 (indices 0, 7, 56 and
  63) plus two edge cells, which is where a missing bounds test wraps a row or
  reads off the end."
- **Reading one:** `c-1-2` reads six indices.
- **Reading two:** `c-1-2` reads eight - 0, 7, 8, 15, 54, 56, 57 and 63. Beyond
  the four corners that is four more, not two, and one of them is not an edge
  cell: index 54 is row 6, column 6, fully interior. Indices 8, 15 and 57 are
  edge cells.
- **Why it matters:** nothing downstream reads a rationale paragraph, and the
  criterion itself is correct and well chosen - index 54 is in fact the best
  pick in the list, because it is the only 3 in the array and it sits next to
  three mines. But this paragraph is the argument a gate reader uses to accept
  that `cut-neighbour-counts` cannot be faked, and `lessons.md` has two entries
  about prose overclaims being trusted. Correcting it costs four words.
- **Suggested wording:** "`c-1-2` reads all four corners of the 8x8 (indices 0,
  7, 56 and 63), three edge cells (8, 15 and 57) and the interior cell 54, whose
  count of 3 is the highest on the board."
