# Scoring Formula Engine

**One line:** Type a tiny scoring formula like "2*impact + features - effort" and see persisted initiatives sorted by the computed score.

## Theme
A constrained, safe expression parser and evaluator that turns a string into a deterministic calculation over rows in SQLite. No eval, no dates, no external APIs. The grammar is tiny and the dataset small enough to seed by hand.

## Sessions
1. Setup and default score.
   - Prisma schema: Initiative(id, name, impact INT, features INT, effort INT), SavedFormula(id, name, expr TEXT).
   - Seed ~8 initiatives with varied numbers; list them with a built-in default score computed server-side (e.g., impact*2 + features - effort).
2. Parse and evaluate a user formula.
   - Build a tokenizer for identifiers (impact, features, effort), integers, operators + - * and spaces; no parentheses.
   - Parse into an AST and implement an evaluator over one Initiative; GET /api/scores?expr=... returns rows [{id, name, score}].
3. Stable sorting and tie-breakers.
   - Sort initiatives by score DESC with a secondary key name ASC so the order is deterministic; UI shows the sorted list and each score.
   - Seed data chosen so natural orders differ from the computed one to keep tests meaningful.
4. Save and apply named formulas.
   - POST /api/formulas saves {name, expr} and GET /api/formulas lists them; selecting one reapplies it to compute and render scores.

## What the student types
- A tiny, safe tokenizer and parser for a fixed vocabulary; AST nodes for number, identifier, binary op; and an evaluator over a known shape.
- Server-side application of the formula to every row and a deterministic sort with a tie-break rule.
- A persistence layer for named formulas and a simple recall/apply flow.

## What this teaches that the shipped projects do not
- Writing and testing a micro-parser and evaluator in TypeScript, then mapping it to a Prisma-backed dataset.
- Deterministic ranking with explicit tie-breaks and seed design that avoids accidental orderings.

## Out of scope
- Parentheses, division, functions, arbitrary identifiers, and user-defined fields.
- Auth, concurrent edits, drag-and-drop reordering.

## Risks
- Parser scope creep is the main risk; keeping the grammar to identifiers, integers, and + - * avoids a session overrun while still teaching parsing and evaluation.