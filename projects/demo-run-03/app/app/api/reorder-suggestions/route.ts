import { prisma } from "@/lib/prisma"

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 501
  // >>> CUT cut-ep-suggestions-calc
  const skus = await prisma.sku.findMany({ orderBy: { id: 'asc' } })
  body = skus.map((s) => ({
    sku_id: s.id,
    name: s.name,
    on_hand: s.on_hand,
    reorder_point: s.reorder_point,
    qty_to_order: Math.max(0, s.reorder_point - s.on_hand)
  }))
  status = 200
  // <<< CUT cut-ep-suggestions-calc
  return Response.json(body, { status })
}
