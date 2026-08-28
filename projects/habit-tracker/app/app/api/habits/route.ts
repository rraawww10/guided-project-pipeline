import { NextResponse } from 'next/server'

import { habitWeek, readStore } from '@/lib/store'
import type { HabitWeek } from '@/lib/store'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

/** GET /api/habits -> HabitWeek[], 200. Every habit, as the tracked week. */
export async function GET(): Promise<Response> {
  const store = readStore()
  const weeks: HabitWeek[] = store.habits.map((habit) =>
    habitWeek(habit, store.trackedDay),
  )

  return NextResponse.json(weeks)
}
