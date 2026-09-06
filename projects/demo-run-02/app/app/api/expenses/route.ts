import { loadSeedExpenses } from "../../../lib/store";
import type { Expense } from "../../../lib/types";

export async function GET(): Promise<Response> {
  let body: Expense[] = [];
  let status = 501;
  // >>> CUT cut-api-expenses-list
  body = await loadSeedExpenses();
  status = 200;
  // <<< CUT cut-api-expenses-list
  return Response.json(body, { status });
}
