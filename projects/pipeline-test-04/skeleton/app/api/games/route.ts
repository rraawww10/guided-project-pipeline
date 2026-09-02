import { frames } from "@/lib/frames"
import { allGames } from "@/lib/store"

export const dynamic = "force-dynamic"

/**
 * ep-games-list. The four seeded games in the seed's own order, each carrying
 * its frame split alongside its flat roll list. Always 200.
 *
 * Shipped written - c-1-1 declares no cut, so this route and `lib/store.ts`
 * tell the student the scaffolding is intact.
 */
export async function GET(): Promise<Response> {
  const games = allGames().map((game) => ({
    id: game.id,
    name: game.name,
    rolls: game.rolls,
    frames: frames(game.rolls),
  }))
  return Response.json(games)
}
