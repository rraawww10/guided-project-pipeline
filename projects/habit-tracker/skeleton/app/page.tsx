'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

import type { HabitWeek } from '@/lib/store'

import styles from './page.module.css'

/**
 * The week board. One row per habit, seven day cells per row. It issues one
 * GET /api/habits when it mounts and never a second one - a click on a cell
 * rebuilds that one row from the toggle response.
 */
export default function BoardPage() {
  const [habits, setHabits] = useState<HabitWeek[]>([])

  useEffect(() => {
    let cancelled = false

    fetch('/api/habits')
      .then((response) => response.json())
      .then((data: HabitWeek[]) => {
        if (!cancelled) {
          setHabits(data)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  /**
   * A click on one cell. It flips that day through the toggle endpoint and
   * replaces that one row from the response, so the board never refetches the
   * whole list.
   */
  async function onCellClick(habitId: string, date: string): Promise<void> {
    // TODO(cut-board-click): Inside `onCellClick`, POST `{ date }` to `/api/habits/` plus the clicked habit id plus `/toggle`, and set the `habits` state to the same 4 rows in the same order with only the clicked habit replaced by the `HabitWeek` in the response body. Do not fetch `/api/habits` a second time.
  }

  return (
    <main className={styles.board}>
      <h1 className={styles.title}>Habit Tracker</h1>
      <p className={styles.week}>The tracked week, Monday to Sunday.</p>

      {habits.map((habit) => (
        <div
          key={habit.id}
          className={styles.row}
          data-testid="habit-row"
          data-habit-id={habit.id}
        >
          <span className={styles.name} data-testid="habit-name">
            {habit.name}
          </span>
          <span className={styles.streak} data-testid="habit-streak">
            {`Streak: ${habit.streak}`}
          </span>

          <div className={styles.days}>
            {habit.days.map((day) => (
              <button
                key={day.date}
                type="button"
                className={styles.cell}
                data-testid="day-cell"
                data-date={day.date}
                data-done={day.done ? 'true' : 'false'}
                onClick={() => {
                  void onCellClick(habit.id, day.date)
                }}
              >
                {day.date.slice(8)}
              </button>
            ))}
          </div>

          <Link className={styles.link} href={`/habits/${habit.id}`}>
            Open {habit.name}
          </Link>
        </div>
      ))}
    </main>
  )
}
