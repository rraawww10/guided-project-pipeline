import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  // Seed only if SKUs table is empty to preserve runtime state across restarts
  const count = await prisma.sku.count()
  if (count > 0) {
    return
  }
  const skus = [
    { name: 'Widget A', on_hand: 2, reorder_point: 5 },   // needs 3
    { name: 'Widget B', on_hand: 10, reorder_point: 8 },  // 0
    { name: 'Widget C', on_hand: 0, reorder_point: 4 },   // 4
    { name: 'Widget D', on_hand: 7, reorder_point: 7 },   // 0
    { name: 'Gadget E', on_hand: 1, reorder_point: 6 },   // 5
    { name: 'Gadget F', on_hand: 3, reorder_point: 3 },   // 0
    { name: 'Gizmo G', on_hand: 9, reorder_point: 12 },   // 3
    { name: 'Gizmo H', on_hand: 4, reorder_point: 4 }     // 0
  ]
  await prisma.sku.createMany({ data: skus })
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
