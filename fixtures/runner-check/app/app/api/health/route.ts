export async function GET(): Promise<Response> {
  // the return stays outside the markers, so the skeleton still compiles
  let body: { ok: boolean; items?: number } = { ok: false }
  let status = 501

  // >>> CUT cut-api-health
  body = { ok: true, items: 3 }
  status = 200
  // <<< CUT cut-api-health

  return Response.json(body, { status })
}
