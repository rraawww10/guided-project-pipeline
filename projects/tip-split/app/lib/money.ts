/**
 * Money is whole paise everywhere. The only place a decimal point exists is
 * inside formatRupees, which builds a string.
 */

/** Ships written: 124000 -> "₹1240.00", 6129 -> "₹61.29", 34100 -> "₹341.00". */
export function formatRupees(paise: number): string {
  const rupees = Math.floor(paise / 100)
  const paisaPart = String(paise % 100).padStart(2, '0')
  return `₹${rupees}.${paisaPart}`
}

/** The tip in whole paise, rounded half up. */
export function tipPaise(totalPaise: number, tipPercent: number): number {
  let tip = 0

  // >>> CUT cut-money-tip
  tip = Math.floor((totalPaise * tipPercent + 50) / 100)
  // <<< CUT cut-money-tip

  return tip
}

/** One share per person, in person order, adding up to amountPaise exactly. */
export function splitPaise(amountPaise: number, people: number): number[] {
  let shares: number[] = []

  // >>> CUT cut-money-split
  const each = Math.floor(amountPaise / people)
  const leftover = amountPaise % people
  shares = Array.from({ length: people }, (_unused, index) =>
    index < leftover ? each + 1 : each,
  )
  // <<< CUT cut-money-split

  return shares
}
