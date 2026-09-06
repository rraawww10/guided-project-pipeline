# CSV Cards: Parse, Map, and Filter

**One line:** Paste a small CSV, map headers to fields, parse it into typed records, and browse/filter the result as cards.

## Theme
A tiny parser is a great way to teach careful logic and edge-case thinking. This project builds a tolerant CSV-to-records pipeline without external libraries, capped to a few dozen rows. Valuable because it shows how to write and test a tokenizer/parser in TypeScript and apply it to a useful UI.

## Sessions
1. App boots and previews text: include a sample.csv in the repo; GET /api/sample returns its raw text; the UI shows a textarea and a live preview of the first 3 rows (unparsed) to prove wiring.
2. Parsing and mapping: implement parseCsv(text) handling quoted fields, embedded commas, and newlines; infer simple types (number/string) and map headers to field names; render parsed rows in a grid.
3. Tiny expression filter: implement a minimal filter expression parser (AND/OR/NOT, key:value, and numeric comparisons like price>10) to produce an AST and evaluate it against rows; add a text box to filter the grid.

## What the student types
- tokenizeCsv(text) + parseRows(tokens): handles quotes, escapes, row boundaries.
- inferType(value) and coerceRow(headers, cells): builds typed records.
- parseExpr(input) -> AST and evalExpr(ast, row): tiny boolean/comparison evaluator.

## What this teaches that the shipped projects do not
- Writing a small parser and evaluator from first principles, not relying on a package.
- Deterministic handling of tricky CSV cases and explicit tests against them.
- Turning a parsed structure into a UI without depending on external data or time.

## Out of scope
- Huge files, streaming parsers, uploads to disk, or schema inference beyond basic numbers/strings.

## Risks
CSV edge cases can balloon; scope the grammar (no multiline quoted fields beyond a single embedded newline) and keep fixtures tiny so the minutes stay within budget.