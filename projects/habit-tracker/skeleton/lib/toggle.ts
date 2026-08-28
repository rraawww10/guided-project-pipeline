/**
 * The flip. A pure function over a list of `YYYY-MM-DD` strings: it neither
 * reads the store nor mutates the array it is handed.
 */

/** `dates` with `date` added when it is absent and dropped when it is present. */
export function toggleDate(dates: string[], date: string): string[] {
  // the fallback stays above the marker and the return below it, so the
  // skeleton still compiles
  let next: string[] = []

  // TODO(cut-toggle-dates): Inside `toggleDate`, assign to `next` a new array holding `dates` with every occurrence of `date` dropped when `dates` already contains it, and `dates` with `date` added when it does not. Every other string in `dates` stays in `next`, and `dates` itself is left unmutated.

  return next
}
