import type { Quantity } from './types'

/**
 * Fractions are exact: a numerator and a denominator, both whole numbers. No
 * floating point anywhere, so 4 -> 6 -> 4 servings lands back on the stored
 * quantity with no drift.
 */

/** Ships written: the greatest common divisor of two whole numbers. */
export function gcd(a: number, b: number): number {
  let left = Math.abs(a)
  let right = Math.abs(b)

  while (right !== 0) {
    const remainder = left % right
    left = right
    right = remainder
  }

  return left === 0 ? 1 : left
}

/** Ships written: the same value with the numerator and denominator reduced. */
function reduceQuantity(quantity: Quantity): Quantity {
  const divisor = gcd(quantity.num, quantity.den)
  return { num: quantity.num / divisor, den: quantity.den / divisor }
}

/**
 * Ships written. Reduces first, then prints:
 * { num: 600, den: 1 } -> "600", { num: 1, den: 3 } -> "1/3",
 * { num: 3, den: 2 } -> "1 1/2".
 */
export function formatQuantity(quantity: Quantity): string {
  const { num, den } = reduceQuantity(quantity)

  if (den === 1) {
    return String(num)
  }

  if (num < den) {
    return `${num}/${den}`
  }

  const whole = Math.floor(num / den)
  return `${whole} ${num - whole * den}/${den}`
}

/**
 * The stored quantity written for `serves` people, rewritten for `servings`
 * people. Always computed from the stored value, never from the value on
 * screen, so there is nothing for rounding to accumulate in.
 */
export function scaleQuantity(stored: Quantity, serves: number, servings: number): Quantity {
  // TODO(cut-fraction-scale): Multiply the quantity by the target servings over the base servings, then divide the numerator and the denominator by their greatest common divisor.

  // the return stays outside the markers, so the skeleton still compiles
  return stored
}
