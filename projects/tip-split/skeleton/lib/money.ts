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

  // TODO(cut-money-tip): Work out the tip as the total times the tip percentage divided by a hundred, rounded half up, and put it into the whole-paise tip value declared above, without turning any value into rupees along the way.

  return tip
}

/** One share per person, in person order, adding up to amountPaise exactly. */
export function splitPaise(amountPaise: number, people: number): number[] {
  let shares: number[] = []

  // TODO(cut-money-split): Fill the shares array declared above with one share per person: give every person the amount divided by the number of people ignoring the remainder, then give one extra paisa each to as many people from the start of the list as there are paise left over.

  return shares
}
