/**
 * The tracked week.
 *
 * Every date in this project is derived from one `YYYY-MM-DD` string - the
 * store's `trackedDay` - and never from the real clock, so the same store
 * always gives the same seven days. All arithmetic goes through the UTC
 * accessors, so the answer does not move with the machine's timezone.
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
 * The seven `YYYY-MM-DD` strings of the Monday-to-Sunday week that contains
 * `trackedDay`, Monday first.
 */
export function weekDates(trackedDay: string): string[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let dates: string[] = []

  // >>> CUT cut-week-dates
  const tracked = utcDate(trackedDay)
  // getUTCDay is 0 on Sunday, so shifting by 6 makes Monday 0 and Sunday 6
  const sinceMonday = (tracked.getUTCDay() + 6) % 7
  const monday = utcDate(trackedDay)
  monday.setUTCDate(tracked.getUTCDate() - sinceMonday)

  dates = []
  for (let offset = 0; offset < 7; offset += 1) {
    const cell = utcDate(isoDay(monday))
    cell.setUTCDate(monday.getUTCDate() + offset)
    dates.push(isoDay(cell))
  }
  // <<< CUT cut-week-dates

  return dates
}
