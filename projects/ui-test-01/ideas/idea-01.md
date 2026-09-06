# Envelope Budget Allocator

**One line:** A tiny Next + React + TypeScript app that allocates a paycheck across budget envelopes by rules, with an explanation trail for every rupee/dollar.

## Theme
A deterministic allocation problem that fits entirely in pure functions. Students model rules (fixed amounts, percentages, and caps), order them, and produce a trace that explains each envelope's final amount. It is worth a session because it turns informal money rules into explicit, testable logic.

## Sessions
1. Scaffolding + first pass allocation: form inputs and a pure `allocate(paycheck, rules)` that handles fixed and percent rules; render a simple results list that updates as you type.
2. Rule interactions: add caps and ordering; implement remainder distribution and generate a step-by-step trace; UI shows per-envelope rationale.
3. Scenarios and history: compare two rule sets side-by-side; add undo/redo via a small reducer; encode state in the URL so a scenario opens reproducibly.

## What the student types
- `allocate(paycheck, rules)`: pure pass that applies fixed, then percentage rules, returning per-envelope amounts.
- `distributeRemainder(amounts, rules)`: deterministic remainder spreading with a stable order and caps respected.
- `rulesByPriority(rules)`: a comparator/ordering that makes evaluation order explicit and testable.

## What this teaches that the shipped projects do not
Not another list-with-a-filter: it is a calculation with ordering, caps, and an explanation trace. It teaches how to express business rules as pure, replayable steps and how to make rule interactions deterministic and inspectable.

## Out of scope
- Real currency/locale libraries, calendars, or recurring income.
- Persistence beyond URL encoding; no external storage or APIs.
- Optimizers beyond the three rule types (no linear programming).

## Risks
Remainder logic can bloat if too many rule types are added. Keep it to fixed, percent, and capped-percent; ensure the distribution order is fixed so tests remain deterministic.
