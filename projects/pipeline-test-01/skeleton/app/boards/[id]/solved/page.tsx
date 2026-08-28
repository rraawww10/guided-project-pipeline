'use client'

import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { ReactElement } from 'react'

import type { BoardView } from '@/lib/boards'

import styles from './page.module.css'

/**
 * sc-solved at /boards/[id]/solved - the whole board face up, a mine glyph or
 * a neighbour count in every square. One GET /api/boards/[id] on mount and no
 * other request.
 */
export default function SolvedBoardPage() {
  const params = useParams<{ id: string }>()
  const boardId = params.id

  const [view, setView] = useState<BoardView | null>(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    let cancelled = false

    fetch(`/api/boards/${boardId}`).then(async (response) => {
      const loaded =
        response.status === 200 ? ((await response.json()) as BoardView) : null

      if (!cancelled) {
        setMissing(response.status === 404)
        setView(loaded)
      }
    })

    return () => {
      cancelled = true
    }
  }, [boardId])

  // the not-found state draws board-missing in place of the grid, so nothing
  // below can dereference a board that was never loaded
  if (missing) {
    return (
      <main className={styles.page}>
        <p className={styles.missing} data-testid="board-missing">
          Board not found
        </p>
      </main>
    )
  }

  // before the first response arrives the page draws no cells
  if (view === null) {
    return <main className={styles.page} />
  }

  const board: BoardView = view
  const counts = board.counts

  // the fallback stays above the marker, so the skeleton draws 0 cells
  const cells: ReactElement[] = []

  // TODO(cut-solved-cells): Fill `cells` with one element per index of `board`, in index order, each carrying `data-testid` `cell`, `data-index` set to that index, `data-count` set to that index's entry in `counts`, and `data-mine` set to the string `true` when `board.mines` holds the index and the string `false` when it does not. A mine cell shows the text `*`, a non-mine cell whose count is 0 shows empty text, and every other cell shows its count.

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>{`${board.name} - solved`}</h1>
      <div
        className={styles.grid}
        data-testid="board-grid"
        data-width={board.width}
        data-height={board.height}
        style={{ gridTemplateColumns: `repeat(${board.width}, 2rem)` }}
      >
        {cells}
      </div>
    </main>
  )
}
