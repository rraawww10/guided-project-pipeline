# Structured From Text

**One line:** Paste lines like "Build landing | 2.5h | #frontend !urgent" and get structured tasks with per-tag totals and inline error feedback.

## Theme
Turn semi-structured text into structured data with a tiny parser and show how small, composable passes (tokenize → parse → validate) improve robustness. It’s valuable because students frequently meet text inputs and logs and need strategies beyond split(','). Everything is local and repeatable.

## Sessions
1. Scaffold a page with a textarea and a results table. Seed a few example lines in the UI and render them raw under the input. End with a working page and no parsing logic yet.
2. Write tokenize(line) and parseLine(tokens) that recognize fields: Title | Hours | optional tags starting with # and flags starting with !. Produce either a Task or a ParseError carrying the column and message. Render parsed rows with inline error styling, and compute a total hours-by-tag summary. End with valid lines structured and totals computed.
3. Add forgiving whitespace rules, numeric normalization (e.g., "2" → 2.0), and partial recovery (skip bad field, keep the rest). Add sorting by hours DESC and a filter to show only lines with a given tag. End with a resilient, useful parser and a simple dashboard over its output.

## What the student types
- tokenize and parseLine: a two-step parser that emits either Task or ParseError with locations.
- reduceTotals: fold parsed tasks into per-tag totals and grand totals.
- validateTask: small guards for hours ≥ 0 and duplicate tags.

## What this teaches that the shipped projects do not
- A minimal but real parsing pipeline (tokens → AST-ish object → validation) with error recovery, not just splitting strings or filtering arrays.
- How to surface parser feedback precisely (per-line, per-field) in a React UI without external libraries.

## Out of scope
- File upload, clipboard integration, or downloading results.
- Dates, time zones, or anything dependent on the real clock.
- Fuzzy matching or natural-language parsing.

## Risks
- Grammar creep: keep to Title | Hours | tags (#tag) | flags (!flag). More than that risks overrunning session time.
- Error reporting UX can sink minutes; prefer simple line-level highlights with short messages.