import { nextTarget } from '@/lib/dispatch'
import { seed } from '@/lib/state'
import { step } from '@/lib/step'
import type { Scenario, SimState, Trace } from '@/lib/types'

/**
 * The run - spec.md, "The run - `runUntil(scenario, maxTicks)` in `lib/run.ts`".
 *
 * Each tick: hand the state to `nextTarget`, append that dispatched car's row
 * to `trace.rows`, advance the dispatched state through `step`. The run ends
 * COMPLETE on a dispatched car that is `idle` with `pending` empty, with that
 * final row appended, and INCOMPLETE the moment `trace.rows` reaches
 * `maxTicks`. `trace.served` is the last state's `served`.
 *
 * The `maxTicks` bound is what makes the loop provably finite rather than
 * hopefully finite, so it is tested at the top of the loop: a bound already
 * reached appends nothing more. A row that both completes the run and reaches
 * the bound is `complete` true - ambiguity.md W9 records that no criterion
 * reaches that coincidence, and this is the reading taken.
 *
 * This is `cut-run-until`. The fallback is declared above the marker and the
 * single `return` sits below it, so the generated skeleton still compiles.
 */
export function runUntil(scenario: Scenario, maxTicks: number): Trace {
  let trace: Trace = { rows: [], served: [], complete: false }
  // >>> CUT cut-run-until
  let state: SimState = seed(scenario)
  while (trace.rows.length < maxTicks) {
    const car = nextTarget(state)
    const dispatched: SimState = { ...state, car }
    trace.rows.push({
      tick: dispatched.tick,
      floor: car.floor,
      mode: car.mode,
      direction: car.mode === 'moving' ? car.direction : null,
    })
    trace.served = dispatched.served
    if (car.mode === 'idle' && dispatched.pending.length === 0) {
      trace.complete = true
      break
    }
    state = step(dispatched)
    trace.served = state.served
  }
  // <<< CUT cut-run-until
  return trace
}
