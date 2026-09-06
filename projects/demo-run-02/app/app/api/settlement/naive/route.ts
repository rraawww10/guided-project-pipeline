import { loadSeedExpenses } from "../../../../lib/store";
import { computeBalances, settleNaive } from "../../../../lib/settlement";
import type { Transfer } from "../../../../lib/types";

export async function GET(): Promise<Response> {
  let body: Transfer[] = [];
  let status = 501;
  // >>> CUT cut-api-naive-settlement
  const expenses = await loadSeedExpenses();
  const people = new Set<string>();
  for (const e of expenses) {
    people.add(e.paidBy);
    for (const p of e.participants) people.add(p.person);
  }
  const balances = computeBalances(expenses, people);
  body = settleNaive(balances);
  status = 200;
  // <<< CUT cut-api-naive-settlement
  return Response.json(body, { status });
}
