import { prisma } from "@/lib/prisma"

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 501
  // TODO(cut-ep-suggestions-calc): Build `body` as an array of { sku_id, name, on_hand, reorder_point, qty_to_order } where qty_to_order is max(0, reorder_point - on_hand), and set `status` to 200
  return Response.json(body, { status })
}
