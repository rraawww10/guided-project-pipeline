import Board from './Board'

/**
 * The one screen. A server component that reads the route id and hands it to
 * the board, which is where every fetch and every click lives.
 */
export default async function PuzzlePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  return <Board puzzleId={id} />
}
