/**
 * The streak.
 *
 * A pure function over a list of `YYYY-MM-DD` strings. It reads no clock and
 * no file, and it steps with the UTC accessors so the count does not move with
 * the machine's timezone.
 */

/** Midnight UTC on a `YYYY-MM-DD` string. */
function utcDate(day: string): Date {
  return new Date(`${day}T00:00:00.000Z`)
}

/** A `Date` back as a `YYYY-MM-DD` string. */
function isoDay(date: Date): string {
  return date.toISOString().slice(0, 10)
}

/**
 * How many consecutive done days end at `trackedDay`. A gap resets it, so a
 * `trackedDay` that is not itself done counts 0.
 */
export function streakOf(doneDates: string[], trackedDay: string): number {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let count = -1

  // >>> CUT cut-streak-count
  const done = new Set(doneDates)
  const cursor = utcDate(trackedDay)

  count = 0
  while (done.has(isoDay(cursor))) {
    count += 1
    cursor.setUTCDate(cursor.getUTCDate() - 1)
  }
  // <<< CUT cut-streak-count

  return count
}
