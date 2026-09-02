# Round 1

Gate 1: rejected
Note: Round 1 rejected on A1 alone.

STOPPING RULE for round 2, declared now: approve when every finding sits in a
column a downstream checker owns, and no blocking finding is owned by 'nothing'.

FIX EXACTLY THESE THREE, change nothing else:

1. A1 (blocking, owner nothing) - apply the Spec Breaker's own suggested wording
   to c-2-6 verbatim: '/games/g-partial displays the exact text 7, 16, 25 and 34
   in the elements with data-testid total-1 through total-4, the exact text 34 in
   game-total, and leaves total-5 and total-6 empty'. No new criterion. The API
   scoring is already graded by c-2-1..c-2-5; this grades the rendered column.

2. A2 (blocking, owner test-runner) - state in one sentence where session 2's
   score cells get their numbers: the page calls scoreGame in process, or it
   POSTs its own route. The spec settles this for session 1 and goes silent for
   session 2. Same seam as A1.

3. B2 (worth a look, owner nothing) - the grading-integrity table claims c-2-3
   'fails alone' on cut-score-lookahead. That is false: an unguarded lookahead
   past the end of rolls gives NaN, JSON.stringify(NaN) is null, and c-2-3's
   body then matches byte for byte with cut-pending-frame still empty. Integrity
   survives via c-2-4/c-2-6 - correct the claim, do not add a criterion.

RECORDED, NOT FIXED: A3 (skeleton-check owns it at step 8), B4 and B6 (owned by
nothing, non-blocking, ship as written). B5's session load stays as-is; both
named drop candidates are blocks a student types.

Do not add spec sentences that assume pipeline capabilities. Ask only for
wording the existing checkers already read.
