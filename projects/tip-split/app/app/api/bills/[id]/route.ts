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

  // >>> CUT cut-api-bill-get
  const bill: Bill | null = findBill(id)
  if (bill === null) {
    body = { error: `no bill with the id ${id}` }
    status = 404
  } else {
    body = bill
    status = 200
  }
  // <<< CUT cut-api-bill-get

  return Response.json(body, { status })
}
