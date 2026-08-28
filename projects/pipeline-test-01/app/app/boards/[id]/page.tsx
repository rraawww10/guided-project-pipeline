'use client'

import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { ReactElement } from 'react'

import type { BoardView } from '@/lib/boards'
import { revealFrom } from '@/lib/reveal'
import { gameStatus } from '@/lib/status'

import styles from './page.module.css'

/**
 * sc-play at /boards/[id] - the playable board, face down. One
 * GET /api/boards/[id] on mount and no other request: every reveal, every flag
 * and the status line are derived in the browser from that one response.
 */
export default function PlayBoardPage() {
  const params = useParams<{ id: string }>()
  const boardId = params.id

  const [view, setView] = useState<BoardView | null>(null)
  const [missing, setMissing] = useState(false)
  const [revealed, setRevealed] = useState<number[]>([])
  const [flagged, setFlagged] = useState<number[]>([])
  const [flagMode, setFlagMode] = useState(false)

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

  /**
   * One click on one cell. Flag mode decides which of the two branches it
   * takes, and each branch guards the other's state.
   */
  function onCellClick(index: number): void {
    if (view === null) {
      return
    }

    const board: BoardView = view

    if (flagMode) {
      // >>> CUT cut-flag-toggle
      // an open cell cannot be flagged
      if (!revealed.includes(index)) {
        setFlagged(
          flagged.includes(index)
            ? flagged.filter((flag) => flag !== index)
            : [...flagged, index],
        )
      }
      // <<< CUT cut-flag-toggle
    } else {
      // >>> CUT cut-play-click
      // a flag protects its cell from being opened
      if (!flagged.includes(index)) {
        const opened = revealFrom(board, index)

        setRevealed([
          ...revealed,
          ...opened.filter((cell) => !revealed.includes(cell)),
        ])
      }
      // <<< CUT cut-play-click
    }
  }

  // the not-found state draws board-missing and nothing else: no board-grid,
  // no cell, no flag-mode, no mines-left and no game-status
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

  // the fallbacks stay above the marker, so the skeleton reads
  // "Mines left: -1" and "Playing" whatever the board is
  let minesLeft = -1
  let statusText = 'Playing'

  // >>> CUT cut-play-status
  minesLeft = board.mines.length - flagged.length

  const status = gameStatus(board, revealed)
  statusText = status === 'won' ? 'Won' : status === 'lost' ? 'Lost' : 'Playing'
  // <<< CUT cut-play-status

  const openCells = new Set(revealed)
  const flaggedCells = new Set(flagged)
  const minedCells = new Set(board.mines)

  // the face-down grid: one cell per index of the range 0 .. width * height - 1,
  // never per entry of counts, so the number of cells on the page does not
  // depend on the neighbour scan
  const cells: ReactElement[] = []

  for (let index = 0; index < board.width * board.height; index += 1) {
    const isOpen = openCells.has(index)
    const isFlagged = flaggedCells.has(index)
    const isMine = minedCells.has(index)
    const count = board.counts[index]

    let text = ''

    if (!isOpen) {
      text = isFlagged ? 'F' : ''
    } else if (isMine) {
      text = '*'
    } else if (count !== 0) {
      text = String(count)
    }

    cells.push(
      <button
        key={index}
        type="button"
        className={styles.cell}
        data-testid="cell"
        data-index={index}
        data-revealed={isOpen ? 'true' : 'false'}
        data-flagged={isFlagged ? 'true' : 'false'}
        onClick={() => {
          onCellClick(index)
        }}
      >
        {text}
      </button>,
    )
  }

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>{board.name}</h1>

      <div className={styles.readouts}>
        <button
          type="button"
          className={styles.toggle}
          data-testid="flag-mode"
          onClick={() => {
            setFlagMode(!flagMode)
          }}
        >
          {`Flag mode: ${flagMode ? 'on' : 'off'}`}
        </button>
        <span data-testid="mines-left">{`Mines left: ${minesLeft}`}</span>
        <span data-testid="game-status">{statusText}</span>
      </div>

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
