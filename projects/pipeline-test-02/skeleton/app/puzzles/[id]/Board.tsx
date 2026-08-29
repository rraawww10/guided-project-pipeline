'use client'

import { useEffect, useRef, useState } from 'react'

import type { Cell, CheckResult, LineStatus } from '@/lib/nonogram'
import type { Puzzle } from '@/lib/puzzles'

import styles from './board.module.css'

/**
 * One board. It fetches the three puzzles once on mount, draws the one the
 * route names, and posts the whole grid to the check endpoint on every click.
 *
 * A clue keeps the status it is already showing until a response is applied, and
 * a response that lands after a later click has already been sent is dropped, so
 * a slow answer never repaints the board with a stale one.
 */
export default function Board({ puzzleId }: { puzzleId: string }) {
  const [puzzles, setPuzzles] = useState<Puzzle[] | null>(null)
  const [grid, setGrid] = useState<Cell[][]>([])
  const [result, setResult] = useState<CheckResult | null>(null)
  const sent = useRef(0)

  useEffect(() => {
    let cancelled = false

    fetch('/api/puzzles').then(async (response) => {
      if (!response.ok) {
        return
      }

      const data = (await response.json()) as Puzzle[]

      if (cancelled) {
        return
      }

      const found = data.find((entry) => entry.id === puzzleId)

      setPuzzles(data)

      if (found !== undefined) {
        setGrid(
          Array.from({ length: found.size }, () =>
            Array.from({ length: found.size }, (): Cell => 'empty'),
          ),
        )
      }
    })

    return () => {
      cancelled = true
    }
  }, [puzzleId])

  async function sendCheck(next: Cell[][]) {
    const seq = sent.current + 1
    sent.current = seq

    const response = await fetch(`/api/puzzles/${puzzleId}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ grid: next }),
    })

    if (!response.ok) {
      return
    }

    const data = (await response.json()) as CheckResult

    // a later click has already been sent, so this answer is out of date
    if (seq === sent.current) {
      setResult(data)
    }
  }

  function handleCellClick(r: number, c: number) {
    // the fallback stays above the marker, so a click still runs a check while
    // the cycle is unwritten
    let updated: Cell[][] = grid

    // TODO(cut-cell-cycle): Set `updated` to a fresh copy of `grid` in which only the cell at row `r` and column `c` moves one step along `empty` then `filled` then `crossed` then back to `empty`. Every other cell keeps the state it had, and `grid` itself is not mutated. The `setGrid` call and the POST to /api/puzzles/<id>/check sit below the closing marker and are already written, so this assignment is the whole task.

    setGrid(updated)
    void sendCheck(updated)
  }

  if (puzzles === null) {
    return (
      <main className={styles.page}>
        <p className={styles.loading} data-testid="board-loading">
          Loading
        </p>
      </main>
    )
  }

  const puzzle = puzzles.find((entry) => entry.id === puzzleId)

  if (puzzle === undefined) {
    return (
      <main className={styles.page}>
        <p className={styles.missing} data-testid="puzzle-missing">
          Puzzle not found
        </p>
      </main>
    )
  }

  const statusOf = (line: LineStatus[] | undefined, index: number): LineStatus =>
    line === undefined ? 'open' : line[index] ?? 'open'

  return (
    <main className={styles.page}>
      <h1 className={styles.title} data-testid="puzzle-title">
        {puzzle.title}
      </h1>

      <div className={styles.board}>
        <div className={styles.colStrip}>
          <div className={styles.corner} aria-hidden="true" />
          {puzzle.colClues.map((clue, c) => (
            <div
              key={`col-${c}`}
              className={styles.clue}
              data-testid={`col-clue-${c}`}
              data-status={statusOf(result?.cols, c)}
            >
              {clue.join(' ')}
            </div>
          ))}
        </div>

        <div className={styles.lower}>
          <div className={styles.rowStrip}>
            {puzzle.rowClues.map((clue, r) => (
              <div
                key={`row-${r}`}
                className={styles.clue}
                data-testid={`row-clue-${r}`}
                data-status={statusOf(result?.rows, r)}
              >
                {clue.join(' ')}
              </div>
            ))}
          </div>

          <div className={styles.grid}>
            {grid.map((row, r) => (
              <div key={`line-${r}`} className={styles.line}>
                {row.map((state, c) => (
                  <button
                    key={`cell-${c}`}
                    type="button"
                    className={styles.cell}
                    data-testid={`cell-${r}-${c}`}
                    data-state={state}
                    aria-label={`row ${r + 1}, column ${c + 1}`}
                    onClick={() => handleCellClick(r, c)}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {result !== null && result.solved ? (
        <p className={styles.banner} data-testid="solved-banner">
          Solved
        </p>
      ) : null}
    </main>
  )
}
