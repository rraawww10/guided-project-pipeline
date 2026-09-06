import { BalanceMap, Expense, Transfer } from "./types";

export function computeBalances(expenses: Expense[], included: Set<string>): BalanceMap {
  let out: BalanceMap = {};
  // Seed everyone present in included to 0 to ensure deterministic render order
  for (const person of included) {
    out[person] = 0;
  }
  // >>> CUT cut-lib-compute-balances
  for (const exp of expenses) {
    if (included.has(exp.paidBy)) {
      out[exp.paidBy] = (out[exp.paidBy] || 0) + exp.amountCents;
    }
    // participants that are included
    const parts = exp.participants.filter((p) => included.has(p.person));
    const weightSum = parts.reduce((s, p) => s + (p.weight ?? 1), 0);
    if (weightSum > 0) {
      for (const p of parts) {
        const w = p.weight ?? 1;
        // Integer-safe share: divide evenly when the seed allows; weights are whole numbers
        const share = Math.round((exp.amountCents * w) / weightSum);
        out[p.person] = (out[p.person] || 0) - share;
      }
    }
  }
  // <<< CUT cut-lib-compute-balances
  return out;
}

export function settleNaive(balances: BalanceMap): Transfer[] {
  let out: Transfer[] = [];
  // >>> CUT cut-lib-settle-naive
  const creditors: { person: string; amount: number }[] = [];
  const debtors: { person: string; amount: number }[] = [];
  for (const [person, amt] of Object.entries(balances)) {
    if (amt > 0) creditors.push({ person, amount: amt });
    else if (amt < 0) debtors.push({ person, amount: -amt });
  }
  // sort: largest first
  creditors.sort((a, b) => b.amount - a.amount || a.person.localeCompare(b.person));
  debtors.sort((a, b) => b.amount - a.amount || a.person.localeCompare(b.person));
  let ci = 0, di = 0;
  while (ci < creditors.length && di < debtors.length) {
    const c = creditors[ci];
    const d = debtors[di];
    const move = Math.min(c.amount, d.amount);
    if (move > 0) {
      out.push({ from: d.person, to: c.person, amountCents: move });
      c.amount -= move;
      d.amount -= move;
    }
    if (c.amount === 0) ci++;
    if (d.amount === 0) di++;
  }
  // <<< CUT cut-lib-settle-naive
  return out;
}

export function settleMinimal(balances: BalanceMap): Transfer[] {
  let out: Transfer[] = [];
  // >>> CUT cut-lib-settle-minimal
  // Start from the naive list and apply a deterministic ordering: amount DESC, then payer ASC, then payee ASC
  const base = settleNaive(balances);
  out = base.slice().sort((a, b) => {
    return (
      b.amountCents - a.amountCents ||
      a.from.localeCompare(b.from) ||
      a.to.localeCompare(b.to)
    );
  });
  // <<< CUT cut-lib-settle-minimal
  return out;
}
