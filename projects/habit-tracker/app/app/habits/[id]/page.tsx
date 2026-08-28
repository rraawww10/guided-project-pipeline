'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { ReactElement } from 'react'

import type { HabitWeek } from '@/lib/store'

import styles from './page.module.css'

/**
 * One habit's page. Same week, same streak, display only - the board at / is
 * the screen that writes.
 */
export default function HabitDetailPage() {
  const params = useParams<{ id: string }>()
  const habitId = params.id

  const [habit, setHabit] = useState<HabitWeek | null>(null)
  const [status, setStatus] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    fetch(`/api/habits/${habitId}`).then(async (response) => {
      const data = response.status === 200 ? ((await response.json()) as HabitWeek) : null
      if (!cancelled) {
        setStatus(response.status)
        setHabit(data)
      }
    })

    return () => {
      cancelled = true
    }
  }, [habitId])

  // the fallbacks stay above the marker, so the skeleton still renders
  let missing = false
  let streakText = 'Streak: -1'
  let cells: ReactElement[] = []

  // >>> CUT cut-habit-page
  if (status === 404) {
    missing = true
  } else if (habit !== null) {
    streakText = `Streak: ${habit.streak}`
    cells = habit.days.map((day) => (
      <div
        key={day.date}
        className={styles.cell}
        data-testid="day-cell"
        data-date={day.date}
        data-done={day.done ? 'true' : 'false'}
      >
        {day.date.slice(8)}
      </div>
    ))
  }
  // <<< CUT cut-habit-page

  return (
    <main className={styles.page}>
      <Link className={styles.back} href="/">
        Back to the board
      </Link>

      {missing ? (
        <p className={styles.missing} data-testid="habit-missing">
          Habit not found
        </p>
      ) : null}

      {!missing && habit !== null ? (
        <section className={styles.habit}>
          <h1 className={styles.name} data-testid="habit-name">
            {habit.name}
          </h1>
          <p className={styles.streak} data-testid="habit-streak">
            {streakText}
          </p>
          <div className={styles.days}>{cells}</div>
        </section>
      ) : null}
    </main>
  )
}
