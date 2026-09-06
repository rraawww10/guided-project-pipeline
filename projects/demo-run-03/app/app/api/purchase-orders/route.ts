import { prisma } from "@/lib/prisma"

export async function POST(req: Request): Promise<Response> {
  let body: any = { id: 0, itemsCount: 0, totalQty: 0 }
  let status = 501
  // >>> CUT cut-ep-po-create-transaction
  const json = await req.json().catch(() => ({})) as { lines?: { sku_id: number; qty: number }[] }
  const lines = Array.isArray(json.lines) ? json.lines.filter(l => typeof l?.sku_id === 'number' && typeof l?.qty === 'number') : []
  const result = await prisma.$transaction(async (tx) => {
    const po = await tx.purchaseOrder.create({ data: { created_label: 'manual' } })
    if (lines.length > 0) {
      await tx.purchaseOrderItem.createMany({ data: lines.map(l => ({ po_id: po.id, sku_id: l.sku_id, qty: l.qty })) })
    }
    const itemsCount = lines.length
    const totalQty = lines.reduce((sum, l) => sum + l.qty, 0)
    return { id: po.id, itemsCount, totalQty }
  })
  body = result
  status = 200
  // <<< CUT cut-ep-po-create-transaction
  return Response.json(body, { status })
}

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 501
  // >>> CUT cut-ep-po-list-aggregate
  const orders = await prisma.purchaseOrder.findMany({
    orderBy: { id: 'asc' },
    include: { items: true }
  })
  body = orders.map((po) => ({
    id: po.id,
    itemsCount: po.items.length,
    totalQty: po.items.reduce((s, it) => s + it.qty, 0)
  }))
  status = 200
  // <<< CUT cut-ep-po-list-aggregate
  return Response.json(body, { status })
}
