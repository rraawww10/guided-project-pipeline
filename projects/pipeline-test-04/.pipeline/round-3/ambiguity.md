# Ambiguity report - pipeline-test-04

**Verdict:** 1 blocking, 5 worth a look

Round 3. Read in the required order: `spec.md` and `spec.json` alone, then
`idea.md`, then `learning/lessons.md`, and only then round 2's `ambiguity.md`,
`gate1.json` and `why.md`. Bound to spec hash
`338b6dde4abc403b864d1378e5eda30d5c34479b145dc26c76d874c38ed9db4a`, the hash
`pipeline breaker pipeline-test-04 begin` recorded and the same hash `lint.json`
carries.

**What I re-derived by hand before reading anything else.** All four frame
splits, all four cumulative arrays and all four totals in the Data model tables
are correct, including `g-mixed`'s tenth frame scoring 16 by the spare rule and
`g-perfect`'s scoring 30 by the strike rule with its own second and third rolls
as the bonus - so the claim that the tenth frame needs no special rule holds for
every legal game, not just the fixtures. The session-load table reproduces
`spec_linter.session_minutes` exactly (38.8 / 37.4; 7.8, 6.0 / 7.9, 6.0, 6.0;
57, 47, 60, 53, 34 hint words; 1, 0, 1, 0, 0 decisions), which is what `lint.json`
holds. E110 is satisfied - all five cut signatures are distinct. E113 holds (2
cuts in the setup session against 3). W114 does not fire and the spec is right
about why: `SHARE_MIN_CUTS` is 3, so session 1's 56% share is not measured, and
session 2's largest cut is 40%. Every fail-alone claim in the Grading integrity
table checks out, including the non-obvious one - with `cut-frames-scan` open and
`cut-frames-tenth` filled, `i` is still 0 and the tenth block appends the whole
roll list as a single frame, so c-1-3 sees one frame where it wants six.

Round 2's four required fixes (A1, A2, A3, B5) are all genuinely made, and the
three round-1 fixes why.md says to keep are kept. Four of round 2's ten findings
were re-raises on unchanged text; I have tried hard not to add a fifth, so three
of the six below carry an explicit round-2 lineage and the classification I give
each one is compared against the one round 2 gave it.

## Blocking

### A1 - `cut-pending-frame` can be left empty with every criterion green, because nothing says the lookahead block must not guard the end of `rolls`
- **Where:** spec.md, Session 2 cut points (`cut-score-lookahead`, `cut-pending-frame`) and Grading integrity; spec.json `cuts[cut-score-lookahead].hint`, criteria c-2-3, c-2-4, c-2-6
- **Owner:** nothing
- **The line:** "It fails c-2-3 only when the lookahead guards the end of `rolls`; an unguarded one yields `NaN`, which serialises to `null` and matches c-2-3's expected body." And, in Grading integrity: "Grading integrity does not depend on c-2-3: c-2-4 compares `total`, where `NaN` is not 34, and c-2-6 reads the page, where `NaN` is not an empty cell."
- **Reading one:** `cut-score-lookahead` is arithmetic only. Its hint lists three rules and no guard, so the block reads `frameScore = 10 + rolls[i+1] + rolls[i+2]` and friends, and the single place the end of `rolls` is tested is `pendingFrame`. `scoreGame`'s shipped-written wrapper pushes `null` when `pendingFrame` returns true and the running sum otherwise. With `cut-pending-frame` empty, `pending` is always `false`, `g-partial`'s frames 5 and 6 are `NaN`, c-2-3 passes on the `null` serialisation and c-2-4 and c-2-6 fail - exactly what the spec claims.
- **Reading two:** the lookahead block guards its own indexing, which is what a Builder writing `lib/score.ts` for real is likely to do and what `noUncheckedIndexedAccess` would force: `frameScore = i + 2 < rolls.length ? 10 + rolls[i+1] + rolls[i+2] : null`. `frameScore` is *declared* `number | null`, so a `null` there is legal and needs no wrapper change. Now `g-partial` yields `[7,16,25,34,null,null]` with `cut-pending-frame` still empty, `gameTotal` returns 34 because the last non-null entry is 34, and the page renders two empty cells because React renders nothing for `null`. **c-2-3, c-2-4 and c-2-6 all pass with `cut-pending-frame` empty.** The cut it is meant to grade grades nothing.
- **Why it matters:** the two criteria the spec nominates as the ones that catch an empty `cut-pending-frame` are exactly the two that stop catching it under reading two, so the Grading integrity section's guarantee for that cut rests on an implementation choice the spec never makes and neither hint states. `spec-linter` cannot see it: E110 compares cut signatures and `cut-pending-frame` {c-2-3, c-2-4, c-2-6} differs from `cut-score-lookahead` {c-2-1, c-2-2, c-2-3, c-2-4, c-2-6}, so the rule that catches indistinguishable *pairs* is silent on a cut made redundant by a *sibling's* implementation. `skeleton-check` sees only the all-open and no-cuts states, and under both readings the all-open skeleton fails every session-2 criterion on `frameScore`'s `null` fallback, so step 8 reports exactly what it expects. `cutter` counts markers. `test-runner` runs against `app/`, which is correct under either reading. `code-check` runs nothing - `code_checks` is undeclared, which the spec states plainly. This is the lessons file's "the cut can be left empty with every criterion green" shape, and it reaches the student skeleton with every gate green.
- **Lineage - this is not new, and round 2 missed it.** Both quoted sentences are in the spec round 2 read, word for word (`.pipeline/round-2/spec.md` lines 301-303 and 331-339); they arrived as round 1's fix to the c-2-3 disclosure and have not changed since. Round 2 raised no finding on them. Round 3 did make the question sharper rather than softer: closing round 2's B1 promoted `pendingFrame` to an exported function with a signature and a declared call site, so there are now two named places the end-of-`rolls` test could live and the spec assigns it to neither. Round 2's B1 was *worth a look / nothing* and cited `cut-pending-frame`, so `gate1-check` may match this against it - it should not read as an escalation of B1. B1 was "`pendingFrame` has no signature", why.md records it as closed by fix 1, and it is closed. This is a different property of the same cut: which of the two functions owns the guard, and therefore whether the cut is gradable at all. Nothing in why.md records it as deliberately kept.
- **Suggested wording:** in the `cut-score-lookahead` bullet, "the block applies the three arithmetic rules unconditionally and never tests the length of `rolls`; `pendingFrame` is the only place the end of `rolls` is checked, and `scoreGame` pushes `null` for a frame it reports pending" - and add "this is what makes c-2-4 and c-2-6 fail when `cut-pending-frame` is empty" to the Grading integrity paragraph so the dependency is stated where the guarantee is made.

## Worth a look

### B1 - `i` is passed to two different functions and its convention is stated in neither
- **Where:** spec.md, Outcome (`pendingFrame(rolls: number[], i: number, frame: number[]): boolean`) and Session 2 Builds; spec.json `cuts[cut-score-lookahead].hint`, `cuts[cut-pending-frame].hint`
- **Owner:** test-runner
- **The line:** "keeps a parallel index `i` into `rolls`, and advances `i` by the length of each frame" - against "Index into `rolls` at `i`, never into `frameList`" and "a frame that opens with a 10 needs the two entries after it"
- **Reading one:** `i` is the index of the frame's **first** roll when both functions see it, and the advance happens after. A strike frame reads `rolls[i+1]` and `rolls[i+2]`; a spare reads `rolls[i+2]`.
- **Reading two:** `i` has already been advanced past the frame, so "the next two entries" are `rolls[i]` and `rolls[i+1]`. Nothing in either hint says which, and "the two entries after **it**" leaves "it" as either the frame or the index.
- **Why it matters:** reading one is the only reading consistent with "advances `i` by the length of each frame", so a careful Builder gets there - but the two hints are the whole text the student sees, and they are the two blocks that have to agree on the convention. If they disagree, `g-mixed`'s array is wrong from frame 3 onwards, which is loud: c-2-2 is the criterion the spec itself nominates as the one to read first when session 2 goes red, so this lands in the Builder/test-runner loop at step 6 and costs a retry, not a rebuild. Genuinely new to this round, and it could not have been raised earlier: `pendingFrame`'s parameter list was literally `(...)` in the spec round 2 read, which is what round 2's B1 flagged.
- **Suggested wording:** "`i` is the index in `rolls` of the frame's first roll; `scoreGame` advances it by the frame's length after scoring the frame" - once, in the Outcome, where the signature is.

### B2 - an in-progress game whose last frame is short is undefined behaviour behind a declared 200
- **Where:** spec.md, Endpoints `ep-games-score`; Out of scope; spec.json `cuts[cut-pending-frame].hint`
- **Owner:** nothing
- **The line:** "`rolls` is an array of numbers: 200 with `{ "frames": FrameScore[], "total": number }`" and "The seed is legal and the POST body is trusted once it is an array of numbers."
- **Reading one:** an open frame with only one roll bowled is pending - its own second roll is missing - so `[3]` scores `[null]` with total 0, and "not computable yet" covers the frame you are standing in.
- **Reading two:** `pendingFrame`'s hint says "an open frame needs nothing beyond its own two rolls", so a one-roll open frame is not pending, `frameScore` is `3 + undefined`, and the response is `[null]` by way of `NaN` - or `[3]` if the scan never emitted the short frame at all, which the `cut-frames-scan` hint also does not settle ("Stop as soon as `rolls` runs out" does not say whether the half-frame is appended first).
- **Why it matters:** `g-partial` is itself an in-progress game, so "in-progress" cannot be waved off as an impossible game; it just happens to end on two strikes, where every reading agrees. The POST endpoint takes any array of numbers and declares only 200 and 400, and `[3]` or `[10,5]` is the first thing a curious student sends it. Under reading two the endpoint answers `null` from `NaN` in a project whose stated point is that `null` is a real value distinct from a broken one, and the Data model's "the cumulative array is `null` from the first frame whose bonus rolls are missing onwards" is quietly violated: a pending frame followed by a short scoreable one is the one input shape that produces a number after a `null`. No criterion covers any of it, no cut hint decides it, and the seed cannot exercise it, so nothing downstream looks. Not blocking: every graded value is unaffected and the Builder can ship either reading. Present in the spec round 2 read (the "trusted once it is an array of numbers" line is unchanged) and not raised then.
- **Suggested wording:** one line in Out of scope - "a roll list that stops part-way through a frame is out of scope: `frames()` emits only whole frames, so a trailing single roll is dropped and never scored."

### B3 - the unknown-id page does not say what happens to the score cells and `game-total`
- **Where:** spec.md, Screens, state "unknown game id"; spec.json `screens[sc-game].elements`, criterion c-1-6
- **Owner:** nothing
- **The line:** "the page answers 200 and renders the `no-game` element with the interpolated text and no frame boxes"
- **Reading one:** "no frame boxes" means no grid at all, so the score cells and `game-total` are inside the same conditional and none of them render.
- **Reading two:** only frame boxes are excluded. `game-total` is listed unconditionally in `screens[sc-game].elements`, so it renders, showing `gameTotal([])` - `0` in the finished app and `-1` on the skeleton - on a page that says there is no such game.
- **Why it matters:** c-1-6 asserts the message and the absence of `frame-1` and nothing else, so both readings are green at step 6 and at step 8, and c-1-6 is a no-cut criterion that `skeleton-check` only requires to stay green. The cost is cosmetic - a stray `-1` under "No game with id no-such-game" in the session-1 walkthrough - which is why it is not blocking. Round 2's B3 covered a different element on this same state and round 2's spec said the route "responds 404", so this line has changed; the score cells and `game-total` were unstated in both rounds and neither round raised them. New as a finding.
- **Suggested wording:** "an unknown id renders the `no-game` element alone - no frame boxes, no score cells and no `game-total`."

### B4 - the minute model reads zero decisions on two more cuts than the spec admits, and both sessions sit inside its known error of the cap
- **Where:** spec.md, Session load
- **Owner:** pack-writer
- **The line:** "It under-reads `cut-score-lookahead` in particular: three mutually exclusive rules live in that block and the regex sees one stated decision."
- **Reading one:** the disclosure is complete, so the residual risk is the model's stated ~5 minutes on 38.8 and 37.4, and the two pre-decided trims cover it.
- **Reading two:** the same under-read applies to `cut-pending-frame`, whose hint states the same three mutually exclusive cases and which `lint.json` prices at **0 decisions and the flat 6.0**, and to `cut-frames-tenth`, whose hint states two frame shapes plus an early-exit case and is also priced at 0 and 6.0. Session 2 is then three multi-rule blocks charged 19.9 minutes between them, against a project history of 45, 45, 45, 50, 47 and a model whose worst known error is 5.1.
- **Why it matters:** this is a re-raise of round 2's **B5**, and it is deliberately weaker than B5 was. B5's arithmetic complaint is closed and should stay closed: the hand-added 3 minutes is gone with a reason that is true (every cut is in `lib/`, no session types markup), and both trims are now *decided* with a named block and a clock trigger rather than offered, which is what why.md asked for and what the pipeline-test-03 lesson requires - both trims are code a student would otherwise type, so both recover real minutes. Round 2 put B5 at *worth a look / nothing*; I keep it at worth a look and move the owner to `pack-writer`, which is a move toward an owner rather than away from one - the Pack Writer prices the session at step 9 from the plan it has just written and beat this model 5:1 on the only out-of-sample measurement, and a person reads its number at Gate 3. Nothing here needs the spec to change; it needs the step-13 note to record whether either trim was pulled, which two consecutive dry runs failed to do. Worth noting alongside it: the idea's risk section asked for the tenth-frame cut to be its own cut **inside session 2**, and the spec keeps it as its own cut but in session 1. The spec gives two reasons - `frames()` must be whole for the grid to render, and E113 forbids relieving session 2 by moving a cut into the setup session - and both are correct, so I am not raising the drift separately.
- **Suggested wording:** none for the spec. One sentence in the Gate 1 note instead: session 1's `cut-frames-tenth` and session 2's `cut-pending-frame` are each priced at the flat 6.0 on 0 stated decisions while stating three cases, so read 38.8 and 37.4 as floors and ask the Pack Writer at step 9 before believing either.

### B5 - "scores not yet computed" is a state of the skeleton, and spec.json lists it as a state of the screen
- **Where:** spec.md, Screens, States; spec.json `screens[sc-game].states[0]`
- **Owner:** pack-writer
- **The line:** "**scores not yet computed** - `lib/score.ts` unfilled: boxes and symbols render, every score cell is empty, and `game-total` reads `-1`."
- **Reading one:** a session-1 milestone, described so the instructor knows what the student should be looking at, with the mechanism spelled out.
- **Reading two:** a state of `sc-game` that a test could be written against, which is what `screens[].states` is for. It cannot hold in the finished app, where `lib/score.ts` is complete, and it holds in the skeleton only while `cut-score-lookahead` and `cut-game-total` are both open.
- **Why it matters:** this is round 2's **B3** on the same line, and I classify it exactly as round 2 did - worth a look, owner `pack-writer` - so there is no move to justify. What changed is that the description is now *correct*: round 2's fallbacks put `0` in every cell, so B3's complaint was that the state was unreachable; round 3 declares `cut-score-lookahead`'s fallback as `null`, which makes empty cells and a `-1` total the real appearance of the open skeleton, and the state is renamed and explained. why.md did not require this fix and the spec made it anyway. What remains is only the mismatch of kind: `coverage.json` is keyed by criterion and no criterion touches this state, so nothing forces a test, but the state list is what the Test Writer reads for the screen and a test written for it would be red at step 7 against correct code. The place it actually lands is session 1's guide telling the instructor what should be on screen, read by a person at Gate 3 and again at the dry run.
- **Suggested wording:** keep the paragraph and mark the state for what it is - "scores not yet computed (skeleton only)" - so nothing downstream reads it as an app state.
