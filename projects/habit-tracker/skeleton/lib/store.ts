import fs from 'node:fs'
import path from 'node:path'

import { streakOf } from './streak'
import { weekDates } from './week'

/**
 * The store: one JSON file under `data/`, read on every call and written
 * through `writeStore`. The three types live here, beside the functions that
 * produce them, and every module outside this one imports them with
 * `import type` so node's `fs` never reaches a client bundle.
 */

export type Habit = {
  id: string
  name: string
  doneDates: string[]
}

export type Store = {
  trackedDay: string
  habits: Habit[]
}

export type HabitWeek = {
  id: string
  name: string
  streak: number
  days: { date: string; done: boolean }[]
}

/** The live store and the immutable seed, both inside the running app. */
function storePath(): string {
  return path.join(process.cwd(), 'data', 'habits.json')
}

function seedPath(): string {
  return path.join(process.cwd(), 'data', 'habits.seed.json')
}

/**
 * Read the whole store. The seed is copied over `data/habits.json` when that
 * file is absent, and the file is re-read and re-parsed on every call, so
 * nothing is cached and deleting the file resets the world.
 */
export function readStore(): Store {
  if (!fs.existsSync(storePath())) {
    fs.copyFileSync(seedPath(), storePath())
  }

  return JSON.parse(fs.readFileSync(storePath(), 'utf8')) as Store
}

/** Write the whole store back to disk. */
export function writeStore(store: Store): void {
  fs.writeFileSync(storePath(), JSON.stringify(store, null, 2) + '\n', 'utf8')
}

/**
 * The one habit in this store with that id, or `null`. What comes back is an
 * element of `store.habits`, so mutating it and then calling `writeStore(store)`
 * persists the change.
 */
export function findHabit(store: Store, habitId: string): Habit | null {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let found: Habit | null = null

  // TODO(cut-store-find-habit): Inside `findHabit`, assign to `found` the one habit in `store.habits` whose `id` equals the `habitId` argument, and leave `found` as `null` when no habit in `store.habits` matches.

  return found
}

/** One habit as the tracked week: seven days, Monday first, plus its streak. */
export function habitWeek(habit: Habit, trackedDay: string): HabitWeek {
  const done = new Set(habit.doneDates)

  return {
    id: habit.id,
    name: habit.name,
    streak: streakOf(habit.doneDates, trackedDay),
    days: weekDates(trackedDay).map((date) => ({ date, done: done.has(date) })),
  }
}
