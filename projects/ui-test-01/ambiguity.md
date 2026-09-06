# Ambiguity report - ui-test-01

**Verdict:** 4 blocking, 10 worth a look

## Blocking
### A1 - Rule priority is referenced but not defined
- **Where:** spec.md, Session 2, criterion c-2-2
- **Owner:** nothing
- **The line:** "On sc-main, with two rules for the same envelope at different priorities, the rationale panel renders the higher-priority rule's line before the lower-priority one."
- **Reading one:** Rules carry an explicit numeric field (e.g., `priority`), where a larger number is a higher priority; sorting uses that field and then rule id for ties.
- **Reading two:** No explicit field exists; evaluation priority is the array/index insertion order (or a smaller number means higher priority). Ties keep input order rather than using rule id.
- **Why it matters:** The Data model section defines no `priority` on any Rule shape, while the session requires ordering by priority and the cut hint sorts by it. A builder must guess both how priority is represented and which numeric direction is "higher". This changes algorithm, rationale order, and test fixtures, and no downstream checker asserts the prose/type coherence here.
- **Suggested wording:** "Add `priority: number` to all rule types; higher numbers have higher priority. Sort by `priority` (desc), breaking ties by ascending `rule.id`."

### A2 - What the cap limits is unclear (rule vs envelope total)
- **Where:** spec.md, Session 2, cut-apply-caps hint
- **Owner:** nothing
- **The line:** "Limit any percent-with-cap contribution so the envelope’s addition into `out` never exceeds its declared cap."
- **Reading one:** The cap limits this rule’s own contribution to the envelope (i.e., `min(paycheck * percent/100, cap)`), independent of other rules on that envelope.
- **Reading two:** The cap limits the envelope’s total allocated amount from all rules to at most the cap (i.e., sum over rules is globally limited to `cap`).
- **Why it matters:** With multiple rules targeting one envelope, these produce different totals and different remainders, and the difference is not graded directly by any criterion. The Rule shapes attach `cap` to the rule, while the hint speaks about the envelope; without an explicit choice this is guesswork a test may not pin.
- **Suggested wording:** "For a `CappedPercentRule`, add at most `min(paycheck * percent/100, cap)` from that rule; caps do not bound the envelope’s overall total."

### A3 - URL encodes which scenario on compare: one or both?
- **Where:** spec.md, Session 3, criterion c-3-5
- **Owner:** test-runner
- **The line:** "On sc-compare, opening a copied share URL displays an identical scenario in both the editor and results."
- **Reading one:** The URL encodes a single scenario; opening the link initializes one column (e.g., the active one) so that its editor and results match.
- **Reading two:** The URL encodes both Scenario A and Scenario B; opening the link restores both columns identically to how they were when copied.
- **Why it matters:** The Data model declares a single "Scenario state (encoded in URL)", while the compare screen contains two scenarios. Builders can reasonably implement either encoding. The tests that drive c-3-5 will pin one behavior; picking the other will fail assertions.
- **Suggested wording:** "The share URL encodes BOTH Scenario A and Scenario B; opening it restores both columns."

### A4 - Undo/Redo target and UI controls are unspecified
- **Where:** spec.md, Session 3, criteria c-3-3 and c-3-4
- **Owner:** nothing
- **The line:** "On sc-compare, after pressing Undo, the active editor shows the previous value." / "On sc-compare, after pressing Redo, the active editor shows the value that was undone."
- **Reading one:** Each column has its own Undo/Redo buttons that affect only that column’s editor state; the "active" editor is the one whose button you pressed.
- **Reading two:** There is a single global Undo/Redo (keyboard or top-level buttons) that applies to whichever editor is "active" by focus, with no visible per-column controls.
- **Why it matters:** `screens` in spec.json list no Undo/Redo controls for sc-compare, while the criteria require "pressing" Undo/Redo and name an "active editor" without defining how it is chosen. Without pinned controls, the test author and builder can implement different affordances and ship incompatible UIs.
- **Suggested wording:** "Each column shows Undo and Redo buttons that affect only that column. Clicking them undoes/redoes edits in that column’s editor."

## Worth a look
### W1 - "Remainder" is not defined
- **Where:** spec.md, Outcome
- **Owner:** test-runner
- **The line:** "... add caps and ordering, distribute any remainder stably, and can compare two rule sets side-by-side."
- **Reading one:** Remainder is paycheck minus the sum of all fixed and percent allocations (after caps and rounding to cents), and it is then distributed.
- **Reading two:** Remainder is only the leftover from per-rule rounding to cents (percentages sum exactly to paycheck); fixed under-allocation does not count as remainder.
- **Why it matters:** The remainder basis changes both which envelopes are eligible and how much gets distributed; tests that assert exact cents will fail if the interpretation differs.
- **Suggested wording:** "Remainder = paycheck − sum of all rule contributions after caps, rounded to cents."

### W2 - Which envelopes are "eligible" for remainder
- **Where:** spec.md, Session 2, cut-distribute-remainder hint
- **Owner:** test-runner
- **The line:** "Spread the leftover amount into `updated` across eligible envelopes in a fixed, repeatable order until no remainder or all caps are met."
- **Reading one:** Eligible = envelopes that have at least one capped-percent rule and are not yet at their caps.
- **Reading two:** Eligible = all envelopes present in the allocation, excluding only those with explicit hard caps currently reached; envelopes with only fixed/uncapped-percent rules also receive remainder.
- **Why it matters:** Eligibility changes which rows increase and can affect multiple criteria. Tests will pin one interpretation; clarifying prevents a rework loop.
- **Suggested wording:** "Eligible envelopes are those present in the allocation whose current total is below their cap, or all envelopes if no caps exist."

### W3 - Basis of the "fixed, repeatable order" for distributing remainder
- **Where:** spec.md, Session 2, cut-distribute-remainder hint
- **Owner:** test-runner
- **The line:** "... across eligible envelopes in a fixed, repeatable order ..."
- **Reading one:** Order by ascending `envelope.id` (lexicographic), independent of insertion.
- **Reading two:** Order by creation/insertion order of the first rule that touched the envelope (stable on reload via URL ids).
- **Why it matters:** Different bases produce different per-envelope cents when caps or indivisible pennies appear. c-2-5 asks for stability but not which order, so tests may still need a concrete basis.
- **Suggested wording:** "Distribute in ascending `envelope.id`; ties cannot occur."

### W4 - Direction of "higher priority comes first"
- **Where:** spec.md, Session 2, cut-rules-by-priority hint
- **Owner:** test-runner
- **The line:** "Sort the given rules into `ordered` so higher priority comes first and ties are resolved stably by rule id."
- **Reading one:** Higher priority = larger numeric value sorts earlier.
- **Reading two:** Higher priority = smaller numeric value sorts earlier.
- **Why it matters:** It changes both evaluation order and the rationale panel order; the tests will pin an ordering.
- **Suggested wording:** "Sort by `priority` descending (higher numbers first)."

### W5 - Tie-breaker by rule id lacks ordering specifics
- **Where:** spec.md, Session 2, cut-rules-by-priority hint
- **Owner:** test-runner
- **The line:** "... ties are resolved stably by rule id."
- **Reading one:** Break ties by ascending string comparison of `rule.id` (case-sensitive).
- **Reading two:** Break ties by numeric comparison of numeric substrings, or case-insensitive.
- **Why it matters:** Equal priorities could reorder rationale lines; while not directly pinned, it risks nondeterminism across reloads unless precisely stated.
- **Suggested wording:** "Break ties by ascending, case-sensitive string compare of `rule.id`."

### W6 - Rounding policy for percent allocations and remainder
- **Where:** spec.md, Session 1, criteria (e.g., c-1-2) and overall rendering of amounts like "50.00"
- **Owner:** test-runner
- **The line:** "sc-main renders a row for 'Food' with amount 50.00 after entering paycheck 500 and a 10% rule to 'Food'."
- **Reading one:** Round each rule contribution to cents before summing per envelope; distribute remainder pennies afterward.
- **Reading two:** Sum at full precision per envelope, then round the envelope total to cents; remainder distribution only addresses under-allocation from caps, not rounding.
- **Why it matters:** Different rounding stages change totals and remainder; tests that assert exact strings will fail if the builder picks the other policy.
- **Suggested wording:** "Round each rule’s contribution to 2 decimals, then sum; distribute leftover cents as remainder."

### W7 - Whether paycheck is shared between Scenario A and B
- **Where:** spec.md, Screens, sc-compare description
- **Owner:** test-runner
- **The line:** "shows two independent columns (Scenario A and Scenario B) each with its own rules editor and results list, plus a shareable URL field."
- **Reading one:** "Independent" means each column has its own paycheck value as part of its scenario.
- **Reading two:** Columns share one paycheck, differing only by rule sets.
- **Why it matters:** Totals per column depend on paycheck; tests that enter different rules may still pass with shared paycheck, but undo/redo and URL encoding differ materially.
- **Suggested wording:** "Each column is a full scenario with its own paycheck, envelopes and rules."

### W8 - Zero-allocation envelopes: should they render a row?
- **Where:** spec.md, Session 1, criterion c-1-3
- **Owner:** test-runner
- **The line:** "sc-main renders one results row per distinct envelope after adding two envelopes with any rules."
- **Reading one:** Show a row for every envelope referenced by any rule, even if its current allocation is 0.00.
- **Reading two:** Show a row only for envelopes whose current allocation is > 0.00.
- **Why it matters:** The row count and which names appear can differ when paycheck is 0 or caps zero out contributions; selectors in tests may rely on presence/absence.
- **Suggested wording:** "Render a row for every envelope referenced by at least one rule, even if its amount is 0.00."

### W9 - What "reload with identical inputs" means operationally
- **Where:** spec.md, Session 2, criterion c-2-5
- **Owner:** test-runner
- **The line:** "On sc-main, after reloading the page with identical inputs, the Results list renders the same per-envelope amounts and the same remainder distribution order."
- **Reading one:** Reload means a fresh page load without persistence; "identical inputs" means re-entering the same data yields the same outcome (determinism only).
- **Reading two:** Reload restores state automatically from the URL or other storage so that no re-entry is needed.
- **Why it matters:** The first is an algorithmic determinism check; the second implies state restoration behavior. Tests may assume one and builders implement the other.
- **Suggested wording:** "Determinism only: re-entering the same inputs after a hard reload yields the same results and order; no persistence implied in session 2."

### W10 - What the rationale must contain vs where fields live
- **Where:** spec.md, Session 2, cut-generate-trace hint
- **Owner:** nothing
- **The line:** "Build `trace` entries that record before, applied and after amounts per rule with a short reason string."
- **Reading one:** The trace must include entries for remainder distributions even though they are not rules; reason strings may include rule ids redundantly.
- **Reading two:** Only rule applications produce trace entries; remainder adjustments are not traced, and "reason" need not repeat ids already in fields.
- **Why it matters:** c-2-4 asks for rationale lines with rule identifiers and applied amounts; without deciding whether remainder adjustments are included, builders may omit or include them and ship different UI.
- **Suggested wording:** "Emit trace entries only for rule applications; the reason string includes the `rule.id` and the applied amount. Remainder distribution is not part of the trace."