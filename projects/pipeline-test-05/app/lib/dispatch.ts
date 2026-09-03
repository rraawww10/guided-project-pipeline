import type { Call, Car, Direction, SimState } from '@/lib/types'

/**
 * The policy - spec.md, "The policy - `nextTarget(state)` in `lib/dispatch.ts`".
 *
 * The policy is arguable, so it is written down as ONE ORDERED PROCEDURE and
 * the first rule that applies wins:
 *
 * 1. `live` is the calls in `state.pending` with `tick <= state.tick`, in the
 *    scenario's array order. With `live` empty the car is idle. Shipped written.
 * 2. With a call in `live` at `car.floor`, the doors open there. Shipped
 *    written, and it is what makes a call registered at tick `t` for the floor
 *    the car is standing on at tick `t` a pickup rather than a skip.
 * 3. `ahead` is every call in `live` the car reaches without turning round,
 *    closest first. This is `cut-calls-ahead`.
 * 4. `ahead` non-empty keeps the car going; `ahead` empty reverses it. This is
 *    `cut-dispatch-target`.
 *
 * `runUntil` consults this once per tick, which is what makes "serve calls in
 * passing order" fall out: a call that arrives while the car is in flight is
 * considered again on the very next tick.
 *
 * Both cuts sit below their fallbacks and the single `return` stays outside
 * every marker pair, so the generated skeleton still compiles.
 */
export function nextTarget(state: SimState): Car {
  const live = state.pending.filter((call) => call.tick <= state.tick)
  if (live.length === 0) return { mode: 'idle', floor: state.car.floor }
  if (live.some((call) => call.floor === state.car.floor)) return { mode: 'doors', floor: state.car.floor }

  const dir: Direction | null = state.car.mode === 'moving' ? state.car.direction : null

  let ahead: Call[] = []
  // >>> CUT cut-calls-ahead
  ahead = live
    .filter((call) => {
      if (dir === 'up') return call.floor > state.car.floor
      if (dir === 'down') return call.floor < state.car.floor
      return true
    })
    .sort(
      (a, b) =>
        Math.abs(a.floor - state.car.floor) - Math.abs(b.floor - state.car.floor) || a.floor - b.floor,
    )
  // <<< CUT cut-calls-ahead

  let next: Car = { mode: 'idle', floor: state.car.floor }
  // >>> CUT cut-dispatch-target
  const nearest = live
    .slice()
    .sort(
      (a, b) =>
        Math.abs(a.floor - state.car.floor) - Math.abs(b.floor - state.car.floor) || a.floor - b.floor,
    )
  const target = ahead.length > 0 ? ahead[0].floor : nearest[0].floor
  next = {
    mode: 'moving',
    floor: state.car.floor,
    direction: target > state.car.floor ? 'up' : 'down',
    target,
  }
  // <<< CUT cut-dispatch-target

  return next
}
