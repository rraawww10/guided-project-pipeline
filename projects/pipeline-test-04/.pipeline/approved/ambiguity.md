# Ambiguity report - pipeline-test-04

**Verdict:** 0 blocking, 4 worth a look

Round 4. Read in the required order: `spec.md` and `spec.json` alone, then
`idea.md`, then `learning/lessons.md`, and only after my own pass round 3's
`ambiguity.md`, `gate1.json` and `why.md`. Bound to spec hash
`eb17a8732739de51bb84d2adcb376a92da23df5245201ad719aaa84359f2bc64` - the hash
`.pipeline/breaker-begin.json` recorded and the same hash `lint.json` carries.

**What I re-derived by hand before reading anything else.** All four frame
splits, all four cumulative arrays and all four totals are correct, including
`g-mixed`'s tenth frame scoring 16 by the spare rule (`rolls[18]` = 6) and
`g-perfect`'s scoring 30 by the strike rule off its own second and third rolls,
so "the tenth frame needs no special rule" holds for every legal game and not
only for the fixtures. `g-partial` splits into six frames with the scan hint as
written (i reaches 10 = `rolls.length` after frame 6) and frames 5 and 6 are
both pending because a frame's highest required roll index is non-decreasing in
the frame number - so "null from the first pending frame onwards" is a property
of the algorithm, not an extra rule someone has to remember. `frames([])` is
`[]`, `scoreGame([])` is `[]`, `gameTotal([])` is 0, which is what c-2-5 wants.
Every "fails alone on" cell in the Grading integrity table checks out, including
the two non-obvious ones: with `cut-frames-scan` open and `cut-frames-tenth`
filled, `i` is still 0 and the tenth block appends the whole roll list as one
frame, so c-1-3 sees one frame where it wants six; and with `cut-pending-frame`
open, `gameTotal` returns `NaN` rather than 34, which is what fails c-2-4.
The Session load table reproduces `lint.json` exactly (38.8 / 37.4; 7.8, 6.0 /
7.9, 6.0, 6.0). E110 holds - all five cut signatures are distinct. E113 holds
(2 cuts in the setup session against 3). W114 does not fire and the spec's
reason is the real one: `SHARE_MIN_CUTS` is 3 in `spec_linter._check_cut_share`,
so session 1's 56% share is not measured. `code_checks` is absent, which the
spec states plainly, so nothing here may be owned by `code-check`.

**Round 3's single blocking finding is genuinely fixed, and fixed where it was
asked for.** `cut-score-lookahead`'s bullet now states that the block applies
the three arithmetic rules unconditionally and never tests the length of
`rolls`, that `pendingFrame` is the only place the end of `rolls` is checked and
that `scoreGame` pushes `null` for a frame it reports pending; Grading integrity
states the dependency where the guarantee is made and names the alternative
implementation that would have made the cut ungradable; `cut-pending-frame`'s
bullet no longer makes its c-2-3 behaviour conditional. `spec.json` is unchanged
from round 3 - I checked every criterion id, every `check` string, every cut id,
`writes_into` and `hint` against `.pipeline/round-3/spec.json` and they are
identical, line for line, so the lint numbers a person read at round 3 are the
numbers in front of them now. Nothing in rounds 1-3 has been undone.

Four findings follow. None is blocking. Two are on text unchanged since round 3
that round 3 did not raise, and I say so rather than presenting them as new
damage; one is created by the shape of round 4's own fix; one is a false clause
in a hint. Round 3's five worth-a-look findings are recorded in `why.md` as
deliberately kept, and I have no new evidence on any of them - they are listed
as adjudicated at the end rather than re-raised.

## Blocking

None. Every place a Builder has to decide something is now decided in the spec,
and the one place where a *student* can still take a wrong turn is B1 below,
which I did not classify as blocking for the reason given in that finding.

## Worth a look

### B1 - the decision about where the end-of-`rolls` test lives is in `spec.md`, and the student only ever reads the hint
- **Where:** spec.json `cuts[cut-score-lookahead].hint` and `cuts[cut-pending-frame].hint`; spec.md, Session 2 cut points and Grading integrity; criteria c-2-3, c-2-4, c-2-6
- **Owner:** nothing
- **The line:** "Set `frameScore` to what this frame is worth: 10 plus the next two entries of `rolls` for a frame that opens with a 10, 10 plus the single entry after the pair for a frame whose two rolls add to 10, and the frame's own two rolls added together for anything else. Index into `rolls` at `i`, never into `frameList`."
- **Reading one:** the student reads this hint together with `pendingFrame`'s, fills both as written, and gets the design the spec decided: the block scores unconditionally, `pendingFrame` decides whether the score is allowed to exist.
- **Reading two:** the student fills `cut-score-lookahead` first, runs the suite, and sees c-2-1, c-2-2 and c-2-3 green with c-2-4 ("expected 34, got NaN") and c-2-6 ("NaN" in `total-5`) red. The obvious diagnosis is right - the arithmetic read past the last roll - and the obvious place to fix it is the block the arithmetic is in. A length guard there turns `frameScore` `null`, which is legal: it is declared `number | null`. c-2-4 and c-2-6 then go green with `cut-pending-frame`'s TODO still in the file, and the student has been told by the tests that they are finished with a task they never wrote.
- **Why it matters:** this is round 3's A1 (blocking, owner `nothing`) *for the student* rather than for the Builder. The Builder half is genuinely closed, and closed by a script: `mutation.py` builds "a student who has done everything except this one" per cut and requires at least one of its `graded_by` criteria to go red (`mutation.py:192`, rule at `:222`), so a `lib/score.ts` with the guard in the wrong block fails step 8 with `ungraded_tasks: ["cut-pending-frame"]`. What no step sees is student code - nothing in the pipeline ever grades a student's variant - so the constraint has to reach them as text, and the only text they get is the hint, which is byte-identical to round 3's and says nothing about not testing the length of `rolls`. I am **not** calling this blocking: no Builder has to guess (spec.md decides it unambiguously and step 8 enforces it), the student under reading two has still written the guard rather than skipped the idea, and no wording change could make the student side *owned* by anything - the gap is structural to a pipeline that grades `app/` and not the learner. It is worth a look because the cheapest possible fix sits in the artifact that actually reaches them, and because the task that can be skipped is the one carrying the project's whole point.
- **Suggested wording:** add one clause to `cut-score-lookahead`'s hint - "Do not test the length of `rolls` here; `pendingFrame` is where a missing bonus roll is caught." Note for the Spec Writer if this is taken: it lengthens the hint past the 55-word nominal, so session 2's estimate moves by a fraction of a minute and `lint.json` has to be re-read.

### B2 - the step from `frameScore` to the cumulative array is unwritten, and the declared appearance of the open skeleton depends on it
- **Where:** spec.md, Outcome (`scoreGame`), Session 2 Builds, Screens ("scores not yet computed"); spec.json `cuts[cut-score-lookahead]`, criteria c-2-1, c-2-2
- **Owner:** nothing
- **The line:** "With this block open, every frame scores `null`, so the whole cumulative array is `null` and c-2-1, c-2-2, c-2-3, c-2-4 and c-2-6 go red."
- **Reading one:** the shipped wrapper around the cut reads `pending ? null : (running += frameScore, running)` and additionally treats a `null` `frameScore` as a `null` entry. Then the open skeleton behaves exactly as Screens describes: every score cell empty, `game-total` reading `-1`.
- **Reading two:** the wrapper only branches on `pendingFrame`, because that is the only branch the spec names ("`scoreGame` pushes `null` for a frame it reports pending"). `running += frameScore` does not compile against `number | null`, so the Builder writes `frameScore ?? 0` or `frameScore!` to satisfy `tsc` - both correct in the finished app, where the block always assigns a number. On the open skeleton they make every cumulative entry `0`, so session 1's screen shows a column of zeroes where the spec says empty cells, and `game-total` still reads `-1` because `gameTotal`'s own fallback is untouched.
- **Why it matters:** no graded value moves. c-2-1 and c-2-2 pin the cumulative arrays, so any real error in the accumulation is red at step 6 in the Builder loop; the open skeleton fails the same five criteria under both readings, so `skeleton-check` and `mutation` report what they expect; `[0,0,...]` is not `[30,60,...]`. What is unowned is the *description*: "boxes and symbols render, every score cell is empty" is what session 1 is declared to end on, what the Pack Writer will write into session 1's guide, and what the instructor will look at on screen - and it is true only under reading one, which the spec never states. This is not round 3's B5 (that one is about `screens[].states[0]` naming a skeleton-only state, and is adjudicated); it is about whether the state as described is the state the skeleton produces. The text is unchanged since round 3 and round 3 did not raise it - there all along and missed, by me as much as by anyone.
- **Suggested wording:** one clause where the cut is described - "`scoreGame` pushes `null` both for a frame `pendingFrame` reports pending and for a frame whose `frameScore` is still `null`, which is what makes every score cell empty on the open skeleton."

### B3 - "one box per entry `frames()` returned" is graded only where the answer is ten
- **Where:** spec.md, Screens; spec.json `screens[sc-game].elements`, criteria c-1-3, c-1-4, c-2-6
- **Owner:** nothing
- **The line:** "One frame box and one score cell are rendered per entry `frames()` returned, so `g-partial` renders six of each and no element with `data-testid` `frame-7`."
- **Reading one:** the page maps over `frames()`, so `/games/g-partial` renders six boxes and six cells. This is the natural implementation and almost certainly what gets built.
- **Reading two:** the page renders a fixed ten-box, ten-cell grid and fills what it has. Every criterion still passes: c-1-4 wants ten boxes on `g-perfect`, c-1-5 reads texts in `frame-1` to `frame-10` on `g-mixed` (ten frames), c-1-2 and c-1-3 grade the endpoint and not the page, and c-2-6 reads `total-1` to `total-4` and requires `total-5` and `total-6` to hold no text - which a padded grid satisfies, along with four more empty cells nobody looks at. `g-partial`'s page then ships with four empty frame boxes.
- **Why it matters:** this is the class `learning/lessons.md` counts six times - a rule the spec states that no criterion grades - and there is nothing downstream to lean on: the Test Writer writes from criteria, so no test asserts a frame count on a short game, and `frame-7`'s absence is asserted for no game at all. The same hole covers the `no-game` element from the other side: `screens[sc-game].elements` says it holds its text "when the id is not in the seed", and no criterion asserts it is *absent* on a valid game's page, so a page that always renders it passes c-1-6 and everything else. Both are cheap to close by extending an existing criterion rather than adding one. Present in the spec round 3 read, word for word (`.pipeline/round-3/spec.md:194`), and not raised then.
- **Suggested wording:** extend c-2-6 - "...and renders no element with `data-testid` `frame-7` or `total-7`" - which grades the short-game grid on the page without a new criterion.

### B4 - the scan hint states a consequence that is false for most 10-roll games
- **Where:** spec.json `cuts[cut-frames-scan].hint`; spec.md, Session 1 cut points, criterion c-1-3
- **Owner:** nothing
- **The line:** "Stop as soon as `rolls` runs out, so a 10-roll game leaves `out` with 6 entries."
- **Reading one:** "a 10-roll game" means the 10-roll game in the seed, `g-partial`, whose last two frames are strikes - and for that one the arithmetic is right: six entries.
- **Reading two:** it is a general statement about the scan. It is not: ten rolls of open frames leave five entries, and `POST /api/games/score` accepts any array of numbers, so ten-roll games with five frames are a legal input the student can send in the same session.
- **Why it matters:** small, and it changes nothing that ships - c-1-3 grades `g-partial` at six frames and a correct scan passes it, so no Builder or test author is misled into different code. It matters because this sentence is the worked example in the one piece of text the student reads while writing the hardest block of session 1, and it is the sentence they will check their own output against. Six is a property of `g-partial`'s two trailing strikes, not of ten rolls. The hint is byte-identical to round 3's and was not raised then.
- **Suggested wording:** "Stop as soon as `rolls` runs out, so `g-partial`'s ten rolls leave `out` with 6 entries."

## Already adjudicated - recorded in round 3's why.md, not re-raised

`why.md` records all five of round 3's worth-a-look findings as deliberately
kept, and says that raising one again needs new evidence. I have none for any of
them. For the record, each line is unchanged and my own reading agrees with the
round-3 classification:

- **round 3 B1** (`i`'s convention stated in the Outcome and in neither hint,
  owner `test-runner`) - unchanged. I confirmed the Outcome's "advances `i` by
  the length of each frame" is consistent only with `i` being the frame's first
  roll, and that both hints work under that reading. Two hints disagreeing makes
  `g-mixed` wrong from frame 3, which c-2-2 catches at step 6. Kept.
- **round 3 B2** (a roll list stopping part-way through a frame, owner
  `nothing`) - unchanged. All four seeded games end on a whole frame and both
  readings answer 200, so no graded value depends on it. Kept.
- **round 3 B3** (the unknown-id page's score cells and `game-total`, owner
  `nothing`) - unchanged. c-1-6 passes under both readings; the cost is a
  cosmetic `-1`. Kept. My B3 above is a different property of the same screen -
  the frame count on a *short* game - and cites different criteria.
- **round 3 B4** (the minute model reading 0 decisions on `cut-frames-tenth` and
  `cut-pending-frame`, owner `pack-writer`) - unchanged, and `lint.json`
  confirms the numbers: `decisions` is 0 on three of the five cuts while their
  hints state three cases each. Read 38.8 and 37.4 as floors, as why.md says.
  Kept, and I add nothing to it.
- **round 3 B5** ("scores not yet computed" listed among the screen's states,
  owner `pack-writer`) - unchanged. Kept. My B2 above is about whether the state
  as described is what the skeleton produces, not about what kind of thing it is.

Round 3 also considered and declined to raise the idea's request that the
tenth-frame cut live "inside session 2", on the grounds that `frames()` must be
whole for the grid to render and that moving a cut into the setup session is
E113. I read it the same way and am not raising it either; the spec states the
deviation and its two reasons in the open, where the person at Gate 1 sees them.

## For the person at Gate 1

One thing about the harness rather than the spec, reported and not acted on, per
rule 5. The `Owner` vocabulary has no name for `mutation.py`, and `mutation.py`
is the script that actually owns the claim the Grading integrity table makes:
"which criterion fails if only this cut is left empty" is exactly its
leave-one-out rule, "every student task must turn at least one of its
requirements red when it alone is removed". Round 3's A1 - the finding this
round exists to fix - would have been caught at step 8 by it, in `app/`, before
any student saw the skeleton; it was correctly reported as owned by `nothing`
because `nothing` is the strictest reading of a name the list does not contain,
and the strictest reading of a missing name is what the rule asks for. That cost
one round. Two consequences worth deciding between rounds, by a person, in the
pipeline and not in a spec: whether `mutation` belongs in the `OWNERS` table
(with the same "what does it say when it cannot run" question asked of it - it
reports `inconclusive`, not `ok`, when no criterion passes, which is the right
answer), and whether the Grading integrity table's hand-checked last column
should simply cite `mutation.json` instead. I have not touched `pipeline/` or
`.claude/`.
