import { frames } from "@/lib/frames"
import { gameTotal, scoreGame } from "@/lib/score"
import { findGame } from "@/lib/store"
import { frameSymbols } from "@/lib/symbols"

export const dynamic = "force-dynamic"

/**
 * sc-game. A server component: it reads the seed through `lib/store.ts` rather
 * than fetching `/api/games`, and calls `scoreGame` and `gameTotal` in process
 * rather than posting to `/api/games/score`. There is no client state here.
 *
 * One frame box and one score cell per entry `frames()` returned, so a game
 * whose rolls ran out early renders fewer than ten of each. All of this markup
 * ships written; every cut in this project is in `lib/`.
 */
export default async function GamePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const game = findGame(id)

  if (game === undefined) {
    return (
      <main className="page">
        <h1>Tenpin</h1>
        <p className="missing" data-testid="no-game">{`No game with id ${id}`}</p>
      </main>
    )
  }

  const frameList = frames(game.rolls)
  const scores = scoreGame(game.rolls)
  const total = gameTotal(scores)

  return (
    <main className="page">
      <h1>{game.name}</h1>

      <ol className="plain card-grid">
        {frameList.map((frame, index) => (
          <li className="frame" key={index}>
            <span className="frame-number">{index + 1}</span>
            <span className="rolls" data-testid={`frame-${index + 1}`}>{frameSymbols(frame)}</span>
            <span className="score" data-testid={`total-${index + 1}`}>{scores[index] === null ? null : scores[index]}</span>
          </li>
        ))}
      </ol>

      <p className="total">
        total: <span data-testid="game-total">{total}</span>
      </p>
    </main>
  )
}
