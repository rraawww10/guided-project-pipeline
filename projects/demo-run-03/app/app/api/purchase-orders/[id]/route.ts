import { prisma } from "@/lib/prisma"

// Next 16 hands a route handler its params as a Promise. Awaiting it here,
// outside the markers, leaves the cut body exactly as it was - the block is
// about the join, not about how the framework delivers the id.
export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }): Promise<Response> {
  const params = await ctx.params
  let body: any = { id: 0, lines: [], itemsCount: 0, totalQty: 0 }
  let status = 501
  // >>> CUT cut-ep-po-detail-join
  const id = Number(params.id)
  const items = await prisma.purchaseOrderItem.findMany({
    where: { po_id: id },
    include: { sku: true },
    orderBy: { id: 'asc' }
  })
  const lines = items.map(it => ({ sku_id: it.sku_id, name: it.sku.name, qty: it.qty }))
  const itemsCount = lines.length
  const totalQty = lines.reduce((s, l) => s + l.qty, 0)
  body = { id, lines, itemsCount, totalQty }
  status = 200
  // <<< CUT cut-ep-po-detail-join
  return Response.json(body, { status })
}
