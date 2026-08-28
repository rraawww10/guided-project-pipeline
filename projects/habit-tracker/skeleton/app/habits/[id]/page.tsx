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

  // TODO(cut-habit-page): When the `/api/habits/[id]` response status is 404, set `missing` to `true`. Otherwise map `habit.days` into one `day-cell` element per entry, each with `data-date` set to that entry's date string and `data-done` set to the string `"true"` on a done entry and the string `"false"` on every other entry, and set `streakText` to `Streak: ` joined with `habit.streak`. Keep the `habit-name` element and the `habit-missing` element already in the file: when `missing` is `true` the page draws `habit-missing` and no `habit-name`, no `habit-streak` and no `day-cell`. Only a 404 sets `missing`; any other non-200 status leaves the page in its pre-response state, and nothing grades that.

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
