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

  // >>> CUT cut-solved-cells
  for (let index = 0; index < board.width * board.height; index += 1) {
    const count = counts[index]
    const mine = board.mines.includes(index)

    cells.push(
      <div
        key={index}
        className={styles.cell}
        data-testid="cell"
        data-index={index}
        data-count={count}
        data-mine={mine ? 'true' : 'false'}
      >
        {mine ? '*' : count === 0 ? '' : String(count)}
      </div>,
    )
  }
  // <<< CUT cut-solved-cells

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
