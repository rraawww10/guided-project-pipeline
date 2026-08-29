# Recalc

**One line:** A 5x5 sheet where a cell holds a number or a formula, and the
student writes the evaluator - dependency order, error propagation, and the
circular reference that has to be caught instead of looped.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A spreadsheet looks like a grid and behaves like a graph. `=A1+B2` means B3
cannot be computed until A1 and B2 are, and the moment a student writes the
obvious recursive `valueOf(cell)` they have also written an infinite loop -
because one seeded sheet contains `A1 -> B1 -> A1` on purpose. Fixing that is the
lesson: a visiting/visited walk that both orders the work and names the cycle.
The grammar is deliberately tiny so the parser is a warm-up and the graph is the
main event.

## Sessions

1. **Setup, the sheet, and the parse.** Types, three seeded sheets,
   `GET /api/sheets`, and `/sheets/[id]` rendering a 5x5 grid of each cell's raw
   contents plus a formula bar for the selected cell. The work is
   `parseFormula(text)`: a formula is `=` followed by terms joined by `+` or `-`,
   where a term is a number or a cell reference. No parentheses, no precedence,
   left to right. Text that does not fit the grammar, or a reference outside the
   sheet, becomes `#PARSE!`. **Runs:** a grid of raw text, and a panel listing the
   parsed terms of the selected cell.
2. **Evaluate, in order.** `refsOf(cell)` extracts the dependencies, including
   expanding a `SUM(A1:A3)` term into its range. `evaluate(sheet)` returns a value
   for every cell: dependencies first, an empty cell reading as 0, `#PARSE!`
   propagating to everything downstream, and `#CYCLE!` for cells the walk re-enters
   while still visiting them. A toggle flips the grid between raw and computed.
   `POST /api/sheets/[id]/cell` writes one cell's raw text and returns the whole
   recomputed sheet. **Runs:** edit a cell, see its dependents change; the cyclic
   sheet shows `#CYCLE!` in exactly the cells the spec names.

## What the student types

- `parseFormula` - the split on the sign characters, the reference pattern with
  its bounds check, and the decision to reject rather than throw.
- `refsOf` including range expansion, which is the only place two coordinates
  have to be walked between.
- `evaluate` - the three-colour walk. Ordering and cycle detection fall out of
  the same traversal, which is the point worth 40 minutes.

## What this teaches that the shipped projects do not

In recipe-box, tip-split and habit-tracker every computed value depends only on
stored data, so the order the work happens in never matters. Here one computed
value depends on another the student also computes, and getting the order wrong
gives a stale answer rather than an error - the hardest kind of bug to see. It is
also the first project in the track with an error *value* that flows through the
data rather than an error response that ends the request, and the first place a
student writes code whose failure mode is a hang.

## Out of scope

- Operator precedence, parentheses, multiplication and division. Plus, minus and
  `SUM` are the whole grammar, and that is deliberate.
- Any function beyond `SUM`, string values, dates, and formatting.
- Inserting rows or columns, resizing the sheet, or sheets other than 5x5.
- Multi-cell selection, copy and paste, fill handles, undo.

## Risks

Scope creep into a real expression parser is the obvious overrun, so the spec has
to close the grammar as a list of what is accepted and state that everything else
is `#PARSE!`. Second, `#CYCLE!` needs an exact rule for *which* cells receive it -
the members of the cycle only, or the members plus everything downstream - or the
Builder and the Verifier will disagree and only the criterion text will say who
was right. Third, `POST` writes to the JSON store, so the spec must say how the
seed is restored between tests, or the suite passes once and fails on the rerun
the nightly watchdog does.
