import { BalanceMap, Expense, Transfer } from "./types";

export function computeBalances(expenses: Expense[], included: Set<string>): BalanceMap {
  let out: BalanceMap = {};
  // Seed everyone present in included to 0 to ensure deterministic render order
  for (const person of included) {
    out[person] = 0;
  }
  // TODO(cut-lib-compute-balances): Compute each person's net in cents into `out` by adding amounts they paid and subtracting their share of each expense; divide an expense by the sum of participant weights (default 1) and subtract each share from that participant
  return out;
}

export function settleNaive(balances: BalanceMap): Transfer[] {
  let out: Transfer[] = [];
  // TODO(cut-lib-settle-naive): From a `balances` map, build `out` as a list of transfers by repeatedly matching the largest positive balance to the largest (most negative) balance and moving the smaller absolute amount; continue until no balances remain nonzero
  return out;
}

export function settleMinimal(balances: BalanceMap): Transfer[] {
  let out: Transfer[] = [];
  // TODO(cut-lib-settle-minimal): Produce `out` as a transfer list equivalent in totals to the naive result but ordered by amount descending, then payer asc, then payee asc; do not increase the number of transfers
  return out;
}
