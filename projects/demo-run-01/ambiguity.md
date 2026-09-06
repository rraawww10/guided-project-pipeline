# Ambiguity report - demo-run-01

**Verdict:** 1 blocking, 6 worth a look

## Blocking
### A1 - Years tie-break when no tokens are active
- **Where:** spec.md, Stable comparator (Session 3) and spec.json, Session 3, criterion c-3-1
- **Owner:** test-runner
- **The line:** "Tie‑break 2: years DESC" (spec.md) vs "c-3-1: With no active tokens (?active=), if two items have the same unrounded score, the order is by name in ASCII codepoint order" (spec.md/spec.json)
- **Reading one:** The comparator always applies years DESC as the second tie-breaker, regardless of which tokens are active. With no active tokens (all scores 0), items are ordered by years DESC, then name ASC.
- **Reading two:** The years DESC tie-break applies only when the "years" token is active. With no active tokens, after score DESC the next (effective) tie-break is name ASC, as c-3-1 implies.
- **Why it matters:** It changes the visible order for ?active= (and any case where unrounded scores tie). A builder could implement either rule and ship a different order; the tests for c-3-1 will pin only one reading and the other will go red.
- **Suggested wording:** "Primary: unrounded score DESC. When 'tag' is active, prefer hasPreferredTag. When 'years' is active, break remaining ties by years DESC. Finally, break any remaining ties by name ASC (ASCII). With no active tokens, ties go straight to name ASC."

## Worth a look
### W1 - "current dataset" for years normalization
- **Where:** spec.md, Weights and signals → Session 2 scoring rule
- **Owner:** test-runner
- **The line:** "normalize years to a 0..1 band by dividing by the maximum years in the current dataset"
- **Reading one:** Compute maxYears over the full, unfiltered candidate set before any request-time filters (including min) are applied.
- **Reading two:** Compute maxYears over the subset relevant to the current request (e.g., after applying a min threshold or other request-scope narrowing).
- **Why it matters:** If maxYears is taken after filtering, the denominator can change with the query, altering scores, ordering, and reasons. The suite will pin one behaviour.
- **Suggested wording:** "Compute maxYears over all seeded candidates (before any request-time filters)."

### W2 - Duplicates and order in the 'active' query
- **Where:** spec.md, Endpoints → ep-rank → Query parameters; spec.json, ep-rank.request.query.active; cut hint for cut-api-rank-parse-query
- **Owner:** test-runner
- **The line:** "If multiple 'active' keys are present ... join their values with commas in arrival order before parsing" and "write the valid set into activeTokens"
- **Reading one:** Treat tokens as a mathematical set: deduplicate after parsing; 'years,years' yields {years} and reasons list remains one entry per signal.
- **Reading two:** Preserve duplicates from arrival order through to parsing; downstream logic may see repeats (e.g., for logging or reasons ordering) even if scoring ignores them.
- **Why it matters:** It affects what the server accepts and could change the exact text shown in reasons if duplicates were reflected there. The tests will assume one of these behaviours.
- **Suggested wording:** "After joining, split, trim, drop empties, validate, and deduplicate so activeTokens is a Set({years, tag})."

### W3 - Behaviour on invalid 'min' values
- **Where:** spec.md, Endpoints → ep-rank → Query parameters (min); spec.json, ep-rank.request.query.min
- **Owner:** test-runner
- **The line:** "min: optional number"
- **Reading one:** Non-numeric or NaN 'min' yields 400 (invalid query).
- **Reading two:** Non-numeric or NaN 'min' is ignored as if 'min' were absent (still 200).
- **Why it matters:** It changes response status and filtering behaviour. The suite will pin exactly one.
- **Suggested wording:** "If 'min' is present and not a finite number, respond 400; otherwise apply the filter."

### W4 - Reasons formatting for the tag bonus
- **Where:** spec.md, Data model → RankItem.reasons examples
- **Owner:** nothing
- **The line:** "reasons[] includes ... e.g., 'years +0.60', 'preferred tag +1'"
- **Reading one:** Show integer bonuses without decimals ("+1").
- **Reading two:** Format all contributions to two decimals for consistency ("+1.00").
- **Why it matters:** UI/tests that assert exact text could disagree. Today the suite only checks for the word 'years', so this likely passes unnoticed but drifts the UX.
- **Suggested wording:** "Format years to two decimals; the tag bonus may be rendered as '+1' (no decimals)."

### W5 - How cmp knows whether 'tag' is active
- **Where:** spec.md, Stable comparator (Session 3); cut hints referencing lib/sort.ts (cmp)
- **Owner:** nothing
- **The line:** "always sort using the stable comparator from lib/sort.ts (cmp)" and "when the 'tag' token is active ..."
- **Reading one:** cmp(a, b, activeTokens) receives the active tokens and is a pure comparator.
- **Reading two:** cmp(a, b) reads 'tag' activeness from a module-level/shared state set elsewhere.
- **Why it matters:** It affects API shape and testability of the comparator but not visible behaviour; no downstream checker constrains the signature.
- **Suggested wording:** "Export cmp(a, b, activeTokens: Set<Token>) and pass activeTokens in /api/rank when sorting."

### W6 - Idea/spec drift on seed size
- **Where:** idea.md (Sessions 1) vs spec.md (Seed)
- **Owner:** nothing
- **The line:** idea.md: "seed file of 8–12 candidates" vs spec.md: "Exactly 10 candidates"
- **Reading one:** Follow the idea's 8–12 range.
- **Reading two:** Follow the spec's exact count of 10 (what tests will pin).
- **Why it matters:** It is a drift from the idea; not graded, but worth noting for expectations and guide prose.
- **Suggested wording:** "Exactly 10 candidates (fixed)."