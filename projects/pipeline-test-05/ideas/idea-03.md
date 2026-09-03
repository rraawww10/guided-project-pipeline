# Rewind

**One line:** A small editable stock table with real undo and redo, where every
edit is stored as a command that knows its own inverse and a replay endpoint
proves the history is honest.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

Undo is where a student discovers that the current state is not the interesting
object - the history is. Keeping a snapshot per keystroke is the first idea
everyone has and it explains nothing; keeping a command with an inverse is the
shape every editor, spreadsheet and design tool actually uses. It is also
gradable in a way UI work rarely is: a replay endpoint takes a list of commands
and a number of undos and returns the state, so the history has to be right and
not just look right.

## Sessions

1. **Setup, the table, and the commands.** Types, `data/board.json` with six
   stock rows (name, quantity, shelf), the command union
   `{ kind: 'set', row, field, from, to }`, `{ kind: 'add', row }` and
   `{ kind: 'remove', index, row }`, `apply(state, cmd)` as a pure function
   returning a new array without mutating the one it was given,
   `GET /api/board`, and `/` rendering the table with a quantity input and a
   remove button per row, each with a `data-testid`, above a readable list of
   the commands issued so far. **Runs:** edits change the table and show up as
   a command list a person can read.
2. **Undo, redo, and replay.** `invert(cmd)` returning the command that cancels
   it - the interesting case being `remove`, whose inverse has to put the row
   back at its own index rather than on the end - and the two-stack reducer:
   undo pops the done stack, applies the inverse, pushes onto the redo stack;
   redo does the reverse; and a *new* command clears the redo stack, which is
   the rule everybody forgets. `POST /api/board/replay` takes a command list
   plus an undo count and a redo count and returns the resulting rows.
   **Runs:** edit four times, undo three, redo one, make a fresh edit, and watch
   redo go unavailable.

## What the student types

- `apply` - the pure transition per command kind, including the splice that has
  to copy rather than mutate.
- `invert` - one line per kind, except `remove`, which needs both the row and
  the index it came from, which is why the command carries them.
- The reducer - two stacks, the disabled states of the two buttons, and the
  clear-redo rule on a new command.

## What this teaches that the shipped projects do not

The first project whose main data structure is a *history* rather than a state,
and the first where immutability is graded rather than advised: an `apply` that
mutates its input passes a single-step test and then fails replay, because the
inverse is applied to an array that already moved. recipe-box and tip-split both
recomputed a view from React state, but neither ever kept a second timeline
beside it, and nothing shipped has a command whose inverse has to be derived.

## Out of scope

- Keyboard shortcuts. Undo and redo are buttons, so a test can drive them with
  a plain click.
- Coalescing a run of keystrokes into one undo step. One committed edit is one
  command.
- Persisting the history, or writing the edited table back to `data/board.json`.
  The board is a read at load; everything after that is in memory or in the
  replay body.
- Adding columns, reordering rows, a general command log for anything but this
  table.

## Risks

The command set must be closed and the stack rules written as an ordered
procedure, because undo's edges are arguable - does undoing an `add` also
discard what was typed into the new row? An open question there becomes two
implementations that disagree. Second: every single-step criterion is also
satisfied by a snapshot stack, so at least one criterion has to drive a mixed
sequence through `replay` that includes a `remove` at index 0 followed by an
undo, where an inverse that appends instead of splicing is wrong in a countable
way. Third: inputs grade badly unless the criteria pin the `value` of a
`data-testid`'d input rather than text on the page.
