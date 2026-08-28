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

  // TODO(cut-api-habit-get): Read the store with `readStore()` into `store` and look the habit up with `findHabit(store, habitId)`. When that gives a habit, set `body` to `habitWeek(habit, store.trackedDay)` and `status` to 200. When it gives `null`, set `body` to an object with an `error` key and `status` to 404.

  return NextResponse.json(body, { status })
}
