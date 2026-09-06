# Ambiguity report - demo-run-02

**Verdict:** 3 blocking, 6 worth a look

## Blocking
### A1 - What “include” means for expenses that mention excluded people
- **Where:** spec.md, Session 3, criterion c-3-2
- **Owner:** test-runner
- **The line:** "GET /api/settlement?include=<subset> excludes the omitted person(s): no transfer mentions an excluded name and the transfers still balance to zero."
- **Reading one:** When an include list is present, drop any expense paid by an excluded person and remove excluded participants from remaining expenses, renormalising weights among the included so balances and transfers are computed only over the included set (which then sum to zero internally).
- **Reading two:** Compute balances over the full dataset and then filter out any transfers that mention excluded names, effectively letting net flow to/from excluded people fall outside the computed subset (balances among the included may need an adjustment or may no longer sum to zero).
- **Why it matters:** The settlement amounts, who pays whom, and even whether totals balance within the included set differ substantially between these two approaches, so a Builder must guess and will likely fail tests written for the other.
- **Suggested wording:** When include is present, compute using only included people by discarding expenses whose payer is excluded, removing excluded participants from other expenses, re-normalising weights to the included set, and producing balances and transfers that sum to zero over the included names only.

### A2 - Rounding and remainder distribution for weighted shares in integer cents
- **Where:** spec.md, Session 2, cut `cut-lib-compute-balances` hint
- **Owner:** test-runner
- **The line:** "hint: For the given expenses and participants, compute each person’s net cents (paid minus an equal share by weight) and write the mapping into `out`."
- **Reading one:** Split each expense’s amountCents proportionally by weight using floor division and give leftover cents to the largest fractional remainders, breaking ties by name ascending for determinism.
- **Reading two:** Round each participant’s share to the nearest cent (or round up creditors / down debtors), or allocate remainder cents in input order (or payer-first), which yields different per-person balances even if totals match.
- **Why it matters:** Different rounding and tie-breaking rules change exact balances and which transfers are required; without a declared rule a Builder cannot predict the fixture and determinism claims do not hold.
- **Suggested wording:** For each expense, compute owed shares with integer math by flooring proportional shares and distributing remainder cents to participants with the largest fractional parts, tie-breaking by person name ASC for determinism.

### A3 - “Refined minimal strategy” is undefined
- **Where:** spec.md, Session 3, criterion c-3-1
- **Owner:** test-runner
- **The line:** "GET /api/settlement on the seed produces a transfers list whose length matches the refined minimal strategy for the fixture and in a deterministic sequence."
- **Reading one:** Minimal means the mathematically minimal number of transfers among included people, with a deterministic tie-break to pick one minimal solution.
- **Reading two:** Minimal means “fewer than the naive greedy result” for this seed only, not necessarily globally minimal, with any deterministic ordering acceptable.
- **Why it matters:** The expected number of transfers and the specific sequence to assert differ; a Builder can reasonably implement either and ship code that fails a suite written for the other.
- **Suggested wording:** Treat “refined minimal” as the mathematically minimal number of transfers for the included set, and when multiple solutions exist pick the lexicographically smallest sequence by (from, to, amountCents) after sorting by from/to ASC.

## Worth a look
### W1 - Test id uses raw name or a normalised slug
- **Where:** spec.md, Screens, sc-expenses elements
- **Owner:** test-runner
- **The line:** "Elements: expenses table (data-testid=\"expense-row\" per item), per-payer totals (data-testid=\"payer-total-<name>\"), proposed transfers list (data-testid=\"transfer-row\"), transfer amount element (data-testid=\"transfer-amount\"), include/exclude toggle per person (checkbox with data-testid=\"toggle-<name>\")"
- **Reading one:** <name> is the raw fixture name (including spaces/case) embedded directly in the data-testid.
- **Reading two:** <name> is a slugified form (e.g., lowercased, spaces to hyphens, alphanumerics only) used in the attribute, with the raw name shown only as visible text.
- **Why it matters:** The Verifier’s selectors and the Builder’s markup must agree on exactly the same token; a mismatch will fail otherwise-correct UI.
- **Suggested wording:** Use the exact fixture name for <name> with no normalisation in data-testid values.

### W2 - Sort order “ascending” and collation rules
- **Where:** spec.md, Session 2, criterion c-2-3
- **Owner:** test-runner
- **The line:** "GET /api/settlement returns transfers in a deterministic order (sorted by from, then to, both ascending), enabling exact assertions."
- **Reading one:** Compare names with case-sensitive Unicode code-point order (ASCIIbetical).
- **Reading two:** Compare names case-insensitively or with locale-aware collation, which orders mixed-case or accented names differently.
- **Why it matters:** Different collations yield different sequences even when transfers are identical; tests asserting a full sequence will be brittle without a fixed rule.
- **Suggested wording:** Sort by from then to using case-sensitive Unicode code-point order, stable sort.

### W3 - Parsing the include list in the query string
- **Where:** spec.md, Endpoints, ep-settlement request description
- **Owner:** test-runner
- **The line:** "Request: optional query param `include` as a comma-separated list of person names to include in the computation. If omitted, include all people found in expenses."
- **Reading one:** Split on commas, trim spaces, decode percent-encoding, and ignore empty tokens; names cannot contain commas.
- **Reading two:** Treat the whole string as one name if it is quoted, or treat empty include (include=) as “include none,” or treat repeated names as an error.
- **Why it matters:** Edge cases (trailing commas, spaces, URL-encoded commas, empty strings) change who participates and thus balances; tests must pin one rule.
- **Suggested wording:** Split on commas, trim spaces, percent-decode each token, drop empties, and ignore unknown names; an empty string means “include none.”

### W4 - What event counts as “when settlement data has been loaded”
- **Where:** spec.md, Session 2, criterion c-2-4
- **Owner:** test-runner
- **The line:** "sc-expenses shows a section title \"Proposed transfers\" when settlement data has been loaded."
- **Reading one:** Fetch settlement on initial page load and render the title only after a successful 200/JSON response.
- **Reading two:** Always render the title regardless of data state (or render after any attempt to load, including failure), with “loaded” interpreted loosely.
- **Why it matters:** A title rendered unconditionally can satisfy the criterion while the data never loads; tests should specify the trigger.
- **Suggested wording:** Render the title only after a successful fetch of /api/settlement has resolved with 200 and valid JSON.

### W5 - Formatting rules for zero and negative amounts
- **Where:** spec.md, Session 3, cut `cut-lib-format-money` hint
- **Owner:** test-runner
- **The line:** "hint: Format an integer cents value into `out` as a currency string like "$12.34" without using floating-point rounding."
- **Reading one:** Always format absolute value with two digits and prefix a minus sign for negatives (e.g., -$1.05).
- **Reading two:** Use parentheses for negatives or place the minus after the symbol (e.g., $-1.05), or special-case zero as "$0" without cents.
- **Why it matters:** UI string assertions will differ; without a pinned rule, either formatting can ship and fail tests written for the other.
- **Suggested wording:** Format with a leading "$", two digits of cents, and a leading "-" for negatives (e.g., $12.34, -$1.05; $0.00 for zero).

### W6 - Session 3 declares no builds despite adding API/UI cuts
- **Where:** spec.json, Session 3, "builds": []
- **Owner:** pack-writer
- **The line:** ""builds": [],"
- **Reading one:** Session 3 changes only library/helpers and does not “build” an endpoint or screen.
- **Reading two:** Session 3 also modifies ep-settlement (include filter) and sc-expenses (toggle/render), so it should list those under builds to match the plan and guide.
- **Why it matters:** The instructor guide and session plan can drift from the machine contract, making the Pack Writer’s narrative and timing misleading.
- **Suggested wording:** Declare Session 3 builds ep-settlement and sc-expenses to reflect the include filter and UI work.
