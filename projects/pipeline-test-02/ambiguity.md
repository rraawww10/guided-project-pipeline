# Ambiguity report - pipeline-test-02

**Verdict:** 0 blocking, 7 worth a look

Nothing in this spec forces a builder to guess about behaviour a criterion
grades. That is an unusual result, so here is what I actually checked rather
than read past:

- Re-derived all 60 clue numbers in the table at spec.md:115-119 from the seed
  strings at spec.md:93-103, by hand, both axes, all three puzzles. Every entry
  matches.
- Re-evaluated the closed status rule (spec.md:142-168) against every literal
  every criterion pins: c-2-1 both requests, c-2-2 all three, c-2-3, c-2-6's
  13-click end state. All 30-odd asserted statuses come out as written.
- Checked the dependency claim at spec.md:342 ("names every cut that makes the
  criterion fail while that cut alone is left empty, and no cut that does not")
  in **both** directions for all 11 criteria. It holds in both. In particular
  c-2-6's omission of `cut-runs-of` and c-2-1's inclusion of it are both
  correct, and no proper subset of any criterion's cut set satisfies it - the
  hand-check `learning/lessons.md` asks for, because `cutter.py` only proves the
  all-open and no-cut cases.
- Checked the step-8 skeleton-check contract: c-1-5 and c-2-4 (the two
  no-cut criteria) both still pass with all five cuts open, and the other nine
  all fail. `puzzleFor` takes `size` from the seed string length, not from
  `runsOf`, which is what keeps c-2-4's 400 cases alive in the skeleton.
- Reproduced `spec_linter.session_minutes` by hand: session 1 = 10 + 12 + 6 + 6
  + 6 = 40.0, session 2 = 10 + 18 + 3 + 6 = 37.0. The spec's claim at
  spec.md:335 is exact. E113 (setup session must carry strictly fewer cuts)
  passes at 2 < 3. E110 passes - all five cuts have distinct criterion sets.
- Checked the two harness capabilities the spec asserts. `.cut-manifest.json`
  with a `by_session` map is real (`pipeline/cutter.py:254`), and the cutter
  cuts one skeleton over the whole app tree, so spec.md:360 is accurate. The
  cutter never validates a cut's declared `file` against where the marker is
  found, so the `lib/nonogram.ts` vs `app/lib/nonogram.ts` path convention at
  spec.md:66-71 costs nothing downstream either way.
- Checked the five fallbacks against `return-safety` and `typecheck`: every cut
  holds an assignment to a variable declared above it, every function's only
  `return` is outside the markers, and every fallback is typeable
  (`number[]`, `T[][]`, `LineStatus`, `boolean`, `Cell[][]`). No hint trips
  `RE_HINT_RETURN`, so no W067.

The seven findings below are all cases where nothing downstream is watching, but
none of them changes what a criterion grades.

## Blocking

None.

## Worth a look

### W1 - What a clue strip shows between a click and its response
- **Where:** spec.md, Screens, `sc-puzzle`, the `data-status` bullet; spec.json `screens[0].elements[6]`
- **Owner:** nothing
- **The line:** "The value shown is the one from the response to the most recent click: a response that arrives after a later click has already been sent is discarded, so an out-of-order response never overwrites a newer one."
- **Reading one:** each clue keeps the `data-status` it is already showing until a response is applied, so nothing changes on click, only on response.
- **Reading two:** the click clears the strips to `open` and the response repaints them, because until the response lands there *is* no "response to the most recent click" and `open` is the declared default.
- **Why it matters:** the rule is written over a window it does not cover. No criterion observes the in-flight window - c-1-4 reads the strips before any click, c-2-6 reads them after the last response - so both ship. Under reading two every line the student has already turned green blinks back to `open` on every later click anywhere on the board, which is the exact opposite of "a line turns green the moment it is right" in the Outcome. It also decides whether c-2-6 is stable or flaky if the Verifier writes its assertion without a wait.
- **Suggested wording:** "Between a click and the arrival of its response, every clue keeps the `data-status` it was already showing. A clue's `data-status` changes only when a response is applied."

### W2 - The out-of-order rule is required and ungraded, and the "What nothing checks" section does not say so
- **Where:** spec.md, Screens, the `data-status` bullet, against spec.md:229-237
- **Owner:** nothing
- **The line:** "a response that arrives after a later click has already been sent is discarded, so an out-of-order response never overwrites a newer one"
- **Reading one:** the Builder tracks a request sequence number (or aborts the previous request) and this is real shipped behaviour.
- **Reading two:** the Builder writes the obvious `await fetch(...); setStatuses(...)` and never implements the guard, because on localhost responses come back in order and every criterion is green.
- **Why it matters:** no criterion sends two overlapping requests. c-2-6 fires 13 POSTs but only asserts the settled state, so it cannot tell the two apart. That is fine as a decision, but the spec has a "What nothing checks" section that lists exactly one constraint and claims that one has an owner - so a Gate 1 reader finishes the spec believing every unowned constraint has been surfaced, and this one has not. Same shape as the c-2-6/`cut-runs-of` note that *is* written down.
- **Suggested wording:** add a second bullet under "What nothing checks": "*The discard of an out-of-order check response.* No criterion sends two overlapping requests, so a Builder that omits the sequence guard is green on all eleven. Owner: nothing."

### W3 - `board-loading` and the text of `puzzle-title` are declared and never graded
- **Where:** spec.md, Screens, `sc-puzzle` bullets 1 and 3; spec.json `screens[0].elements[0]` and `[2]`, `states: ["loading", ...]`
- **Owner:** nothing
- **The line:** "`data-testid=\"board-loading\"`, text `Loading`, drawn until the `GET /api/puzzles` response arrives and never after it" and "`data-testid=\"puzzle-title\"`, carrying the puzzle title"
- **Reading one:** the Builder ships both exactly as written.
- **Reading two:** the Builder renders nothing while loading and puts the route `id` in the title element instead of `puzzle.title`, and all eleven criteria stay green. c-1-5 is the only criterion that names `puzzle-title` and it asserts its *absence*; nothing names `board-loading` at all.
- **Why it matters:** the spec is careful elsewhere to say why an ungraded thing is ungraded - c-1-5 exists specifically "so the `not-found` state the screen declares is graded", and the `/` redirect gets a paragraph explaining that its worst case is a preview 404. `loading` gets the same declaration in spec.json with none of that reasoning, and `Boat`/`Blanks`/`House` are graded on the wire by c-1-1 but never on the page. The linter's E033 only requires that states be *listed*.
- **Suggested wording:** extend c-1-4 with "renders `puzzle-title` with text `Blanks` and renders no `board-loading` element", which costs no new cut dependency - both are Builder-shipped and outside every marker.

### W4 - "no other key" is stricter than the criterion that grades it
- **Where:** spec.md, Endpoints, `ep-puzzles-list`; against c-1-1
- **Owner:** nothing
- **The line:** "each with `id`, `title`, `size`, `rowClues` and `colClues` and no other key. The solution is not in the response, which is what stops the board grading itself in the browser."
- **Reading one:** the response objects have exactly those five keys.
- **Reading two:** the response has those five keys and whatever else is convenient, because the only criterion that grades it - c-1-1 - asserts only that "no entry carries a `solution` key".
- **Why it matters:** the prose is unambiguous, so the Builder does not have to guess; the grading is what is loose. A Builder that spreads the derived puzzle and leaves `rows`, `cells` or `answer` on it passes c-1-1 and hands the browser the solution, which defeats the one security property the paragraph names. This is also the property the whole derived-not-stored design exists to protect.
- **Suggested wording:** in c-1-1, replace "no entry carries a `solution` key" with "each entry's key set is exactly `id`, `title`, `size`, `rowClues`, `colClues`".

### W5 - Session 2 is budgeted to exactly 40 with no slack, and it carries the project's largest cut
- **Where:** spec.md, Sessions, the session 2 budget
- **Owner:** pack-writer
- **The line:** "Session 2, 40 minutes: 4 for the intro and the recap of `runsOf` and `transpose`; 3 walking the `POST /api/puzzles/[id]/check` route the Builder ships whole; 14 on `cut-line-status`, the large one ...; 9 on `cut-cell-cycle` ...; 6 on `cut-board-solved` ...; 4 for the end-of-session run-through."
- **Reading one:** 14 minutes is enough for a four-branch rule with three ordered violation conditions plus the `[0]`/`[]` convention, and the session lands on 40.
- **Reading two:** it is not, and the session lands at 45-46 like the last three projects did.
- **Why it matters:** `learning/lessons.md` records three consecutive overruns and each one was the session holding a single oversized cut. habit-tracker's `cut-api-toggle` - a comparable multi-branch rule with an ordering constraint - was estimated at 6 and measured near 20. `cut-line-status` is strictly harder: the student must get `[0]`, `[]`, the three violation conditions and their order all right, and every one of c-2-1, c-2-2, c-2-3 and c-2-6 goes red if any of them is wrong. The spec does declare per-cut weight, which is the fix the lesson asked for, so this is a judgement call rather than a defect - but nothing measures it before step 9, and the budget has zero slack.
- **Suggested wording:** name the drop candidate in the same paragraph: "if `cut-line-status` runs past 14, `cut-board-solved` is walked rather than typed - it is two `every` loops over a function the student has already written." Do not move a cut into session 1 to fix this: session 1 would then carry 3 cuts plus the setup against session 2's 2, which is spec_linter E113.

### W6 - spec.json drops the grid's orientation
- **Where:** spec.json `screens[0].elements[3]`, against spec.md, Screens, the cell bullet
- **Owner:** test-runner
- **The line:** spec.md says "`size` x `size` button elements with `data-testid=\"cell-<r>-<c>\"`, `r` and `c` counted from 0 **with row 0 at the top and column 0 at the left**"; spec.json says only "with data-testid cell-<r>-<c>, r and c counted from 0".
- **Reading one:** `r` is the row index, matching spec.md.
- **Reading two:** the Verifier, writing fixtures from spec.json alone as c-2-6 explicitly invites ("so the Verifier can write the fixture from spec.json alone"), has to infer the orientation from c-2-6's "columns 0 and 4 of row 2" and c-1-4's `col-clue-2` text.
- **Why it matters:** it is recoverable - a transposed rendering fails c-1-4's `col-clue-2` text `1 2` and fails c-2-6's solve, because `blanks` is not its own transpose - so the worst case is one red test at step 6. But c-2-6 is the criterion the spec singles out as writable from spec.json alone, and this is the one fact it needs that spec.json does not carry.
- **Suggested wording:** append "row 0 at the top and column 0 at the left" to the cell element string in spec.json, matching spec.md.

### W7 - "Next.js 15" names no minimum patch
- **Where:** spec.md, the opening stack line; spec.json `stack`
- **Owner:** deploy-check
- **The line:** "Next.js 15 App Router, React 19, TypeScript, CSS Modules."
- **Reading one:** the Builder pins a current 15.x.
- **Reading two:** the Builder pins whatever `create-next-app` or a stale lockfile gives it, including `next@15.1.6`.
- **Why it matters:** `learning/lessons.md` records tip-split shipping `next@15.1.6` with CVE-2025-66478 while `deploy_check.py` recorded `install` as `ok: true`. The advisory shows up only in the detail string a person has to read at Gate 3. Naming a floor in the spec is the cheapest place to close it, and costs the Builder nothing.
- **Suggested wording:** "Next.js 15 App Router (`next@^15.2.3` or newer), React 19, TypeScript, CSS Modules."
