# Round 3

Gate 1: rejected
Note: Round 3 rejected on A1 alone - one clause, one paragraph.

Round 3 was a real improvement and none of it is in question: 6 findings against
10 in each of the two rounds before it, 1 blocking against 3, every one of round
2's four required fixes genuinely made, round 1's three fixes intact, and all
five cuts now declaring writes_into with hints that agree (lint 0 errors, 0
warnings). Do not undo any of it.

STOPPING RULE, unchanged: approve when every finding sits in a column a
downstream checker owns, and no blocking finding is owned by 'nothing'.

FIX EXACTLY THIS ONE THING:

A1 (blocking, owner nothing) - the Grading integrity guarantee for
cut-pending-frame rests on an implementation choice the spec never makes. The
spec says c-2-4 and c-2-6 catch an empty cut-pending-frame because an unguarded
lookahead yields NaN. But guarding the end of rolls inside cut-score-lookahead
is equally legal - frameScore is declared number|null and
noUncheckedIndexedAccess pushes a Builder that way - and then g-partial yields
[7,16,25,34,null,null], gameTotal returns 34, the page renders two empty cells,
and c-2-3, c-2-4 and c-2-6 ALL PASS with cut-pending-frame still empty. The task
grades nothing and ships into the skeleton with every gate green.

Apply the Spec Breaker's own suggested wording, which is what this brief asks for
and nothing more:

  1. In the cut-score-lookahead bullet, state: "the block applies the three
     arithmetic rules unconditionally and never tests the length of `rolls`;
     `pendingFrame` is the only place the end of `rolls` is checked, and
     `scoreGame` pushes `null` for a frame it reports pending".

  2. In the Grading integrity paragraph, add: "this is what makes c-2-4 and c-2-6
     fail when `cut-pending-frame` is empty" - so the dependency is stated where
     the guarantee is made.

Do not add a criterion, do not change any criterion, and do not move the guard to
a third place. Two named functions exist and the spec must assign the guard to
one of them; the Breaker's wording assigns it to pendingFrame.

RECORDED, NOT FIXED - deliberately kept for this round, all five of round 3's
worth-a-look findings:
  B1 the `i` convention shared by both session-2 hints (owner test-runner)
  B2 a short in-progress roll list behind the declared 200 (owner nothing)
  B3 the unknown-id page's score cells and game-total (owner nothing)
  B4 the minute model reading 0 decisions on two more cuts (owner pack-writer)
  B5 screens[sc-game].states[0] being a skeleton-only state (owner pack-writer)
If the next pass has genuinely new evidence on any of these it may still raise
it - being recorded here is not a gag, it is a record that a person read it and
chose to ship it.

Do not add spec sentences that assume pipeline capabilities. Ask only for wording
the existing checkers already read.
