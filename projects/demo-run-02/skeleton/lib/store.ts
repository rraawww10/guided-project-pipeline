import { readFile } from "node:fs/promises";
import path from "node:path";
import { Expense } from "./types";

function getAppDir(): string {
  // APP_DIR provided by the pipeline; fall back to CWD for student runs
  return process.env.APP_DIR || process.cwd();
}

export async function loadSeedExpenses(): Promise<Expense[]> {
  const appDir = getAppDir();
  const seedPath = path.join(appDir, "data", "expenses.seed.json");
  const raw = await readFile(seedPath, { encoding: "utf-8" });
  const parsed = JSON.parse(raw);
  const expenses: Expense[] = parsed.expenses;
  return expenses;
}
