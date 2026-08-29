# Accept

**One line:** A finite-automaton simulator - pick one of four hand-written
machines, feed it a string, and watch it walk state by state to an accept or a
reject.

**Stack:** Next.js (App Router), React, TypeScript. Sessions: 2 x 40 minutes.

## Theme

A state machine drawn on a whiteboard is obvious and a state machine in code is
usually a pile of `if`s. Here the machine is *data* - a transition table in a JSON
file - and the student writes the twelve lines that run it. Four seeded machines
give it something to say: binary numbers divisible by three, strings ending in
`ab`, a valid identifier, and one with a dead state you can fall into and never
leave. Watching a string walk the table is the moment the abstraction stops being
a diagram.

## Sessions

1. **Setup, the table, and one step.** Types, a seed of four machines (alphabet,
   states, start state, accepting states, transitions), `GET /api/machines`, and
   `/machines/[id]` rendering the transition table as a plain HTML table with the
   start state and the accepting states marked. The work is
   `step(machine, state, symbol)`: the table lookup, returning `null` when the
   symbol is outside the alphabet rather than throwing. A single-symbol control
   advances the current state by hand. **Runs:** four machines you can step one
   symbol at a time.
2. **Running, tracing, and the suite.** `run(machine, input)` returns
   `{ verdict, trace }` where verdict is `accept`, `reject` or `invalid-symbol`
   and trace is one entry per consumed character: index, symbol, from-state,
   to-state. The trace renders a row per character. Each machine ships a labelled
   suite of ten strings; `GET /api/machines/[id]/suite` returns each with its
   expected and actual verdict and a pass count. **Runs:** type a string, see the
   walk; the suite page reads 10/10 on every machine.

## What the student types

- `step` - the lookup and the missing-symbol case, which is the difference
  between a rejected string and an invalid one.
- `run` - the fold that both threads the state and accumulates the trace, plus
  the empty-input rule: accepted exactly when the start state is accepting.
- The suite reducer - comparing expected against actual and counting, which is
  where a student sees their own runner being graded by data.

## What this teaches that the shipped projects do not

habit-tracker writes state, but its only mutation is a boolean flip that is
always legal, and recipe-box and tip-split hold no state machine at all. This is
the first project where the seed file is a *program* rather than a set of
records, and the first with a three-valued verdict where two of the values look
alike on screen. The empty string is the kind of edge case that never comes up in
a list-with-a-filter and always comes up here.

## Out of scope

- Non-deterministic automata, epsilon transitions, and any conversion between the
  two.
- Turning a regular expression into a machine, and minimising a machine.
- Building or editing a machine in the UI. The seed is the machine set.
- Animation, timers, or anything that steps the trace on a clock.

## Risks

The trace object's exact shape is the overrun risk: if the spec leaves it loose,
the Verifier grades one field name and the Builder writes another. Declare the
four keys and their types in the spec. Second, `run` graded on a single accepted
string is indistinguishable from `return 'accept'`, so the criteria need an
accept, a reject, the empty string, and a symbol outside the alphabet - at least
two of them on the same machine. Third, rendering the transition table can quietly
eat ten minutes; keep it an unstyled table with a `data-testid` per cell.
