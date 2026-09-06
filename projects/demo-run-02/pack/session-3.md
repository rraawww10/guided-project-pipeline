# Session 3 - Minimal-mode, integer formatting, and include/exclude

Time: 40 minutes
Students start from: Session 2’s app: balances and naive transfers render in the UI; /api/settlement/naive returns JSON.
Students end with: formatMoney renders "-$6.15" at the probe; minimal toggle ON orders transfers by amount DESC then payer/payee; include/exclude immediately recomputes balances/transfers.

What they learn
- Integer-safe money formatting
- Stable sort and deterministic tie-breaking
- Local UI toggles that drive recomputation; immutable Set updates so hooks fire

Before you start
- Keep app/lib/money.ts, app/lib/settlement.ts and app/app/page.tsx open
- Point out the probe element [data-testid="money-sample"] and the minimal toggle in the UI

The plan
| Minutes | What you do |
|---|---|
| 0-4 | Recap: integers, greedy naive list, endpoint. Show the probe that will read "-$6.15". |
| 4-10 | Live-code formatMoney for integer cents with a leading minus and zero-padded cents. Verify the probe updates. |
| 10-18 | Live-code settleMinimal as “naive then order by amount DESC, then payer, then payee”. Explain deterministic tie-breaks. |
| 18-24 | Wire minimal mode in the UI: when ON, use minimal; when OFF, keep the naive list unchanged. |
| 24-30 | Implement the include/exclude toggle with a new Set each time (immutability) so recomputes fire. |
| 30-37 | Students test: turn minimal ON/OFF, uncheck Eve, confirm ordering and absence from rows. |
| 37-40 | Recap: formatting, ordering, toggles. Where this would go next in a bigger app. |

Cut points in this session
### cut-lib-format-money - lib/money.ts:3
- What students see: // TODO(cut-lib-format-money): Format integer cents into `out` as "$X.YY" with a leading minus for negatives (e.g. -615 → "-$6.15"); do not use floats
- What they write: Compute dollars = floor(abs/100) and cents = abs % 100; left-pad cents to 2; prefix with “-” for negatives.
- Teach it like this: “Never use floats; operate on integer cents and pad the remainder.”
- Passes when: c-3-1 goes green.

### cut-lib-settle-minimal - lib/settlement.ts:61
- What students see: // TODO(cut-lib-settle-minimal): Produce `out` as a transfer list equivalent in totals to the naive result but ordered by amount descending, then payer asc, then payee asc; do not increase the number of transfers
- What they write: Start from the naive list and return a copy sorted by amount DESC, then by from then to (both ASC).
- Teach it like this: “Order is display-only; we don’t change amounts or counts, only the sequence.”
- Passes when: c-3-2 and c-3-4 go green.

### cut-ui-use-minimal - app/page.tsx:75
- What students see: // TODO(cut-ui-use-minimal): When minimal mode is ON, write the refined transfer sequence into `transfers` using the minimal function; when it is OFF, preserve the naive sequence already derived
- What they write: In a useMemo depending on naiveTransfers, minimal, balances: if minimal is true, set transfers = settleMinimal(balances); else leave naiveTransfers.
- Teach it like this: “Switch the derivation based on the toggle; do not reorder naive results yourself.”
- Passes when: c-3-2 and c-3-5 go green.

### cut-ui-toggle-include - app/page.tsx:87
- What students see: // TODO(cut-ui-toggle-include): Toggle the given person's id in the `included` Set while preserving every other selection; the next recompute must use exactly the currently included people
- What they write: Create a new Set from the old one, add/remove the person, then setIncluded(newSet).
- Teach it like this: “Immutability: create a new Set so React sees the change and recomputes balances/transfers.”
- Passes when: c-3-3 goes green.

Where students get stuck
- “Probe doesn’t show -$6.15” — used floats or toFixed over dollars — Say: keep integer cents; compute dollars = Math.floor(abs/100) and rem = abs % 100; pad to 2.
- “Minimal ON looks the same as OFF” — forgot to call settleMinimal when the toggle is ON — Say: switch based on the checkbox; dependencies are naiveTransfers, minimal, balances.
- “Toggling a checkbox does nothing” — mutated the Set in place — Say: always create a new Set from the old one; then add/remove and setIncluded(next).
- “Order under minimal isn’t what the test expects” — comparator missing tie-breaks — Say: sort by amount DESC first, then payer ASC, then payee ASC.

Check before moving on
- Probe reads "-$6.15"; minimal ON shows the exact ordered sequence; turning minimal OFF makes the last item "Bob pays Cara $4.00"; unchecking Eve removes her from balances and transfers.
