import { NextResponse } from 'next/server'

import { findHabit, habitWeek, readStore } from '@/lib/store'
import type { HabitWeek, Store } from '@/lib/store'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/habits/[id] -> HabitWeek, 200; or { error }, 404 when the store
 * holds no habit with that id.
 */
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id: habitId } = await params

  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let body: HabitWeek | { error: string } = { error: 'not implemented' }
  let status = 501

  // >>> CUT cut-api-habit-get
  const store: Store = readStore()
  const habit = findHabit(store, habitId)

  if (habit === null) {
    body = { error: `no habit with the id ${habitId}` }
    status = 404
  } else {
    body = habitWeek(habit, store.trackedDay)
    status = 200
  }
  // <<< CUT cut-api-habit-get

  return NextResponse.json(body, { status })
}
