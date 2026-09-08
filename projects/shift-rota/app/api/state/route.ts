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
  // >>> CUT cut-ep-state-get
  const base = appDir();
  const live = path.join(base, "data", "state.json");
  const seed = path.join(base, "data", "state.seed.json");
  try {
    const existsLive = await fs
      .access(live)
      .then(() => true)
      .catch(() => false);
    if (existsLive) {
      body = await readJSON<State>(live);
    } else {
      body = await readJSON<State>(seed);
    }
    status = 200;
  } catch (e: any) {
    body = { error: e?.message || "read error" } as any;
    status = 500;
  }
  // <<< CUT cut-ep-state-get
  return Response.json(body as any, { status });
}

export async function POST(req: Request): Promise<Response> {
  let body: State | { error: string } = { error: "invalid" } as any;
  let status = 501;
  // >>> CUT cut-ep-state-post
  try {
    const incoming = (await req.json()) as State;
    const base = appDir();
    const live = path.join(base, "data", "state.json");
    await writeJSON<State>(live, incoming);
    body = incoming;
    status = 200;
  } catch (e: any) {
    body = { error: e?.message || "write error" } as any;
    status = 500;
  }
  // <<< CUT cut-ep-state-post
  return Response.json(body as any, { status });
}
