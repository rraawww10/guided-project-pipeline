Troubleshooting

Real errors students hit in this project and how to fix them.

Setup and boot
- "'next' is not recognized" or dev server won’t start — npm ci failed or node_modules is empty — Run npm ci again from app/, then npm run dev. An empty node_modules (only .bin) is not installed.
- Port 3000 already in use — Another process is running on 3000 — Stop it or set PORT=3001 before npm run dev and visit that port.
- Build fails on stale lock — package-lock.json and package.json disagree — Regenerate the lock with npm install --package-lock-only and re-run.

API
- /api/expenses returns 501 — status never set to 200 — Assign status = 200 after writing body.
- /api/settlement/naive returns [] — people Set built from payers only — Include both paidBy and every participant.
- TypeScript cannot find types in route files — Wrong import path depth — Use the exact imports already present at the top of each file; do not change them.

UI data loading
- Table stays empty but no error shows — setState done inside try before loaded is assigned — Keep a local loaded variable and only setItems in finally.
- Unhandled promise rejection in console — didn’t check resp.ok — Throw on non-2xx so the catch path sets error.

Balances and transfers
- Balances don’t update when include/exclude changes — missing dependency — The useMemo for balances must depend on items and included.
- Balances are off by a few dollars — subtracted the whole amount from each participant — Divide by the sum of weights among included participants and subtract only each share.
- Transfers grow beyond 4 items — re-sorting or duplicating in the greedy loop — Sort creditors/debtors once; each iteration moves min(creditor, debtor); increment indices on zero.

Toggles and recomputation
- Include/exclude has no effect — mutated Set in place — Always create a new Set(included), then add/delete and setIncluded(next).
- Minimal mode doesn’t change ordering — comparator missing tiebreaks — Sort by amount DESC, then payer (from) ASC, then payee (to) ASC.

Money formatting
- Probe shows "-6.15" or "$-6.15" — sign handling wrong — Build the string as "-$X.YY" for negatives and "$X.YY" otherwise; the UI prepends '+' for positives in balances only.
- Probe shows rounding errors like "-$6.14" — used floats — Keep integer math: dollars = Math.floor(abs/100), cents = abs % 100, left-pad cents to 2.
