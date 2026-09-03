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
  // TODO(cut-calls-ahead): Put into `ahead` every call in `live` the car reaches without turning round: floors above `state.car.floor` for a `dir` of `'up'`, floors below it for a `dir` of `'down'`, and all of `live` for a `dir` of `null`. Order them by distance from the car, closest first, a tie taken by the lower floor.

  let next: Car = { mode: 'idle', floor: state.car.floor }
  // TODO(cut-dispatch-target): Set `next` to a `moving` car standing at `state.car.floor`, its `target` taken from `ahead[0].floor` and falling back to the floor in `live` closest to the car - the lower floor on a tie - when `ahead` is empty, and its `direction` set to `'up'` for a target above the car and `'down'` for one below it.

  return next
}
