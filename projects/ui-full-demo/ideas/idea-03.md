# Expression Evaluator with AST Viewer

**One line:** A tiny expression language with +, −, ×, ÷ and parentheses, evaluated deterministically and shown as an AST, all on one page.

## Theme
Students often meet parsers only as black boxes. Here they write a tokenizer and a small, testable parser with operator precedence, then render and evaluate its AST. It’s worth the time because precedence, associativity and clear error positions are foundational and reusable.

## Sessions
1. Tokens and +/−: implement tokenize(text) and a minimal parseAddSub that handles integers and +/− only. Render the numeric result and the token stream at "/".
2. Precedence and () : extend to ×/÷ and parentheses with a recursive-descent parse (expr → term → factor). Show an AST tree and evaluate it. Add POST /api/eval returning { value, ast } or { error: { pos, message } }.
3. Variables: accept identifiers and resolve them from a small on-page JSON env (e.g. { x: 3, y: 4 }). Undefined names are a deterministic error with a pinned span. Keep everything local and reproducible.

## What the student types
- tokenize(text): numbers, identifiers, operators, parentheses with positions.
- parseExpr/parseTerm/parseFactor: a recursive-descent parser that enforces precedence and associativity.
- eval(ast, env): a pure interpreter over the AST with precise error cases.

## What this teaches that the shipped projects do not
- Distinct from the Ledger project’s record parser: this teaches operator precedence, recursive descent and AST evaluation, none of which appear in Minesweeper, Nonogram, Bowling, Elevator or the Budget Allocator.
- It introduces positional error reporting and a clean separation of tokenize/parse/eval, which the shipped specs have not covered.

## Out of scope
- Floats, exponentiation, function calls, implicit multiplication, or assignment. One page, one POST endpoint, integers only.

## Risks
- Precedence bugs and off-by-one error spans. Keep the grammar tiny, fix a single-number token type, and pin tie-breaking so identical input always yields the same AST.