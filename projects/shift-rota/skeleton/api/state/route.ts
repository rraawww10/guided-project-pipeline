import { promises as fs } from "fs";
import path from "path";
import { State } from "../../lib/types";

function appDir(): string {
  return process.env.APP_DIR || process.cwd();
}

async function readJSON<T>(p: string): Promise<T> {
  const data = await fs.readFile(p, "utf-8");
  return JSON.parse(data) as T;
}

async function writeJSON<T>(p: string, v: T): Promise<void> {
  await fs.mkdir(path.dirname(p), { recursive: true });
  await fs.writeFile(p, JSON.stringify(v, null, 2), "utf-8");
}

export async function GET(): Promise<Response> {
  let body: State | { error: string } = { error: "not found" } as any;
  let status = 501;
  // TODO(cut-ep-state-get): Read data/state.json when it exists, otherwise read data/state.seed.json, write the parsed State object into `body` and set `status` to 200
  return Response.json(body as any, { status });
}

export async function POST(req: Request): Promise<Response> {
  let body: State | { error: string } = { error: "invalid" } as any;
  let status = 501;
  // TODO(cut-ep-state-post): Read the request JSON into a typed State object, write that object to data/state.json, copy it into `body` and set `status` to 200
  return Response.json(body as any, { status });
}
