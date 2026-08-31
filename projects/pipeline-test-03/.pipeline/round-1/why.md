# Round 1

Gate 1: rejected
Note: GATE 1 REJECTED - round 1. Human decision, and the stopping rule agrees: 2 blocking findings, both owned by 'nothing'. Linter clean at 0 errors / 0 warnings.

Round 2 is a small, bounded revision. The spec's data is sound - the Breaker recomputed every paise value, all four account totals, both running-balance tables, the 21/6 accepted/rejected split and all six reason strings against the 30 seed lines and found no disagreement. Keep all of it. This is a revision, not a rewrite.

FIX BOTH BLOCKERS - each is a cut that no criterion can tell from a version that was never written:

  A1  cut-amount-paise, session 1's headline cut, can be left at its TODO with
      all nine criteria green. cut-parse-line's markers span the whole body
      between 'let paise = 0' and the two returns, and nothing outside them
      calls amountToPaise, so a student who inlines the conversion passes
      everything. E110 does not catch it: it requires exactly equal criteria
      sets and these differ, 9 against 6. Fix by putting the amountToPaise call
      ABOVE cut-parse-line's opening marker so the cut cannot absorb it, or by
      adding a criterion that reaches amountToPaise on its own. Pin whichever
      you choose in spec.md, including where the marker sits.

  A2  sc-account defines account-total as formatPaise of the account's total
      'from accountTotals', but c-2-3 and c-2-4 declare no cut-account-totals.
      Two readings - the page calls accountTotals, or the total is the last
      runningBalance value - are both green on the full build and both red on
      the fully-open skeleton, so no checker separates them. State which one is
      the contract, and declare the cuts every criterion actually depends on.

ALSO CLOSE W6, which is A2's class: c-1-2, c-2-2 and c-2-4 omit cut-amount-paise
though none of them can pass while it is empty. A criterion's 'cuts' list is the
grading contract the mutation check reads - an omission there is a hole.

DECIDE, DO NOT SILENTLY DROP: W1 (the loading state and ledger-loading are
graded by nothing - grade it in c-1-4 or remove the element), W2 (the href on
account-link is the app's only navigation and session 2's closing demo, and
nothing grades it), W3 (account-entry- is a testid PREFIX of its four child
testids, so 'exactly 3 elements' counts 15 under a prefix locator), W4 (pin the
exact bytes of data/ledger.txt, and exclude the line-number gutter the way the
'<- broken:' markers are excluded).

W5 is accepted as written - shipping parseLedger already written is correct,
because making it a student task trips E113.

ON W7, AND READ THIS BEFORE TOUCHING A HINT: both sessions estimate 38.5 against
the 40 cap with no headroom, and the two flow-2 sessions that have been timed ran
45 and 50 against flat estimates of 32.5 and 37. Every cut in this spec came in
at 46-54 hint words against a 55-word nominal, with none over. Write each hint at
the length its cut honestly needs. Do NOT tune a hint's length to sit under the
nominal - the word count is a signal about the size of the work, and a hint
compressed to duck a threshold destroys the signal without making the session any
shorter. If a cut genuinely needs more than 55 words to state, that is the cut
telling you to split it.
