// Real route handlers, defined here because Next only registers handlers that
// are DECLARED in a file under the app directory. The previous version was
// `export { GET, POST } from "../../../api/state/route"`, and a re-export is
// not picked up: `next build` listed only /, /_not-found and /script, so
// /api/state 404'd. That single 404 failed all 14 criteria - the two API ones
// directly, and every UI one because page.tsx throws "failed to load" on mount
// when the fetch is not ok, so no testid ever renders.
//
// The implementation stays in app/api/state/route.ts because spec.json places
// cut-ep-state-get and cut-ep-state-post in that file; moving it would put the
// cut markers somewhere the cutter does not look. This wrapper only forwards.
import { GET as getState, POST as postState } from "../../../api/state/route";

export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  return getState();
}

export async function POST(req: Request): Promise<Response> {
  return postState(req);
}
