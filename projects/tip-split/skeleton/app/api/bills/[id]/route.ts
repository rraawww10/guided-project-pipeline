import { findBill } from '@/lib/store'
import type { Bill } from '@/lib/types'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params

  // the return stays outside the markers, so the skeleton still compiles
  let body: unknown = { error: 'not implemented' }
  let status = 501

  // TODO(cut-api-bill-get): Put the bill into the response body and set the status to 200 when the store finds it; when the store finds nothing, put an object holding an error field into the response body and set the status to 404.

  return Response.json(body, { status })
}
