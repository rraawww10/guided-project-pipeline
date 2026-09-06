import { prisma } from "@/lib/prisma"

export async function GET(): Promise<Response> {
  let body: any = []
  let status = 501
  // >>> CUT cut-ep-skus-list-query
  const skus = await prisma.sku.findMany({ orderBy: { id: 'asc' } })
  body = skus
  status = 200
  // <<< CUT cut-ep-skus-list-query
  return Response.json(body, { status })
}
