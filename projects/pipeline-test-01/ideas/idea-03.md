# Sweeper

**One line:** Minesweeper on three fixed, hand-authored boards - the student
writes the neighbour count, the flood-fill reveal, and the win/lose rule.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 3 x 40 minutes.

## Theme

The boards are seed data, not random, so every game is the same game and every
test gives the same answer twice. What is left is the algorithm: count the mines
touching each cell, and when a student clicks a zero, open the whole connected
region of zeros plus the numbered cells fringing it. That flood fill is the first
recursion in the track that has a real reason to exist, and getting its boundary
rule wrong is visible instantly on screen.

## Sessions

1. **Setup, boards, and the solved view.** Types, three seeded boards (a 5x5, an
   8x8, and a 4x4 whose mines sit in one corner), `GET /api/boards` and
   `GET /api/boards/[id]`, and `/boards/[id]` rendering every cell face-up: a mine
   glyph or the neighbour count. The work is `neighbourCounts(width, height, mines)` -
   the eight-way scan with edge clamping. **Runs:** three fully-revealed boards.
2. **Reveal and flood fill.** `revealFrom(board, index)` returns the set of cells
   a single click opens: the cell itself, and if it is a zero, every zero reachable
   through orthogonal and diagonal neighbours plus the numbered cells bordering
   that region - but never recursing *through* a numbered cell. Cells render face-
   down until revealed; clicking a mine reveals it. **Runs:** one click on a
   corner zero opens 14 cells at once.
3. **Flags, status, and replay.** A flag-mode toggle, a remaining-mines counter,
   and `gameStatus(board, revealed, flagged)` returning `playing`, `won` (every
   non-mine cell revealed) or `lost`. `POST /api/boards/[id]/replay` takes an
   ordered list of clicks and returns the final revealed set and status.
   **Runs:** a board can be won, a board can be lost, and both can be replayed
   from a list of moves.

## What the student types

- `neighbourCounts` - the eight-offset scan and the edge cases at corners.
- `revealFrom` - the queue or recursion, the visited set, and the boundary rule
  that a numbered cell is revealed but not expanded.
- `gameStatus` - the win condition expressed as "revealed count equals cells minus
  mines", which is deliberately not "all mines flagged".

## What this teaches that the shipped projects do not

habit-tracker has a grid, but it only renders two nested arrays. Here the grid is
a graph: neighbours, a frontier, a visited set, and a termination condition. It is
also the first project in the track where a pure function returns a *set* whose
membership tests care about ordering-independence, and the first with an
adversarial edge case (the corner, the wall, the region touching itself).

## Out of scope

- Random board generation. Randomness would break repeatable tests; the boards
  are authored.
- Difficulty selection, timers, best scores, or anything counting elapsed time.
- Right-click / context menu. Flagging goes through an explicit mode toggle so a
  test can drive it with a plain click.
- Saving progress. Reveal state lives in React state and dies with the page,
  except through the replay endpoint.

## Risks

Session 2 is the whole project's weight in one function, and a flood fill that
recurses through numbered cells looks *nearly* right on a sparse board - so the
seeded boards must include one where the two behaviours differ by a large,
countable number of cells. Second risk: the reveal set must be graded by count
plus a few named cells, not by array equality, or the criterion pins an
implementation's traversal order.
