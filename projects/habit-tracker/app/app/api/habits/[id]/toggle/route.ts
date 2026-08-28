import { NextResponse } from 'next/server'

import { findHabit, habitWeek, readStore, writeStore } from '@/lib/store'
import type { HabitWeek, Store } from '@/lib/store'
import { toggleDate } from '@/lib/toggle'
import { weekDates } from '@/lib/week'

// the store is read and written on every request, so this handler is never
// prerendered
export const dynamic = 'force-dynamic'

/**
 * POST /api/habits/[id]/toggle, body { date } -> HabitWeek, 200; or { error }
 * with 400 when `date` is not one of the tracked week's seven days, or 404 when
 * the store holds no habit with that id. Neither error branch writes anything.
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id: habitId } = await params
  const payload = (await request.json().catch(() => null)) as { date?: unknown } | null

  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let body: HabitWeek | { error: string } = { error: 'not implemented' }
  let status = 501

  // >>> CUT cut-api-toggle
  const date = payload === null ? undefined : payload.date
  const store: Store = readStore()
  const week = weekDates(store.trackedDay)

  if (typeof date !== 'string' || !week.includes(date)) {
    body = { error: 'date must be one of the seven days of the tracked week' }
    status = 400
  } else {
    const habit = findHabit(store, habitId)

    if (habit === null) {
      body = { error: `no habit with the id ${habitId}` }
      status = 404
    } else {
      habit.doneDates = toggleDate(habit.doneDates, date)
      writeStore(store)
      body = habitWeek(habit, store.trackedDay)
      status = 200
    }
  }
  // <<< CUT cut-api-toggle

  return NextResponse.json(body, { status })
}
