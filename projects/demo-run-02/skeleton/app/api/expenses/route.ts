import { loadSeedExpenses } from "../../../lib/store";
import type { Expense } from "../../../lib/types";

export async function GET(): Promise<Response> {
  let body: Expense[] = [];
  let status = 501;
  // TODO(cut-api-expenses-list): Put every expense from the seed store into `body` and set `status` to 200
  return Response.json(body, { status });
}
