# Tiny Expression Language: Tokenize, Parse, Evaluate

**One line:** A mini expression editor that shows the AST and evaluates a small arithmetic/variable language entirely in the browser.

## Theme
Build a tiny, deterministic parser and evaluator: numbers, + − × ÷, parentheses, variables, and 2–3 functions (min, max). Worth a session because it demystifies parsers and puts pure, testable logic behind a simple UI.

## Sessions
1. Tokens and AST: write a hand-rolled tokenizer and a recursive‑descent `parseExpression` for +/− and */÷ with parentheses; render the AST tree and result for literals.
2. Names and functions: add variables (from a small environment map) and simple functions (`min(…)`, `max(…)`); keep evaluation pure.
3. Errors and UX: add span-aware errors with caret highlighting; ship a preset palette of examples; ensure every parse/eval is reproducible from seeded inputs.

## What the student types
- `tokenize(source)`: produces typed tokens with positions.
- `parseExpression(tokens)`: precedence-respecting parser returning an AST.
- `evaluate(ast, env)`: pure evaluator over numbers, names, and built-ins.

## What this teaches that the shipped projects do not
It is a small parser, not CRUD. Students practice building a lexer, a precedence parser, and a pure evaluator with position-aware error reporting—skills not covered by grid/query projects.

## Out of scope
- Floating-point locale quirks, bigints, or user-defined functions.
- Side effects or IO; evaluation is pure.
- Any real-time features.

## Risks
Parser scope creep can break the time budget. Keep grammar tiny (binary ops, grouping, names, and 2 functions) and pin precedence with tests to avoid ambiguity.
