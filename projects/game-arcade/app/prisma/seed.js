/* eslint-disable no-console */
import { execSync } from 'node:child_process'
import { PrismaClient } from '@prisma/client'

async function main() {
  try {
    // Ensure the SQLite schema exists; skip generate which runs on install
    execSync('npx prisma db push --skip-generate', { stdio: 'ignore' })
  } catch (_) {
    // Ignore failures; tests call this as a best-effort reset.
  }
  const prisma = new PrismaClient()
  try {
    // Hard reset: delete all data for isolation between tests.
    await prisma.guess.deleteMany({})
    await prisma.game.deleteMany({})
  } catch (e) {
    // Swallow errors; reset should never break the test run.
  } finally {
    await prisma.$disconnect()
  }
}

main().catch(() => process.exit(0))
