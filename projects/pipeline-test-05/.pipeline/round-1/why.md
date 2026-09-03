# Round 1

Gate 1: rejected
Note: Round 1 rejected on B1 and B2 only. Both are blocking and owned by nothing.

The spec is mechanically strong and round 1 got a lot right: linter 0 errors / 0
warnings first try, all four runUntil traces re-derive correctly from the ordered
procedure, all five cuts turn one of their own criteria red when opened alone,
the five cut signatures are pairwise distinct, and ALL THREE Gate 0 risks are
answered - the passing-order policy is now a closed ordered procedure. Keep all
of that. This is a revision, not a rewrite.

STOPPING RULE for round 2: approve when every finding sits in a column a
downstream checker owns, and no blocking finding is owned by 'nothing'.

FIX EXACTLY THESE TWO:

1. B1 (blocking, owner nothing) - the `overtake` scenario seeds {floor:8,tick:0}
   before {floor:5,tick:2}. Because `live` is a filter it preserves array order,
   so a student writing `ahead = live` - no direction filter, no ordering -
   reproduces every pinned trace byte for byte and passes all twelve criteria.
   The same accident hides the tie rule, since both-sides is seeded floor 2
   before floor 6. Both rules inside the cut whose whole justification is
   `overtake` are therefore graded by nothing.
   FIX, as the Breaker states it and no more: reorder the two seed rows. The
   correct traces are unchanged; the wrong reading turns c-2-2 and c-2-1 red.
   Do not add a criterion for this.

2. B2 (blocking, owner nothing) - the only `direction` values any criterion
   asserts are `up` and `null`, so no criterion ever observes a downward-moving
   car and `direction: 'up'` unconditionally is green everywhere. Session 1 does
   not help: manualStart aims up in both `above` and `passing`.
   FIX: add the tick-5 floor-8 `direction: 'down'` row - already present in the
   pinned `overtake` table, so no new numbers are being invented - to c-2-2, and
   state that `step` advances by `car.direction` rather than by
   Math.sign(target - floor).

RECORDED, NOT FIXED - deliberately kept, all of round 1's worth-a-look findings:
  W1 cut-dispatch-target's ahead-empty reversal branch is unreachable (nothing)
  W2 cut-step-doors graded by one criterion on one served call (nothing)
  W3 the maxTicks/complete boundary is unstated and unreachable (nothing)
  W4 shaft display order and the tick readout are stated but ungraded (nothing)
  W5 three skeleton locals unused once the cuts are open (typecheck)
  W6 the idea's visible-trace payoff ships as JSON only (pack-writer)
  W7 session load: largest_cut_share 0.56 on session 1, which the share check
     structurally skips at two cuts; the spec discloses the risk itself and both
     drop candidates are real blocks a student types
B3 is blocking but owned by test-runner - the Builder/test-runner loop hits it at
step 7 for free. Do not pre-fix it.

Do not add spec sentences that assume pipeline capabilities. Ask only for wording
the existing checkers already read.
