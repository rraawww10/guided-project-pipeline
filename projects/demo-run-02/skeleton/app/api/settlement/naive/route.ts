import { loadSeedExpenses } from "../../../../lib/store";
import { computeBalances, settleNaive } from "../../../../lib/settlement";
import type { Transfer } from "../../../../lib/types";

export async function GET(): Promise<Response> {
  let body: Transfer[] = [];
  let status = 501;
  // TODO(cut-api-naive-settlement): Populate `body` with the current naive settlement computed from the seeded expenses and set `status` to 200
  return Response.json(body, { status });
}
