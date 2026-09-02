# Ambiguity report - pipeline-test-04

**Verdict:** 3 blocking, 7 worth a look

Read in order: `spec.md` and `spec.json` alone, then `idea.md`, then
`learning/lessons.md`. Bound to the spec hash recorded in
`.pipeline/ambiguity-meta.json` by `pipeline breaker pipeline-test-04 end`.

This is a strong spec. The grading-integrity section does by hand the two things
the lessons file says no script can do - it names which criterion fails when each
cut alone is left empty, and it discloses the one multi-cut criterion a proper
subset satisfies (c-2-3 via `NaN` serialising to `null`). I re-derived every
frame split and every cumulative array in the tables and all four games are
correct. The session-load numbers reproduce exactly against
`spec_linter.session_minutes` (38.7 / 37.4, largest session-2 cut share 40%), and
the drop candidates are real cuts a student types, which is the pipeline-test-03
lesson. The findings below are all in the two classes the lessons say remain the
Breaker's: a rule the spec states that no criterion grades, and a symbol or a
degenerate case left unstated.

## Blocking

### A1 - the hints tell the student to append to `frames`; the declared variable is `out`
- **Where:** spec.md, Session 1 cut points, and spec.json `cuts[cut-frames-scan].hint` / `cuts[cut-frames-tenth].hint`
- **Owner:** nothing
- **The line:** hint 1: "Walk `rolls` from index 0 and append the first nine frames to `frames`" / hint 2: "Append one last entry to `frames` holding every roll still left in `rolls`" - against spec.md: "a typed `const out: number[][] = []` is declared above `cut-frames-scan` and returned below `cut-frames-tenth`"
- **Reading one:** the accumulator is named `out`, as the return-safety sentence says. The student then reads a TODO telling them to append to `frames`, and the only `frames` in scope in `lib/frames.ts` is the exported function itself, so `frames.push(...)` is `Property 'push' does not exist on type '(rolls: number[]) => number[][]'`.
- **Reading two:** the accumulator is named `frames`, matching the hints, and the sentence about `const out` is wrong. `const frames: number[][] = []` inside `export function frames()` shadows the function name in its own body - legal TypeScript, so nothing complains.
- **Why it matters:** the hint is the only text the student sees (`CONTRACT.md`: "What the student reads is the task's `hint` from `spec.json`") and it is frozen at Gate 1, so this cannot be fixed after approval without `pipeline revise`. Under reading one the headline cut of session 1 ships with a TODO naming a symbol that does not exist, in the session that already carries the setup. Nothing downstream compares a hint's symbols to the code: `W066` only asks whether the hint names *anything* concrete and both hints pass it on `rolls`/`frames`; `tsc` at step 8 sees the generated skeleton, where the TODO is a comment; the test suite runs against `app/`, which is correct either way. It costs live minutes in exactly the session with the least slack.
- **Suggested wording:** name one variable in both places - either change the return-safety sentence to "a typed `const frames: number[][] = []` is declared above `cut-frames-scan`", or change both hints to say `out`.

### A2 - nothing says how `scoreGame` gets its frames, and one reading ships the answer to `cut-frames-scan` inside `lib/score.ts`
- **Where:** spec.md, Outcome and Session 2 cut points; spec.json `cuts[cut-score-lookahead].hint`
- **Owner:** nothing
- **The line:** "`lib/score.ts` - `scoreGame(rolls: number[]): (number | null)[]`, a cumulative total per frame" and, in the hint, "Index into `rolls` at `i`, never into `frames`."
- **Reading one:** `scoreGame` calls `frames(rolls)` from `lib/frames.ts` and walks the returned list while keeping a parallel index `i` into `rolls`. This is what "never into `frames`" implies, since it presupposes a `frames` value in scope.
- **Reading two:** `scoreGame` walks `rolls` itself and chunks it as it goes - a strike advances one, anything else two - because it only needs a frame count and a start index, not the frame arrays. `lib/score.ts` then contains its own written copy of the scan.
- **Why it matters:** reading two puts the whole answer to `cut-frames-scan` in the student's skeleton, in a file whose cuts are elsewhere. The student can copy the chunking out of `lib/score.ts` into the empty `lib/frames.ts` TODO. Every checker stays green: the app is correct, so `test-runner` passes; the skeleton has all cuts open, so `frames()` returns `[]`, c-1-2 to c-1-5 fail and every session-2 criterion fails on its own cuts, so `skeleton-check` sees exactly what it expects; `cutter` only counts markers. The leak scan looks for answer lines from the removed blocks, not for a paraphrased re-implementation in another file, and it is not on the owner list in any case. Reading two also silently decouples the sessions: under reading one, every session-2 criterion depends on `cut-frames-scan` and `cut-frames-tenth`, which spec.json's `cuts` lists for c-2-1 to c-2-6 do not declare.
- **Suggested wording:** in the Outcome, "`scoreGame` calls `frames(rolls)` and walks the frames it returns, carrying a parallel index into `rolls`; the frame-splitting scan exists only in `lib/frames.ts`."

### A3 - c-1-6 asks a server component for a 404 status and an id-interpolated message at the same time
- **Where:** spec.md, Session 1, criterion c-1-6; Screens, "unknown game id"; spec.json c-1-6
- **Owner:** test-runner
- **The line:** "`/games/no-such-game` responds 404 and displays the exact text `No game with id no-such-game`"
- **Reading one:** the page looks the id up, finds nothing, and renders the `no-game` element with the interpolated text. The App Router returns **200** - a page cannot set its own status code - so the text half passes and the status half fails.
- **Reading two:** the page calls `notFound()`. Next answers **404** and renders the nearest `not-found.tsx`, which is a server component that receives no route params, so the message can only be a static "No game with id" without the id. The status half passes and the text half fails.
- **Why it matters:** the only way to satisfy both is a `not-found.tsx` that reads the id from a client hook (`usePathname`), which contradicts the Out of scope line "Any client-side interaction. `/games/[id]` is a server component". c-1-6 is also declared "No cut: shipped written", so `skeleton-check` requires it to be **green on the skeleton** - a criterion the Builder cannot satisfy makes step 8 red as well as step 6. This is caught: the test asserts a status code and an exact string against `BASE_URL`, so it lands in the Builder/test-runner loop at step 6 and shows up in `results.json`. What the loop cannot decide is which of the three constraints to drop, and the constraint it will drop - server-only rendering - is the one nothing checks. Worth deciding here rather than paying up to 15 retries for it.
- **Suggested wording:** pick one. Either "`/games/no-such-game` renders the `no-game` element with the exact text `No game with id no-such-game`" and drop the status, or "`/games/no-such-game` responds 404 and displays the exact text `No game with that id`", rendered from `app/games/[id]/not-found.tsx`.

## Worth a look

### B1 - `pendingFrame` is promised in the Outcome with no signature, no criterion and a hint that names something else
- **Where:** spec.md, Outcome; spec.json `cuts[cut-pending-frame].hint`
- **Owner:** nothing
- **The line:** "`pendingFrame(...)`, the test for 'the rolls this frame needs do not exist yet'" - against the hint "Set `pending` to true while the rolls this frame needs are still missing from `rolls`" and the declared fallback "`let pending = false`"
- **Reading one:** an exported `pendingFrame(rolls, i, frame): boolean` that `scoreGame` calls, with `cut-pending-frame` inside it over a `let pending = false` / `return pending` pair.
- **Reading two:** no such export - a loop-local `let pending = false` in `scoreGame`, which is what the fallback wording describes. `lib/score.ts` then does not deliver the function the Outcome promises, and the idea lists as one of three things the student types.
- **Why it matters:** the parameter list is literally `(...)`, and no criterion mentions `pendingFrame`, so no test will reference it and `tsc` has nothing to resolve - both readings ship. `gameTotal(...)` is elided the same way but is recoverable from the endpoint section (`gameTotal(scoreGame(rolls))`); `pendingFrame` is not recoverable from anywhere. Not blocking because the graded behaviour is identical either way, but the Pack Writer will write session 2's guide around a function that may not exist.
- **Suggested wording:** "`pendingFrame(rolls: number[], i: number, frame: number[]): boolean`, the test for 'the rolls this frame needs do not exist yet', called by `scoreGame` once per frame" - or drop it from the Outcome and say the check is a local `pending` flag inside `scoreGame`.

### B2 - `cut-frames-tenth` needs to know where the scan stopped, and no symbol for that is declared
- **Where:** spec.md, Session 1 cut points
- **Owner:** nothing
- **The line:** "Append one last entry to `frames` holding every roll still left in `rolls` after those nine frames" - against "a typed `const out: number[][] = []` is declared above `cut-frames-scan`", which is the only declaration the spec places above the markers
- **Reading one:** the scan index is declared beside `out`, above `cut-frames-scan`, so both cut blocks read the same `i` and each TODO is fillable on its own.
- **Reading two:** `let i = 0` lives inside `cut-frames-scan`. The markers are comments, not braces, so `app/` still compiles and the fully-open skeleton removes both blocks together and also compiles - but a student who fills the second TODO before the first has no `i` and no name for it in the hint.
- **Why it matters:** `typecheck` only ever sees the all-open skeleton, where both references are gone, so it will not fire; `return-safety` only looks for a cut holding the only `return`. A student working in session order declares `i` themselves in the first cut and is fine, which is why this is not blocking - but "after those nine frames" is the one quantity in either hint with no symbol attached to it.
- **Suggested wording:** "a typed `const out: number[][] = []` and a `let i = 0` are declared above `cut-frames-scan`; both cut blocks read and advance `i`", and add "reading `i` for the position the scan stopped at" to the `cut-frames-tenth` hint.

### B3 - session 1's declared end state cannot exist, because only one skeleton is generated
- **Where:** spec.md, Session 1 "Runs at the end"; Screens, state "frames without scores"; spec.json `screens[sc-game].states[0]`
- **Owner:** pack-writer
- **The line:** "All four games render as correctly divided frame grids with their roll symbols, and no totals anywhere" and "**frames without scores** - session 1's end state: boxes and symbols, no score cells and no total"
- **Reading one:** a session-1 milestone described loosely - the score cells are there but nobody looks at them yet.
- **Reading two:** an actual state of `sc-game`, as spec.json's `states` list says it is.
- **Why it matters:** `cutter.py` generates one skeleton for the whole project, so the score-cell and `game-total` markup that Session 2 "adds as shipped markup" is present from the first minute of session 1, wired to `lib/score.ts` with every cut open. By the spec's own fallbacks that renders `0` in every `total-N` cell and `-1` in `game-total`. So at the end of session 1 there are totals everywhere, one of them a negative number, and the state "frames without scores" is unreachable in the finished app. This is also the "every fetch needs an owner" lesson in another form: a screen built in session 1 depending on a module session 2 owns. The place it surfaces is session 1's guide telling the instructor what the student should see, read by a person at Gate 3, and again at the step-13 dry run.
- **Suggested wording:** "Session 1's page renders the score cells and `game-total` from the start; with `lib/score.ts` unfilled they read `0` and `-1`, and session 1 ignores them. The grid, the symbols and the frame count are what session 1 is judged on." Then drop "frames without scores" from `states` or rename it "scores not yet computed".

### B4 - two rules the spec states that no criterion grades
- **Where:** spec.md, Data model (roll symbols) and Endpoints (`ep-games-list`)
- **Owner:** nothing
- **The line:** "a roll of 0 is `-`" / "`[0,0]` reads `- -`", and "in the seed's order: `g-gutter`, `g-perfect`, `g-mixed`, `g-partial`"
- **Reading one:** both are requirements, and `lib/symbols.ts` and the route are expected to honour them.
- **Reading two:** both are illustration. Rendering `0 0` for a gutter frame, or returning the four games in any order, passes every one of the twelve criteria.
- **Why it matters:** this is the class the lessons file counts six times ("a rule the spec states that no criterion grades"). c-1-4 reads g-perfect's page, c-1-5 reads g-mixed's, and no criterion renders `g-gutter`'s page at all - so the `-` symbol, which appears in half the seed, is never asserted anywhere. Both files ship written rather than cut, so no cut becomes bypassable and the Builder is likely to get them right; the exposure is a silent regression with the suite green. c-1-2 and c-1-3 name games rather than indices, so the order is a free variable for the Test Writer too.
- **Suggested wording:** add `- 1` in `frame-6` to c-1-5's list of exact strings (g-mixed frame 6 is `[0,1]`), and add "in that order" to c-1-1: "returns 200 with a JSON array of 4 games with `id` `g-gutter`, `g-perfect`, `g-mixed`, `g-partial` in that order, each carrying `id`, `name`, `rolls` and `frames`".

### B5 - session 2 is over the cap once the spec's own two adjustments are applied
- **Where:** spec.md, Session load
- **Owner:** nothing
- **The line:** "Both are under the 40 minute cap" and, four lines later, "Session 2 also edits the page markup, which the model does not price at all - call it 3 minutes"
- **Reading one:** 37.4 and 38.7 are the numbers; both fit.
- **Reading two:** 37.4 + 3 = 40.4 against a 40 minute cap, before the model's own stated 5-minute error and against a track record of five consecutive overruns at 45, 45, 45, 50, 47.
- **Why it matters:** the spec is honest about this and it still reads as slack it does not have. `spec-linter` will not fire - I reproduced 38.7 and 37.4 exactly, and the largest session-2 cut is 40% of its cut minutes against the 45% cap, so no `W112` and no `W114`. Nothing before the step-13 dry run measures it. Both named drop candidates are real cuts a student types, which is the right shape, but neither is *decided*: "pull this only if the scan overruns" leaves the call to whoever is teaching, and the lessons file records two consecutive dry runs that could not say whether the trims were pulled. The idea also put the tenth-frame cut in session 2 and the spec moved it to session 1 with a reason given, which is the right call for `E113` but loads the setup session with the block the idea flagged as the overrun risk.
- **Suggested wording:** state the decision rather than the option - "`cut-game-total` is handed out pre-written; session 2's cuts are `cut-score-lookahead` and `cut-pending-frame`" - or say plainly that session 2 is planned at 40.4 minutes and that the trim is expected to be pulled.

### B6 - "empty" is not pinned against the markup, and c-2-6's empty cells are load-bearing for grading
- **Where:** spec.md, Session 2, criterion c-2-6; Screens table
- **Owner:** test-runner
- **The line:** "leaves the elements with `data-testid` `total-5` and `total-6` empty" / "the cumulative score as a decimal string, or nothing when that frame's score is `null`"
- **Reading one:** the element renders no text at all, so `textContent` is `""`.
- **Reading two:** the element renders a layout placeholder - `&nbsp;`, an em dash, a `-` reusing the gutter symbol - so the grid does not collapse. Then a strict emptiness assertion fails, and a whitespace-tolerant one would also accept a cell rendering `null`.
- **Why it matters:** c-2-6 is the only criterion that reads a populated and an unscored score cell in the same test, and the Grading integrity section leans on it twice: it is one of the two criteria that catch an empty `cut-pending-frame`, and the argument that `NaN` cannot hide on the page is exactly "`NaN` is not an empty cell". If the Builder styles unscored cells with a placeholder, that argument weakens and the Test Writer has to choose the assertion. Cheap to catch - it is a red test at step 6 - but the resolution should be the spec's, not the loop's.
- **Suggested wording:** "the elements with `data-testid` `total-5` and `total-6` contain no text: `textContent` is the empty string. A pending cell renders nothing, not a placeholder character."

### B7 - a POST body that is not JSON at all has no declared status
- **Where:** spec.md, Endpoints, `ep-games-score`; spec.json c-2-5
- **Owner:** nothing
- **The line:** "`rolls` is absent, or is not an array of numbers: 400 with `{ "error": "rolls must be an array of numbers" }`"
- **Reading one:** the handler wraps `request.json()`, so a malformed or empty body is "rolls is absent" and answers 400 with that message.
- **Reading two:** the handler awaits `request.json()` unguarded, the parse throws, and Next answers 500. The endpoint's declared `status` list is `[200, 400]`, so 500 is undeclared behaviour.
- **Why it matters:** c-2-5 only requires a body "whose `rolls` is not an array of numbers", which the Test Writer can satisfy with `{"rolls": "abc"}` and never touch the parse path - so this may well go untested, which is why I have not put `test-runner` on it. Low impact: the Out of scope section already says the body is trusted once it is an array of numbers, and no student cut is involved. It is one clause.
- **Suggested wording:** "a request whose body is absent, empty or not valid JSON is treated the same as an absent `rolls`: 400 with `{ "error": "rolls must be an array of numbers" }`."
