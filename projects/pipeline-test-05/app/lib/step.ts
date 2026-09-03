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
    // >>> CUT cut-step-move
    const floor = car.direction === 'up' ? car.floor + 1 : car.floor - 1
    next = {
      ...next,
      car:
        floor === car.target
          ? { mode: 'doors', floor: car.target }
          : { mode: 'moving', floor, direction: car.direction, target: car.target },
    }
    // <<< CUT cut-step-move
  } else if (state.car.mode === 'doors') {
    const car = state.car
    // >>> CUT cut-step-doors
    const arriving = state.pending.filter((call) => call.floor === car.floor && call.tick <= state.tick)
    next = {
      ...next,
      car: { mode: 'idle', floor: car.floor },
      pending: state.pending.filter((call) => !(call.floor === car.floor && call.tick <= state.tick)),
      served: [
        ...state.served,
        ...arriving.map((call) => ({ floor: call.floor, calledAt: call.tick, servedAt: state.tick })),
      ],
    }
    // <<< CUT cut-step-doors
  }

  return next
}
