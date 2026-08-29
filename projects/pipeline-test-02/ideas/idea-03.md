idea 3

**One line:** A nonogram board you fill by clicking, where the run-length clues
down the top and the side tick green one line at a time until the picture is
declared solved.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A nonogram grid is read twice: once by row and once by column, by the same rule.
That makes it an unusually honest teaching object - write `runsOf` correctly and
it grades both directions, write it carelessly and half the board lies. The clues
are not authored in the seed; they are *derived* from the solution at load, so a
student cannot fudge one to match a bug. The reward is immediate and visual: a
clue strip turning green the moment its line is right.

## Sessions

1. **Setup, the boards, and the clues.** Types, three seeded puzzles stored as
   solution grids (a 5x5, an 8x8, and a 5x5 containing one completely empty row
   and one completely full row), `GET /api/puzzles`, and `/puzzles/[id]` rendering
   an empty playable grid with the clue strips down the top and the left. The work
   is `runsOf(cells)`: the run-length encoding of a line, plus the transpose that
   turns rows into columns so one function produces both strips. **Runs:** three
   boards showing correct clues, derived rather than stored.
2. **Filling, checking, and solved.** A click cycles a cell empty -> filled ->
   crossed-out -> empty, so cell state is three-valued and cannot be faked with a
   boolean. `lineStatus(cells, clue)` returns `satisfied`, `open` or `violated`
   under a rule the spec closes exactly. `boardSolved(grid)` is true when every
   row and every column is satisfied. `POST /api/puzzles/[id]/check` takes a grid
   and returns per-line statuses plus the solved flag. **Runs:** fill a board,
   watch clues go green, get a solved banner on the last cell.

## What the student types

- `runsOf` - the scan that collects consecutive filled cells, and the two cases
  that break naive versions: a run ending at the last cell, and an empty line
  whose clue is `[0]`.
- `transpose` - four lines that let session 1's row logic grade the columns.
- `lineStatus` - the three-way answer, including the cheap violation test
  (crossed-out cells already split the line into more pieces than the clue has,
  or a completed run is longer than the clue allows).

## What this teaches that the shipped projects do not

habit-tracker has a grid, but it only renders two nested arrays and every cell is
independent. Here a cell participates in two overlapping constraints at once, and
the same pure function evaluates both axes - so a student meets transposition as
a way to reuse code rather than as a puzzle. It is also the first three-valued
cell state in the track, and the first derived-not-stored seed: the clues are
computed from the answer, so the fixture cannot disagree with itself.

## Out of scope

- Solving, hinting, or auto-filling forced cells. The student solves by hand.
- Creating or editing puzzles, and any board larger than 8x8.
- Timers, scores, undo history, and saving progress between page loads.
- Colour nonograms. Cells are filled or not.

## Risks

The boundary between `open` and `violated` is arguable, and an arguable rule is
how the Builder and the Verifier end up grading different things. The spec must
state the violation test as a closed list of conditions, and the criteria must
include one line that is wrong-but-still-open and one that is genuinely
violated. Second risk: `runsOf` graded against one line can be a hardcoded array,
so it needs at least the empty row, the full row, and a two-run line. Third: the
grid must carry a stable `data-testid` per cell, or every criterion is pinned to
markup the student is about to rewrite.
