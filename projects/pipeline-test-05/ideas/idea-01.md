# Hunk

**One line:** Two versions of the same file shown side by side, aligned by a
longest-common-subsequence table the student fills in, with the changes grouped
into hunks with two lines of context.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A diff is not "compare line 1 with line 1". Two files stay in step for a page,
slip by one inserted line, and every naive comparison is wrong from there on.
The only honest way to line them up is to find the longest run of lines they
share, and that is a table - the first two-dimensional dynamic-programming
table in the track. The payoff is unusually visual: the moment the recurrence
is right, the two columns snap into alignment on screen.

## Sessions

1. **Setup, the revisions, and the table.** Types, `data/revisions.json` with
   four before/after pairs given as line arrays - one pure insertion, one pure
   deletion, one where a block near the top shifts everything below it, and one
   pair sharing no line at all - `lcsTable(a, b)` returning the
   `(m+1) x (n+1)` matrix of common-subsequence lengths, `GET /api/revisions`,
   and `/revisions/[id]` rendering both versions in two columns, one
   `data-testid` per line, above the reported length of the common subsequence.
   **Runs:** four pairs render side by side and each reports how many lines it
   has in common.
2. **The edit script and the hunks.** `editScript(a, b, table)` walking the
   matrix back from the bottom-right into an ordered list of `keep` / `add` /
   `remove` operations, each carrying its line number in whichever file it came
   from; `hunks(script, context)` grouping consecutive changes with up to two
   unchanged lines either side and merging groups whose contexts touch;
   `POST /api/revisions/diff` taking two line arrays in the body and returning
   the script and the hunks. **Runs:** the columns align, added and removed
   lines are marked, and the long pair shows only its changed regions.

## What the student types

- `lcsTable` - the row and column of zeros, and the two-branch recurrence
  (equal lines add one to the diagonal, unequal take the better neighbour).
- `editScript` - the backwards walk, and the tie-break when up and left are
  equal, which has to be stated rather than discovered.
- `hunks` - the grouping window and the merge rule for two changes three lines
  apart.

## What this teaches that the shipped projects do not

The first algorithm in the track whose answer is an *alignment* rather than a
number, and the first that builds a table and then reconstructs a path out of
it. Sweeper's flood fill had a frontier and a visited set but no table and
nothing to reconstruct; every shipped project folds a list forwards once. Being
honest about the overlap: reading values out of nested arrays is not new -
filling them in, and walking back through them, is.

## Out of scope

- Character-level or word-level diff inside a changed line. Lines are atomic.
- Three-way merge, conflict markers, applying a patch, unified-diff text output.
- Detecting a moved block as a move. A move is a delete plus an add, and the
  seed includes one so the spec can say so.
- Uploading or editing files. Versions come from the seed or the POST body.

## Risks

`lcsTable` is one uninterrupted block of live coding and this is the shape that
has overrun five projects in a row, so session 2 must be two separate cuts
(`editScript`, `hunks`) with the two-column markup shipped written, and the
named drop candidate should be the hunk merge rule - which a student actually
types - not the layout. Second: the tie-break in the backwards walk decides
whether an equal-cost edit reads as add-then-remove or the reverse, and if the
spec leaves it open the Builder and the Verifier grade two different scripts
that both look correct. Third: the pure-insertion pair is satisfied by matching
lines positionally, so the shifted-block pair is the load-bearing fixture and
`lcsTable` needs at least it plus the no-common-line pair.
