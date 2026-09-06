# Unit Converter with an Expression Parser

**One line:** Convert between units using a small parser that understands expressions like "3 ft 2 in -> cm" and custom units.

## Theme
A focused parser-plus-calculation problem: tokenize and parse quantities with units, reduce to a canonical base, and format results. It’s deterministic, self-contained, and teaches dimension checking and precise numeric handling without dates or external APIs.

## Sessions
1. Simple conversions: seed `app/data/units.seed.json` with base and derived units (m, cm, in, ft; g, kg). Build a converter API that handles simple inputs (e.g., `m -> cm`) and a page with an input and output view. End: base conversions work with fixed factors.
2. Expression parsing: implement `parseExpression` for inputs like `3 ft 2 in` (sum of like-dimension quantities). Normalize to base units and compute. End: mixed-unit expressions convert correctly and format sensibly.
3. Custom units: add a route to define a new unit in terms of a base (e.g., `spoon = 5 ml`) saved to a local JSON file. UI lists known units and supports converting using the new definition. End: a user-defined unit participates in conversions.

## What the student types
- `parseExpression(input: string): Quantity[]` – tokenizer and parser for number+unit terms with optional addition.
- `convert(qs: Quantity[], to: Unit, table: UnitTable): Quantity` – dimension check, normalization, and factor math.
- `format(q: Quantity, to: Unit): string` – rounding and user-friendly output.

## What this teaches that the shipped projects do not
- A tiny domain-specific language for units and robust dimensional conversion; distinct from pipeline-test BFS exercises and from list/filter/search projects.
- Numeric normalization and precision considerations in a testable, clock-free setting.

## Out of scope
- Arbitrary algebra, temperature scales with offsets, or unit multiplication/division.
- Persisting multiple user profiles or sharing custom units.
- Fancy input widgets beyond a text box and buttons.

## Risks
- Parser ambiguity or floating-point surprises. Keep grammar minimal (sum of terms, shared dimension) and use exact rational factors for base units where possible.
