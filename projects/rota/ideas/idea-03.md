# Availability String Parser + Coverage Grid

**One line:** Parse compact availability strings into slot sets and compute a coverage grid against required targets per slot.

## Theme
Many teams record availability in shorthand. This project defines a strict, tiny grammar (e.g., "Mon-Thu AM, Fri PM, Sat*2", "none") and turns it into slot tokens (MonAM, MonPM, …). From those sets, it computes coverage versus a target per slot and flags gaps or overstaffing. Storage is a JSON file; no real clocks or dates—slots are named tokens.

## Sessions
1. Parser: implement a tokenizer and parser from strings to a normalized `Set<Slot>`, supporting ranges (Mon-Thu), parts of day (AM/PM), multipliers (`*2`), and `none`. End: API validates and returns parsed slots for seeded inputs; UI shows a parsed preview.
2. Coverage: from parsed availabilities, compute coverage counts against per-slot targets and flag under/over with reasons. Persist people and their raw strings. End: grid view that recomputes from file on reload.
3. Assignment suggestion: given the grid, produce a simple greedy suggestion of who to assign per slot to hit targets, with deterministic tie-breakers and a write to `assignments.json`. End: end-to-end flow from entering strings to saved suggestions.

## What the student types
- Tokenizer + parser from controlled strings to slot tokens.
- Set algebra/aggregation to compute coverage deltas vs targets.
- Greedy assignment with fair, stable tie-breaking.

## What this teaches that the shipped projects do not
A small, explicit parser feeding a concrete decision engine. Other shipped projects skew toward UI or numeric aggregation; this adds language-to-structure parsing and then uses it to drive staffing decisions without touching real time.

## Out of scope
Free-form natural language, calendars/timezones, and drag/drop. Grammar is fixed and documented; inputs are typed text.

## Risks
Grammar ambiguity and edge cases (e.g., range endpoints, `none`, `*2`). Keep the grammar small and provide at least two grading fixtures per rule (including an edge case) so the parser cannot be replaced by constants.