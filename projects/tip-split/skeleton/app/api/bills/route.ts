import { readAllBills } from '@/lib/store'
import type { Bill } from '@/lib/types'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

export async function GET(): Promise<Response> {
  // the return stays outside the markers, so the skeleton still compiles
  let body: unknown = { error: 'not implemented' }
  let status = 501

  // TODO(cut-api-bills-list): Put every bill the store holds into the response body, and set the status to 200.

  return Response.json(body, { status })
}
