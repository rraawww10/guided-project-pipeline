import { prisma } from "@/lib/prisma"

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 501
  // TODO(cut-ep-skus-list-query): Put every SKU the store holds into `body` and set `status` to 200
  return Response.json(body, { status })
}
