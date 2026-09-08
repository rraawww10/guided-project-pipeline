# Tiny Expression Evaluator

**One line:** A small arithmetic expression parser and evaluator (numbers, + − × ÷, parentheses, variables) with a live preview.

## Theme
Hand-writing a tiny parser is a great way to learn how to turn text into structure and then into a result. It is worth a session because the grammar is minimal and the logic is purely deterministic, with no dependencies beyond the page.

## Sessions
1. Scaffold input/output UI: a textarea for the expression, a table for variables, and a result panel. Wire a placeholder `evaluate()` that always returns 0 so the page runs.
2. Implement a tokenizer and Pratt or precedence-based parser for `+ - * /` and parentheses producing an AST; implement an evaluator over the AST (no variables yet).
3. Add variables and functions: read a small key/value map from the table and resolve identifiers; add two pure functions `min(a,b)` and `max(a,b)`; report friendly errors without throwing.

## What the student types
- Tokenizer that emits number, identifier, operator, and paren tokens.
- Recursive-descent or Pratt parser that builds an AST with correct precedence/associativity.
- AST evaluator that resolves variables from a context and supports `min`/`max`.

## What this teaches that the shipped projects do not
Existing projects do not perform text parsing into an AST. This adds a new skill: building a tiny language end-to-end (lex, parse, eval) inside a React+TS app.

## Out of scope
- Exponentiation, unary operators beyond unary minus, or user-defined functions.
- Any evaluation that depends on the real date/time or locale.

## Risks
Parser scope creep. Pin the grammar early and keep the tokenizer and parser small to fit comfortably into the session budget.
