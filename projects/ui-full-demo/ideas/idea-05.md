# Tiny Diff: LCS‑Based Edit Script

**One line:** A split-view diff that computes a minimal edit script between two short texts via LCS and highlights inserts/deletes deterministically.

## Theme
Diffs are everyday tools built on dynamic programming. This project teaches the LCS table and a backtrack with explicit tie-breakers so the same inputs always yield the same edits. It’s a compact, high‑leverage algorithm exercise with a satisfying visual.

## Sessions
1. LCS length: two textareas at "/", build lcsTable(a, b) and show the LCS length. Keep inputs tiny and local; visualize the length only.
2. Backtrack and ops: add a deterministic backtrack to produce an edit script (keep, insert, delete). Add POST /api/diff that returns { ops } and render colored spans in the UI.
3. Line mode: add a toggle to diff by line (split on "\n") using the same algorithm, with tie-break rules fixed so output is stable across runs.

## What the student types
- lcsTable(a, b): a DP table fill that is O(n×m) with small, seeded inputs.
- backtrack(table, a, b): walk the table with fixed tie-breaks to emit an alignment.
- toOps(alignment): compress the alignment into { kind, text } runs for rendering.

## What this teaches that the shipped projects do not
- None of the shipped projects use dynamic programming with a table and a backtrack; this adds that shape and a deterministic tie-break policy.
- It differs from Nonogram’s line-status checks (no DP) and from Elevator/Bowling state machines (no table reconstruction).

## Out of scope
- Myers’ O(ND) diff, move detection, syntax highlighting, or huge inputs. One page, one POST endpoint, fixed small limits.

## Risks
- Backtrack tie-breaking must be pinned or two valid scripts will exist. Keep inputs short, fix the policy (prefer diagonal "keep", then delete, then insert), and cap lengths in tests.