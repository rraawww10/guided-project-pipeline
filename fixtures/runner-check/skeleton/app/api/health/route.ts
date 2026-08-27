export async function GET(): Promise<Response> {
  // the return stays outside the markers, so the skeleton still compiles
  let body: { ok: boolean; items?: number } = { ok: false }
  let status = 501

  // TODO(cut-api-health): Reply with a JSON body holding ok true and the item count, at status 200

  return Response.json(body, { status })
}
