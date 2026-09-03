import type { SimState } from '@/lib/types'

/**
 * One tick - spec.md, "One tick - `step(state)` in `lib/step.ts`".
 *
 * A total function. `tick` always advances by exactly one; the car's mode
 * decides the rest, and there are exactly three cases:
 *
 * 1. `moving` - the car advances one floor along `car.direction` and opens its
 *    doors only when it lands on `car.target`. This is `cut-step-move`.
 * 2. `doors` - the tick is spent with the doors open: every live call for this
 *    floor is served and the car goes `idle`. This is `cut-step-doors`.
 * 3. `idle` - nothing but the tick changes. Shipped written, because it is
 *    exactly the declared fallback of `next` below, so it needs no code at all.
 *
 * Re-dispatch is not `step`'s job. A car that has just closed its doors is
 * `idle`, and `nextTarget` sends it somewhere on the next tick.
 *
 * The fallback is declared above the markers and the single `return` sits below
 * them, so the generated skeleton still compiles.
 */
export function step(state: SimState): SimState {
  let next: SimState = { ...state, tick: state.tick + 1 }

  if (state.car.mode === 'moving') {
    const car = state.car
    // TODO(cut-step-move): The car is `moving`, so put into `next` a car one floor along `car.direction`: `'up'` adds one to `car.floor` and `'down'` takes one away. `car.target` decides only where the doors open, never which way the car travels. Landing on `car.target` gives the pair `{ mode: 'doors', floor: car.target }`, and otherwise a `moving` car at the new floor keeping the same `direction` and `target`. Leave `pending` and `served` as they are.
  } else if (state.car.mode === 'doors') {
    const car = state.car
    // TODO(cut-step-doors): The doors are open at `car.floor`, so put into `next` the state one tick on: each call in `state.pending` for that floor with a `tick` at or below `state.tick` joins `served` as `{ floor, calledAt: the call's own tick, servedAt: state.tick }` and leaves `pending`, and the car becomes `{ mode: 'idle', floor: car.floor }`.
  }

  return next
}
