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

  // TODO(cut-week-dates): Fill `dates` with the 7 `YYYY-MM-DD` strings for Monday through Sunday of the week that contains `trackedDay`, oldest first. Step back from `trackedDay` to that week's Monday and forward from there, and use the UTC accessors (`getUTCDay`, `setUTCDate`) or plain string arithmetic so the 7 strings do not change with the machine's timezone. Read no clock: the same `trackedDay` always gives the same 7 strings.

  return dates
}
