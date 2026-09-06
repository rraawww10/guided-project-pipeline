# Session 2 - Netting works and a naive settlement renders

Time: 40 minutes
Students start from: Session 1’s app: /api/expenses returns the 4 items, the UI renders the table and totals-paid summary.
Students end with: Balances list shows 5 rows with exact texts; Proposed transfers shows 4 rows beginning “Eve pays Alice $13.00”; GET /api/settlement/naive returns the 4 transfers with the first equal to {"from":"Eve","to":"Alice","amountCents":1300}.

What they learn
- Pure functions over arrays/maps for netting
- Deterministic greedy matching for a naive settlement
- Wiring computed data into UI and exposing it via an endpoint

Before you start
- Keep app/app/page.tsx and app/lib/settlement.ts open
- Have app/app/api/settlement/naive/route.ts ready for the final endpoint wiring

The plan
| Minutes | What you do |
|---|---|
| 0-4 | Recap integers and the seed. Name the goal: balances and naive transfers in UI, then the API. |
| 4-14 | Live-code computeBalances: add what you paid, subtract your share per expense over included participants. Emphasise determinism. |
| 14-22 | Wire balances in the page (useMemo). Confirm the 5 exact balance texts and ordering by name. |
| 22-28 | Live-code settleNaive: split creditors/debtors, sort by amount DESC, walk the two lists, move the min each time. |
| 28-32 | Wire transfers into the page and show transfers total equals $30.00. |
| 32-36 | Expose the naive list via /api/settlement/naive. Build the people Set, compute balances, then settle. |
| 36-39 | Students finish and you circulate. Refresh UI and call the endpoint to sanity-check JSON. |
| 39-40 | Recap: balances and transfers now render; the endpoint answers JSON. Next: minimal ordering and toggles. |

Cut points in this session
### cut-lib-compute-balances - lib/settlement.ts:9
- What students see: // TODO(cut-lib-compute-balances): Compute each person's net in cents into `out` by adding amounts they paid and subtracting their share of each expense; divide an expense by the sum of participant weights (default 1) and subtract each share from that participant
- What they write: For each expense, add amountCents to the payer if included; compute the weight sum over included participants, subtract each participant’s integer share from their balance.
- Teach it like this: “Net = paid minus owed. Use integer shares and only over included names.”
- Passes when: c-2-1 goes green; also enables c-2-2 and c-2-4 downstream.

### cut-ui-set-balances - app/page.tsx:59
- What students see: // TODO(cut-ui-set-balances): Derive `balances` from the loaded `items` (and the current included people) using the provided netting function
- What they write: Call computeBalances(items, included) inside useMemo and return the map.
- Teach it like this: “Make it a pure derivation; depend on items and included so it recomputes when either changes.”
- Passes when: c-2-1 goes green.

### cut-lib-settle-naive - lib/settlement.ts:32
- What students see: // TODO(cut-lib-settle-naive): From a `balances` map, build `out` as a list of transfers by repeatedly matching the largest positive balance to the largest (most negative) balance and moving the smaller absolute amount; continue until no balances remain nonzero
- What they write: Split balances into creditors/debtors, sort both amount-descending (tie-break by name), then two-pointer walk, pushing a transfer of min(creditor, debtor) each step.
- Teach it like this: “Greedy and deterministic: largest settles first; break ties by name so tests can assert exact sequences.”
- Passes when: c-2-2 and c-2-3 go green in the UI; also needed for c-2-4.

### cut-ui-set-transfers - app/page.tsx:67
- What students see: // TODO(cut-ui-set-transfers): Derive `transfers` from the current `balances` using the naive settlement function and make it stable across renders
- What they write: In a useMemo keyed by balances, call settleNaive(balances) and return the array.
- Teach it like this: “Derive, don’t store. The result is stable for a given balances object.”
- Passes when: c-2-2 and c-2-3 go green.

### cut-api-naive-settlement - app/api/settlement/naive/route.ts:8
- What students see: // TODO(cut-api-naive-settlement): Populate `body` with the current naive settlement computed from the seeded expenses and set `status` to 200
- What they write: Load the seed, build a Set of all names (payers and participants), compute balances, then body = settleNaive(balances); set status = 200.
- Teach it like this: “The endpoint mirrors the UI derivation: seed → balances → transfers.”
- Passes when: c-2-4 goes green.

Where students get stuck
- “Balances don’t match the expected texts” — forgot to filter to included participants when subtracting shares — Say: filter participants to included before weight-sum and subtractions.
- “Balances don’t update after toggling later” — didn’t include `included` in the useMemo deps — Say: include both items and included so it recomputes.
- “Transfers total is wrong” — walking creditors/debtors without re-sorting or without tie-breakers — Say: sort once by amount DESC and break ties by name; then walk with two indices.
- “Endpoint returns []” — built the people Set from payers only — Say: add both paidBy and each participant to the Set.

Check before moving on
- UI shows 5 balance rows with exact strings and 4 transfer rows with the first “Eve pays Alice $13.00”; transfers total reads "$30.00"; GET /api/settlement/naive returns the 4 transfers with the first matching the spec.
