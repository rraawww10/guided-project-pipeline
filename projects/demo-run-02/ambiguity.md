# Ambiguity report - demo-run-02

**Verdict:** 0 blocking, 8 worth a look

## Blocking

## Worth a look
### W1 - Rounding/tie-break for weighted shares and after exclusions
- **Where:** spec.md, Session 2, cut `cut-lib-compute-balances` hint
- **Owner:** test-runner
- **The line:** "Hint: Compute each person's net in cents into `out` by adding amounts they paid and subtracting their share of each expense; divide an expense by the sum of participant weights (default 1) and subtract each share from that participant."
- **Reading one:** Use integer math: floor each proportional share; distribute remainder cents to the largest fractional parts, tie-breaking by person name ASC for determinism.
- **Reading two:** Round each participant's share differently (nearest, up for creditors/down for debtors), or allocate remainder cents by input order/payer-first.
- **Why it matters:** Different rounding/tie-break rules change exact balances and, downstream, which transfers are required. The seed divides evenly, but toggling people (Session 3) or non-unit weights would surface this.
- **Suggested wording:** "Use integer math; for each expense, floor proportional shares and distribute leftover cents to participants with larger fractional parts, breaking ties by name ASC."

### W2 - Include/exclude semantics when an excluded person is a payer/participant
- **Where:** spec.md, Session 3, criterion c-3-3
- **Owner:** test-runner
- **The line:** "Unchecking [data-testid=\"include-Eve\"] removes Eve from balances and no [data-testid=\"transfer-row\"] contains \"Eve\""
- **Reading one:** Excluding a person removes their paid expenses from consideration and removes them from participant lists in remaining expenses, re-normalising weights to the included set.
- **Reading two:** Compute balances over the full data, then filter balances/transfers mentioning excluded people from the display (included-set totals may no longer sum to zero).
- **Why it matters:** The recomputed balances and transfers can differ substantially; the test pins only absence of a name, not the recompute rule.
- **Suggested wording:** "When excluded, drop expenses they paid and remove them from other expenses, renormalising weights; balances/transfers must sum to zero over the included names."

### W3 - Naive transfers order is underspecified
- **Where:** spec.md, Session 2, criterion c-2-2 and cut `cut-ui-set-transfers` hint
- **Owner:** test-runner
- **The line:** c-2-2: "the first item reads \"Eve pays Alice $13.00\""; hint: "make it stable across renders."
- **Reading one:** Define the full naive list order (e.g., generation order of the greedy algorithm) and assert it.
- **Reading two:** Only the first (and later, the last) item are pinned; intermediate ordering can vary as long as items are present, which may differ between implementations.
- **Why it matters:** Tests asserting sequence positions can flake across reasonable implementations if the order rule is not fixed.
- **Suggested wording:** "For naive mode, order transfers by generation time from the greedy loop; when amounts tie, break by payer then payee ASC."

### W4 - Screen elements omit the transfers total hook used by a criterion
- **Where:** spec.json, Screens -> sc-home elements; and spec.md, Session 2, criterion c-2-3
- **Owner:** test-runner
- **The line:** spec.json elements list lacks `[data-testid=transfers-total]`; c-2-3 asserts an element `[data-testid=\"transfers-total\"]` equals "$30.00".
- **Reading one:** The elements list is authoritative; tests should not rely on hooks not declared there.
- **Reading two:** Criteria can introduce additional required hooks even if not listed under elements.
- **Why it matters:** The Verifier relies on stable hooks; a drift between the two files invites a selector mismatch.
- **Suggested wording:** Add "Transfers total [data-testid=transfers-total]" to sc-home elements in spec.json, or change c-2-3 to cite an existing element.

### W5 - Session 2 ‘builds’ omits the screen it modifies
- **Where:** spec.json, Session 2, "builds": ["ep-naive-settlement"] while criteria target sc-home
- **Owner:** pack-writer
- **The line:** "\"builds\": [\"ep-naive-settlement\"]"
- **Reading one:** Session 2 builds only the endpoint; UI changes to sc-home are incidental.
- **Reading two:** Session 2 also builds sc-home (balances and transfers render), so the guide/session plan should name it under builds.
- **Why it matters:** The guide’s narrative and timing depend on builds; leaving sc-home out risks drift between plan and machine contract.
- **Suggested wording:** Add "sc-home" to Session 2 "builds".

### W6 - Session 3 declares no builds despite UI/lib changes
- **Where:** spec.json, Session 3, "builds": []
- **Owner:** pack-writer
- **The line:** "\"builds\": [],"
- **Reading one:** Session 3 changes only library/helpers and toggles with no build-owned artifact.
- **Reading two:** Session 3 also modifies sc-home (toggle and include/exclude) and lib/settlement.ts; it should reflect those under builds to match the plan/guide.
- **Why it matters:** Omitting builds can mislead the Pack Writer on scope and timing.
- **Suggested wording:** Declare sc-home under builds for Session 3 (and any endpoint if later extended).

### W7 - Positive balance formatting vs formatMoney guidance
- **Where:** spec.md, Session 2, criterion c-2-1; and Session 3, cut `cut-lib-format-money` hint
- **Owner:** test-runner
- **The line:** c-2-1 pins texts like "Alice +$26.00"; the formatting hint gives only a negative example "-615 → \"-$6.15\"".
- **Reading one:** formatMoney returns "$26.00" and the UI prepends "+" for positives in the balances list only.
- **Reading two:** formatMoney itself returns "+$26.00" for positives and "$26.00" elsewhere, or the UI omits the plus entirely.
- **Why it matters:** Exact string assertions differ depending on where the plus sign is applied.
- **Suggested wording:** "formatMoney returns "$X.YY" for non-negatives and "-$X.YY" for negatives; the balances UI prepends "+" for positives as shown in c-2-1."

### W8 - Name sort collation for “name-ASC”
- **Where:** spec.md, Session 2, criterion c-2-1
- **Owner:** test-runner
- **The line:** "in name-ASC order, with exact texts: Alice +$26.00; Bob -$6.00; Cara +$4.00; Dan -$11.00; Eve -$13.00"
- **Reading one:** Sort using case-sensitive Unicode code-point order (ASCIIbetical).
- **Reading two:** Sort case-insensitively or with locale-aware collation.
- **Why it matters:** Different collations can reorder names in other fixtures; pinning the rule keeps ordering deterministic.
- **Suggested wording:** "Sort names by case-sensitive Unicode code-point order; use a stable sort."