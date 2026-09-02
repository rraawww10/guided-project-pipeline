# Ambiguity report - pipeline-test-04

**Spec hash:** `b91e8b8d11143b7338b5f52d9227ac086af436744c392ca580db83b1ed93265d`
(spec.md + spec.json as read; matches `.pipeline/breaker-begin.json`)

**Verdict:** 3 blocking, 7 worth a look

The arithmetic in this spec holds. I re-derived all four seed games by hand -
frames, cumulative arrays, totals, the tenth-frame reach, the two `null` frames
of `g-partial` and the six-frame count - and every number in the derived-values
table and every criterion literal is correct. The load table also reproduces
exactly against `spec_linter.session_minutes` (7.7 + 6.0 -> 38.7, 7.9 + 6.0 +
6.0 -> 37.4, largest share 40%). The findings below are all about what the spec
does *not* say, and about which of its claims no script will ever re-check.

## Blocking

### A1 - No criterion ever reads a score cell that has a number in it
- **Where:** spec.md, Session 2, criterion c-2-6; spec.json `sessions[1].criteria[5]`; the Screens table
- **Owner:** nothing
- **The line:** "**c-2-6** - `/games/g-partial` displays the exact text `34` in the element with `data-testid` `game-total` and leaves the elements with `data-testid` `total-5` and `total-6` empty."
- **Reading one:** the per-frame cumulative column is part of the graded page, and c-2-6 is just naming its two most interesting cells.
- **Reading two:** the graded page contract is exactly what the criteria say: `game-total` reads `34`, `total-5` and `total-6` are empty, and every other `total-k` is unconstrained.
- **Why it matters:** walk the twelve criteria against the page. c-1-4 and c-1-5 read frame boxes. c-1-6 reads the not-found text. c-2-6 reads `game-total` and asserts two cells are *empty*. c-2-1 to c-2-5 are all `POST`. **No criterion asserts a number in any `total-k` element**, so an `app/` that renders every score cell empty - or renders `null`, or a dash, or the frame's own score instead of the cumulative one - passes all twelve criteria, passes the test runner, passes mutation, passes the skeleton check (c-2-6 has cuts, so it is only ever required to fail on the open skeleton) and ships. The cumulative-score-per-frame column is the one thing the Outcome says this project exists to teach ("`/games/[id]` rendering the frame grid, the roll symbols, the cumulative score per frame and the game total"), it is shipped markup rather than a cut so no student writes it, and it is graded nowhere. This is the recurring class in `learning/lessons.md` - "A rule the spec states that no criterion grades", 6 of 10 Gate 1 rejections - and it has no downstream owner: `test-runner` sees green, `skeleton-check` only decides pass/fail per criterion, and there is no `code_checks` entry (nor could one see rendered text).
- **Suggested wording:** extend c-2-6 to "...displays the exact text `7`, `16`, `25` and `34` in the elements with `data-testid` `total-1` through `total-4`, the exact text `34` in `game-total`, and leaves `total-5` and `total-6` empty" - one clause, no new criterion, and it makes the populated column and the empty column graded by the same test.

### A2 - Session 2's score cells have no declared data source
- **Where:** spec.md, Session 2, "Builds"; Screens `sc-game`
- **Owner:** test-runner
- **The line:** "**Builds.** `ep-games-score`. The score cells and the `game-total` element are added to `sc-game` in this session as shipped markup, not as a cut."
- **Reading one:** the server component already holds the game's `rolls`, so it calls `scoreGame(game.rolls)` and `gameTotal(...)` in process, exactly as session 1's page calls `frames()` after reading `lib/store.ts`.
- **Reading two:** session 2 built the scoring endpoint, so the page `POST`s to `/api/games/score` and renders the response - which is what "answer the running total over HTTP **and on the page**" in the session goal can be read to mean.
- **Why it matters:** the spec goes out of its way to settle this for session 1 - "It reads the seed through `lib/store.ts` directly rather than fetching `/api/games`, so session 1's page does not depend on its own HTTP route" - and then says nothing for session 2, where the same question is sharper. Reading two is the shape `learning/lessons.md` records as "Every fetch needs an owner": a server component `fetch`ing its own route needs an absolute base URL, cannot be relative, and self-fetching during render or `next build` is the standard way this fails late - c-2-6 goes red at step 6, or the page renders in dev and the build breaks at step 10. It also changes the instructor's story about what session 2 is for, and it silently makes `sc-game` depend on `ep-games-score`.
- **Suggested wording:** add to Session 2's Builds paragraph: "The page calls `scoreGame` and `gameTotal` from `lib/score.ts` directly, like session 1's page calls `frames`; it never fetches `/api/games/score`, which exists only for the HTTP criteria."

### A3 - "each carrying `frames`" has to mean key-presence, and only the prose says so
- **Where:** spec.md, Session 1, criterion c-1-1; spec.json `sessions[0].criteria[0]`
- **Owner:** skeleton-check
- **The line:** "**c-1-1** - `GET /api/games` returns 200 with a JSON array of 4 games, each carrying `id`, `name`, `rolls` and `frames`. No cut: the route and the store ship written, so this is green on the skeleton and tells the student the scaffolding is intact."
- **Reading one:** the four objects each have a `frames` key; its value is not constrained here, so `frames: []` satisfies it.
- **Reading two:** each object carries *its frames* - so the test asserts `frames` is a non-empty list of lists (ten of them for three of the four games), which is the natural way to write "carrying `frames`" once you have the derived-values table in front of you.
- **Why it matters:** `cutter.expected_skeleton_results` gives a criterion with an empty `cuts` list the verdict PASS ("A criterion with no cuts is given to the student, so it must PASS", `cutter.py:568`). On the skeleton `cut-frames-scan` is open and `frames()` returns the declared empty `out`, so reading two makes c-1-1 fail on the skeleton and `pipeline cut` refuses to hand over a skeleton at step 8 - after the Test Writer and the Builder have both been paid. The Test Writer reads the criterion, not the parenthetical about the skeleton, and spec.json carries no parenthetical at all. Note c-1-1 is also the one criterion whose whole job is to be green on the skeleton, so the two readings are not equally harmless.
- **Suggested wording:** "returns 200 with a JSON array of 4 games, each of which has the keys `id`, `name`, `rolls` and `frames` - `frames` may be empty, because this criterion checks the scaffolding and not the scan."

## Worth a look

### B1 - `pendingFrame` is a function in two places and a local variable in a third
- **Where:** spec.md, Outcome; Session 2 cut points, `cut-pending-frame`; idea.md, "What the student types"
- **Owner:** return-safety
- **The line:** "`pendingFrame(...)`, the test for \"the rolls this frame needs do not exist yet\"" against the hint "Set `pending` to true while the rolls this frame needs are still missing from `rolls`".
- **Reading one:** `pendingFrame` is an exported function in `lib/score.ts` and `cut-pending-frame` is the assignment to a `let pending = false` declared at the top of its body - which reconciles both lines and is return-safe.
- **Reading two:** `pending` is a local inside `scoreGame`'s loop and `pendingFrame` never exists, since no criterion names it and its signature is written as a literal `(...)` nowhere expanded.
- **Why it matters:** under reading one the cut sits inside a small boolean function, which is precisely the shape that tempts a `return` inside the markers (TS2355, two recorded occurrences in `lessons.md`) - and the spec's own return-safety sentence covers "Both route handlers and `gameTotal`" and names neither `pendingFrame` nor `scoreGame`, the two functions that actually hold the session-2 cuts. `cutter.scan_return_safety` catches that at step 8 without a toolchain, so it is owned, but it is owned late. Under reading two the Outcome and the idea both promise the student a deliverable that does not exist, and nothing sees that at all.
- **Suggested wording:** in the Outcome, give it a signature - "`pendingFrame(frames: number[][], rolls: number[], i: number): boolean`" - and extend the return sentence to "`scoreGame`, `pendingFrame`, `gameTotal` and both route handlers keep their `return` below the markers".

### B2 - "fails alone on c-2-3" is not true under the literal reading of the sibling hint
- **Where:** spec.md, Session 2 cut points and the Grading integrity table
- **Owner:** nothing
- **The line:** "With `pendingFrame` left empty the last two entries come back as numbers, which is what makes this the criterion that grades it."
- **Reading one:** the lookahead guards missing rolls (`rolls[i+1] ?? 0`, or a `slice(...).reduce(...)`), so with `pending` stuck at `false` frame 5 of `g-partial` scores 20, the array reads `[7,16,25,34,54,...]`, and c-2-3 goes red as the table claims.
- **Reading two:** the hint says "10 plus the next two entries of `rolls`" and "Index into `rolls` at `i`", so the block is `10 + rolls[i+1] + rolls[i+2]`. For `g-partial` frames 5 and 6 that reaches `rolls[10]` and `rolls[11]`, which do not exist, giving `NaN` - and `JSON.stringify(NaN)` is `null`. The response body is then exactly `[7,16,25,34,null,null]` and **c-2-3 passes with `cut-pending-frame` still empty.**
- **Why it matters:** the table's last column is the spec's own proof that each cut is graded, and it says it was "checked by hand for every cut, because the skeleton check only sees the all-open and no-cuts states". Under reading two that hand-check is wrong for `cut-pending-frame`, and nothing recomputes it: the skeleton check only ever sees the all-open state (where `cut-score-lookahead` is open too and the array is all zeros, so c-2-3 does go red), and E110 does not fire because the five cut signatures are all distinct. Grading integrity survives - c-2-4 and c-2-6 still catch an empty `cut-pending-frame`, because `NaN` is not `null` in `gameTotal` and renders as `NaN` in a score cell - so this is a false claim and a misleading diagnosis lever ("the one to read first when session 2 goes red"), not a bypassable cut. It is also worth saying out loud that in this project `NaN` and "not computable yet" are indistinguishable once the response is serialised, in a project whose whole point is that the second one is a real value.
- **Suggested wording:** either state the guard - "a lookahead past the end of `rolls` must leave `frameScore` as `null`, never `NaN`" - or correct the table to "fails alone on c-2-4".

### B3 - c-1-6 wants a 404 status and the id in the message, and App Router puts those in two different files
- **Where:** spec.md, Session 1, criterion c-1-6; Screens, "unknown game id"
- **Owner:** test-runner
- **The line:** "**c-1-6** - `/games/no-such-game` responds 404 and displays the exact text `No game with id no-such-game`. No cut: shipped written."
- **Reading one:** the page calls `notFound()`, which gives the 404, and the text lives in `app/games/[id]/not-found.tsx` - which receives no `params`, so the id has to be recovered from `headers()` or a client `useParams`.
- **Reading two:** the page renders the `no-game` element itself with the id interpolated, which is trivial and returns 200 - failing half the criterion.
- **Why it matters:** this is the one criterion in session 1 that is "shipped written" *and* has to be green on the skeleton (no cuts, so `cutter` requires PASS), and it is the only place where the spec asks for something the framework does not hand over in one move. The cost is retries in the Builder/test-runner loop rather than a wrong ship, because both facts are pinned exactly - but the spec pins the outcome without naming the mechanism anywhere else it is this awkward.
- **Suggested wording:** name the file: "the id-bearing message is rendered by `app/games/[id]/not-found.tsx` after the page calls `notFound()`", or drop the id from the required text.

### B4 - `frames()` is undefined for a roll list that stops in the middle of a frame
- **Where:** spec.md, Session 1 cut points, `cut-frames-scan`; Endpoints, `ep-games-score`
- **Owner:** nothing
- **The line:** "taking two rolls per frame unless the first of them is 10, in which case the frame holds that one roll and the index advances by one. Stop as soon as `rolls` runs out"
- **Reading one:** the scan slices two at a time, so a single leftover roll becomes a one-roll frame: `frames([1,4,5])` is `[[1,4],[5]]`, and `pendingFrame` on a one-roll open frame is undefined too ("an open frame needs nothing beyond its own two rolls" - it has one).
- **Reading two:** an incomplete pair is not a frame and is dropped, or worse, is pushed as `[5, undefined]`, which serialises to `[5,null]` inside a `number[][]`.
- **Why it matters:** `POST /api/games/score` accepts any array of numbers ("the POST body is trusted once it is an array of numbers") and `g-partial` establishes that a game stopped early is a legal input - but all four seed games happen to run out exactly on a frame boundary, so no criterion, fixture or seed distinguishes the readings. Whatever the Builder picks ships unexamined; nothing downstream looks. Out of scope covers *validating* impossible games, which is a different question from what the arithmetic does with a legal partial one.
- **Suggested wording:** add to the scoring rules: "A roll list that stops after the first roll of an open frame yields that frame with one roll, and the frame is pending."

### B5 - Session 2 modifies `sc-game` without declaring it, and the three minutes are invisible to the linter
- **Where:** spec.json `sessions[1].builds`; spec.md, Session load
- **Owner:** pack-writer
- **The line:** "Session 2 also edits the page markup, which the model does not price at all - call it 3 minutes."
- **Reading one:** `builds` means "creates from nothing", so session 2 correctly lists only `ep-games-score` even though c-2-6 targets `sc-game`.
- **Reading two:** `builds` is what the linter charges 3 minutes for and what the Pack Writer reads to plan the session, so a session that adds two element families to a screen builds that screen and should say so.
- **Why it matters:** declaring it would put session 2 at 40.4 estimated minutes and raise W112; not declaring it keeps the spec silent at 37.4 with the overrun disclosed only in prose. Six sessions have now been measured against this model and five overran (45, 45, 45, 50, 47), the worst known error is about 5 minutes, and the spec itself says the model under-reads `cut-score-lookahead` because the decision regex scores its three mutually exclusive rules as one branch and `cut-pending-frame`'s three cases as zero. Both sessions here are therefore realistically at or over 40. The mitigation is real, and I checked it against the `lessons.md` failure mode "a named drop candidate that costs no live minutes": both candidates (`cut-frames-tenth`, `cut-game-total`) are blocks a student types, so they recover actual minutes - which is why this is not blocking. The Pack Writer prices the session at step 9 and has been within ~1 minute; it needs to know the markup edit is in session 2.
- **Suggested wording:** add `"sc-game"` to session 2's `builds` and let the linter's W112 be the disclosure, or state in Session load that session 2's real estimate is 40.4 and which drop candidate is pulled by default.

### B6 - The `-` glyph, and `g-gutter`'s page, are graded nowhere
- **Where:** spec.md, Data model, "Roll symbols"; Session 1 criteria
- **Owner:** nothing
- **The line:** "a roll of 0 is `-`; anything else is its digit. A frame box holds its symbols joined by one space, so `[2,8,6]` reads `2 / 6` and `[0,0]` reads `- -`."
- **Reading one:** the rule is stated once and `lib/symbols.ts` ships written, so it is settled and needs no criterion.
- **Reading two:** it is a rule like any other, and c-1-4 and c-1-5 grade `X`, `/`, digits and the single-space join through `g-perfect` and `g-mixed` only - no criterion renders `/games/g-gutter` at all, so `0` mapping to `-` is asserted by nothing.
- **Why it matters:** "All Gutters" is the first game in the seed and the first page an instructor opens in the dry run. A `symbols.ts` that returns `"0"` instead of `"-"` keeps all twelve criteria green and every checker silent. Small, cosmetic, and in the same class as A1 - a stated rule with no criterion - which is why it is here rather than above.
- **Suggested wording:** extend c-1-5, or add to c-1-4, "and `/games/g-gutter` displays the exact text `- -` in the element with `data-testid` `frame-1`".

### B7 - "frames without scores" is a state the finished app never renders
- **Where:** spec.json `screens[0].states[0]`; spec.md, Screens, States
- **Owner:** test-runner
- **The line:** "**frames without scores** - session 1's end state: boxes and symbols, no score cells and no total."
- **Reading one:** it is a temporal state of the project, true only between session 1 and session 2, and no test should ever assert it.
- **Reading two:** it is what spec.json says it is - a state of `sc-game`, listed beside "fully scored" and "unknown game id", both of which are real states of the shipped page - so a suite written from spec.json asserts that some route renders frame boxes with no `total-k` elements.
- **Why it matters:** the tests are written before the code and the whole suite runs against the finished `app/`, where every game renders score cells. A test taking reading two is red at step 6 and the Builder cannot fix it, because rule 3 stops it editing `verify/` - so it burns retries against a spec sentence rather than a bug. The Test Writer works criterion-first and no criterion covers this state, which is the only reason this is not blocking.
- **Suggested wording:** in spec.json, either drop the state or rename it "frames without scores (session 1 only, not a state of the finished page)".
