/**
 * The flip. A pure function over a list of `YYYY-MM-DD` strings: it neither
 * reads the store nor mutates the array it is handed.
 */

/** `dates` with `date` added when it is absent and dropped when it is present. */
export function toggleDate(dates: string[], date: string): string[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let next: string[] = []

  // >>> CUT cut-toggle-dates
  next = dates.includes(date)
    ? dates.filter((candidate) => candidate !== date)
    : [...dates, date]
  // <<< CUT cut-toggle-dates

  return next
}
