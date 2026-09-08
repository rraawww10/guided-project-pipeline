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
    // One fixture game with a fixed id, so a criterion that reads an EXISTING
    // game does not have to create one first. c-2-1 declares Cuts: [] - the
    // skeleton check therefore requires it to PASS on the student tree - but
    // its test built its own game through POST /api/games, which is cut by
    // cut-ep-games-create-save. On the skeleton the create returns no id and
    // c-2-1 died on KeyError 'id' before reaching the endpoint it is about.
    // Seeding the row moves that dependency out of the cut path.
    await prisma.game.create({ data: { id: 'seed-game-1', seed: 13579 } })
  } catch (e) {
    // Swallow errors; reset should never break the test run.
  } finally {
    await prisma.$disconnect()
  }
}

main().catch(() => process.exit(0))
