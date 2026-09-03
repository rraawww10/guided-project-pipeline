# Pegs

**One line:** A code-breaking board where each guess comes back scored as exact
and near matches under a repeat rule that breaks every first attempt, and the
student then writes the filter that lists which codes are still possible.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Mastermind's scoring function looks like two lines and is not. As soon as a
colour appears twice in the guess and once in the secret, counting matches by
membership double-counts it, and the board silently lies for the rest of the
game. Once scoring is right it earns its keep twice over: the same function,
run backwards over the guesses already played, answers "which of the 1296 codes
could still be the secret?" - so the student uses their own function as a
predicate on its own output space.

## Sessions

1. **Setup, the boards, and the score.** Types, `data/games.json` with four
   games - each a hidden 4-peg secret from 6 colours plus the guesses already
   played - chosen so that one game has no repeated colour anywhere, one has a
   secret that repeats a colour, one has a guess repeating a colour the secret
   holds once, and one is already solved on its last row. `score(secret, guess)`
   returning `{ exact, near }` by the two-pass rule: count exact positions
   first, then tally the leftovers by colour and take the smaller count per
   colour. `GET /api/games` (scores and rows, never the secret), and
   `/games/[id]` rendering each played row as colour pegs plus score pegs, one
   `data-testid` per row. **Runs:** four boards render their history correctly,
   and the repeat fixtures visibly disagree with the naive one-pass version.
2. **Guessing and what is left.** `allCodes()` generating all 1296 codes,
   `candidates(history)` keeping every code that would have produced every
   score already recorded, and `status(history)` returning `won` on four exact,
   `lost` after ten rows, else `playing`. `POST /api/games/[id]/guess` takes the
   player's whole guess list in the body, scores each row against the hidden
   secret, and returns the rows, the status and the remaining-candidate count -
   nothing is written, so the seed stays constant and criteria stay
   order-independent. 400 on a malformed guess, 409 on a guess past a finished
   game. **Runs:** add a row, see it scored, and watch the possibilities fall
   from 1296.

## What the student types

- `score` - the two passes and the leftover colour tally, which is the whole
  point of the project and the thing nearly everyone gets wrong once.
- `allCodes` - four positions over six colours as a fold (or a recursion), 1296
  rows, generated rather than stored.
- `candidates` - `score` used as a predicate: keep `s` only if
  `score(s, g)` equals the recorded score for every guess `g` in the history.

## What this teaches that the shipped projects do not

Two things. Multiset counting - no shipped project has ever had to reconcile
two bags of the same items, and `near` is exactly that. And inverting a
function: asking "if this were the answer, would the evidence match?" over an
enumerated space. recipe-box filtered stored records by a substring; here the
search space is generated and the filter is the student's own function from
session 1, so a bug in it is visible twice.

## Out of scope

- Solver strategy. No minimax, no next-best-guess suggestion, no hints beyond
  the candidate count.
- Code lengths, colour counts or row limits other than 4 / 6 / 10.
- Starting a new game or persisting a played one. Guesses live in React state
  and are posted as a list.
- Timers, scores, difficulty levels, animation.

## Risks

The repeat rule has to be written as a closed procedure, not as "count colours
in the wrong place", or the Builder and the Verifier will grade different peg
counts on the two repeat fixtures. Second: a criterion pinning a
remaining-candidate count is only meaningful against a named history, so the
spec must fix the history each count is measured after, or a seed edit moves
every number. Third: session 2 carries two cuts plus an endpoint - `candidates`
is small once `score` exists, and `allCodes` is the honest drop candidate
inside its own session, since the count can be graded against a shipped
generator if time runs short.
