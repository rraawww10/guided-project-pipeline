# Watchlist Rule Evaluator (Mini‑DSL)

**One line:** Type a simple expression like `price >= 120 and pct_change_1d <= -2` and evaluate it against a seeded watchlist with a hand‑rolled parser.

## Theme
A small parser + evaluator: turn a constrained expression language into an AST and run it deterministically over locally seeded symbol data. Valuable because it teaches tokenization, parsing, safe evaluation, and derived metrics.

## Sessions
1. Schema and seed: Symbols and Prices (EOD history for a few tickers). Render a basic watchlist table from SQLite.
2. Parser: implement tokenization and a recursive‑descent parser for a limited grammar (identifiers, numbers, `and`/`or`, `(` `)`, comparison ops). An endpoint parses to JSON AST and returns errors deterministically.
3. Evaluator: compute derived fields (e.g., `pct_change_1d` from last two closes) and evaluate the AST per symbol without `eval()`. UI shows which symbols match.
4. Saved rules: persist named rules in SQLite, list/apply them server‑side, and render matched symbols. The page runs end‑to‑end from stored rule -> matches.
5. Editor polish: show a readable AST preview and basic validation messages; allow importing/exporting rule JSON.

## What the student types
- A tokenizer and recursive‑descent parser that produces a typed AST.
- A pure evaluator over symbol data and derived metrics with short‑circuit logic.
- Deterministic error reporting (unexpected token, unknown identifier) returned by an API route.

## What this teaches that the shipped projects do not
- Building a mini‑DSL parser and AST evaluator, which is a different shape from CRUD/filter UIs seen elsewhere.
- Combining derived metric calculations with rule application across a set.

## Out of scope
- Full query languages, SQL passthrough, user auth, or live quotes.
- Complex editor widgets; keep to a textarea + results.

## Risks
- Scope creep in the grammar: fix the operator set and associativity up front so the parser stays small and the sessions remain balanced.