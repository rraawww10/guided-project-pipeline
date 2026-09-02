# Round 2

Gate 1: rejected
Note: Round 2 rejected on A1 and A2, both blocking and owned by nothing.

Round 1's three items were all fixed correctly and stay fixed - c-2-6 now grades
the rendered score column, the page's data source is stated, and the c-2-3
integrity claim is corrected. Do not undo any of them.

STOPPING RULE, unchanged from round 2: approve when every finding sits in a
column a downstream checker owns, and no blocking finding is owned by 'nothing'.

FIX EXACTLY THESE FOUR, change nothing else:

1. A1 (blocking, owner nothing) - the frames hints tell the student to append to
   `frames`, but the value declared above the markers is `const out`. In
   lib/frames.ts the only `frames` in scope is the exported function, so
   frames.push is a type error on the student's first keystroke.
   This is now enforced by the linter, not by judgement: every cut must declare
   `writes_into` - the symbol the block assigns to - and the hint must name that
   same symbol in backticks. E121 if they disagree, E122 if writes_into is not a
   bare identifier, W068 if the field is missing. See CONTRACT.md, section
   "writes_into - the symbol the block assigns to".
   Declare writes_into on all five cuts and make each hint agree. Either rename
   the accumulator to `frames` or write `out` in the hints - both are acceptable,
   they just have to match. This also closes B1 (`pending` vs `pendingFrame`)
   and B2 (the scan index cut-frames-tenth needs, never declared), which are the
   same class.

2. A2 (blocking, owner nothing) - state in one sentence that scoreGame obtains
   its frames by calling frames(rolls), and must not chunk `rolls` itself. As
   written, one reading ships a written copy of cut-frames-scan's answer inside
   lib/score.ts with test-runner, skeleton-check and cutter all green. The hint's
   "never index into `frames`" implies it but never states it.

3. A3 (blocking, owner test-runner - but not solvable as written) - c-1-6 asks a
   server component for a 404 status AND the exact text
   'No game with id no-such-game'. Out of scope says "Any client-side
   interaction. /games/[id] is a server component". notFound() gives 404 but
   not-found.tsx receives no route params; a page rendering its own message
   returns 200. c-1-6 is also declared no-cut, so skeleton-check requires it
   green at step 8 too. This appeared in round 1 as B3 and was parked on
   test-runner both times - the Builder cannot satisfy it without breaking a
   stated constraint, so it is a spec decision, not a retry. Pick one: assert
   the 404 without the interpolated id, assert the text without the status, or
   move the criterion to an endpoint that can set both.

4. B5 - session 2 sits at 40.4 minutes against the 40 cap once the spec's own
   two adjustments are applied, and the linter passes silently because the
   adjustments are not in its model. Five consecutive projects have overrun and
   pipeline-test-03 measured 47 minutes on a 40-minute session 1. Decide the drop
   candidate in the spec now and say which block goes, rather than discovering it
   at the dry run.

RECORDED, NOT FIXED: B4 (the `-` gutter glyph and the seeded game order stated
and ungraded), B6 ("empty" not pinned against the markup), B7 (a non-JSON POST
body has no declared status). All owned by nothing, all non-blocking, all ship as
written unless you choose otherwise.

Do not add spec sentences that assume pipeline capabilities. Ask only for wording
the existing checkers already read.
