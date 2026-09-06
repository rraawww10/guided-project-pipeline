import { prisma } from "@/lib/prisma"

// Next 16 hands a route handler its params as a Promise. Awaiting it here,
// outside the markers, leaves the cut body exactly as it was - the block is
// about the join, not about how the framework delivers the id.
export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  const params = await ctx.params
  let body: any = { id: 0, lines: [], itemsCount: 0, totalQty: 0 }
  let status = 501
  // TODO(cut-ep-po-detail-join): Query a single purchase order’s lines joined to SKU names, compute itemsCount and totalQty, write { id, lines, itemsCount, totalQty } into `body`, and set `status` to 200
  return Response.json(body, { status })
}
