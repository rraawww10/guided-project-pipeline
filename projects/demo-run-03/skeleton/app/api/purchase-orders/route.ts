import { prisma } from "@/lib/prisma"

export async function POST(req: Request): Promise<Response> {
  let body: any = { id: 0, itemsCount: 0, totalQty: 0 }
  let status = 501
  // TODO(cut-ep-po-create-transaction): In one transaction, insert a new PurchaseOrder with a fixed created_label (e.g. 'manual'), insert one PurchaseOrderItem per line, then set `body` to { id, itemsCount: number of lines, totalQty: sum of qty } and `status` to 200
  return Response.json(body, { status })
}

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 501
  // TODO(cut-ep-po-list-aggregate): Query purchase orders with an aggregate to produce { id, itemsCount, totalQty } for each order, write the array into `body`, and set `status` to 200
  return Response.json(body, { status })
}
