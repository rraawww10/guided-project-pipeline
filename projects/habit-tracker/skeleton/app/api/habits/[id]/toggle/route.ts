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

  // TODO(cut-api-toggle): Read `date` from the parsed JSON body and read the store with `readStore()` into `store`. When `date` is not one of the 7 strings from `weekDates(store.trackedDay)`, set `status` to 400 and `body` to an object with an `error` key, and write nothing to disk. Otherwise call `findHabit(store, habitId)`: on `null` set `status` to 404 and `body` to an object with an `error` key, and write nothing to disk; on a habit set that habit's `doneDates` to `toggleDate(habit.doneDates, date)`, persist the whole `store` with `writeStore(store)`, then set `body` to `habitWeek(habit, store.trackedDay)` and `status` to 200.

  return NextResponse.json(body, { status })
}
