// Seed the SQLite database with deterministic data
const { PrismaClient } = require('@prisma/client')

const prisma = new PrismaClient()

async function main() {
  // Assets
  const assets = [
    { symbol: 'AAPL', name: 'Apple Inc.', lotSize: 1 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', lotSize: 1 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', lotSize: 1 },
    { symbol: 'TSLA', name: 'Tesla, Inc.', lotSize: 1 }
  ]

  for (const a of assets) {
    await prisma.asset.upsert({
      where: { symbol: a.symbol },
      update: { name: a.name, lotSize: a.lotSize },
      create: a
    })
  }

  // Prices (in cents)
  const prices = {
    AAPL: 19500,
    MSFT: 41000,
    GOOGL: 14500,
    TSLA: 25000
  }

  for (const [symbol, priceCents] of Object.entries(prices)) {
    await prisma.price.upsert({
      where: { assetSymbol: symbol },
      update: { priceCents },
      create: { assetSymbol: symbol, priceCents }
    })
  }

  // Holdings (shares)
  const holdings = {
    AAPL: 20,
    MSFT: 8,
    GOOGL: 30,
    TSLA: 5
  }

  for (const [symbol, shares] of Object.entries(holdings)) {
    await prisma.holding.upsert({
      where: { assetSymbol: symbol },
      update: { shares },
      create: { assetSymbol: symbol, shares }
    })
  }

  // Targets (weights that sum to 1.0)
  const targets = {
    AAPL: 0.3,
    MSFT: 0.3,
    GOOGL: 0.25,
    TSLA: 0.15
  }

  for (const [symbol, weight] of Object.entries(targets)) {
    await prisma.target.upsert({
      where: { assetSymbol: symbol },
      update: { weight },
      create: { assetSymbol: symbol, weight }
    })
  }

  // Default budget setting
  await prisma.setting.upsert({
    where: { key: 'budgetCents' },
    update: { value: String(100000) }, // $1000.00
    create: { key: 'budgetCents', value: String(100000) }
  })
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
