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

  // TODO(cut-streak-count): Walk day by day backwards from `trackedDay` while each date is present in `doneDates`, and put the number of unbroken done days ending on `trackedDay` into `count`. Step with the UTC accessors or plain string arithmetic so the answer does not change with the machine's timezone, and leave `count` at 0 when `trackedDay` itself is absent from `doneDates`.

  return count
}
