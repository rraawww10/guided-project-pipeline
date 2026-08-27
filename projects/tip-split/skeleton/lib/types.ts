export type Bill = {
  /** kebab-case, and the URL segment: "anand-bhavan" */
  id: string
  place: string
  /** ISO calendar date, "2026-03-14" */
  date: string
  /** the bill before tip, in whole paise */
  totalPaise: number
  /** a whole-number percentage, 1..100 */
  tipPercent: number
  /** how many people it was split between when it was saved, 1..20 */
  people: number
}
