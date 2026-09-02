/**
 * The one reader of `data/games.json`. Both the route and the page go through
 * here, so nothing else in the project knows where the seed lives.
 *
 * Scoring is a pure read - nothing in this project writes the seed back - so
 * there is no cache to invalidate and no state to reset between requests.
 */
import { readFileSync } from "node:fs"
import path from "node:path"

import type { Game } from "./types"

/** The four seeded games, in the order the file lists them. */
export function allGames(): Game[] {
  const text = readFileSync(path.join(process.cwd(), "data", "games.json"), "utf8")
  return JSON.parse(text) as Game[]
}

/** The game carrying this id, or `undefined` when the id is not in the seed. */
export function findGame(id: string): Game | undefined {
  return allGames().find((game) => game.id === id)
}
