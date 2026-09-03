import type { Direction, Scenario, SimState } from '@/lib/types'

/**
 * The two seeds - spec.md, "Two seeds, and why there are two". Both shipped
 * written.
 *
 * `seed` is what `runUntil` folds from, so every dispatch decision in a trace
 * comes from `nextTarget`. `manualStart` is what the shaft page holds in
 * `useState`, so session 1 can step a car by hand with no dispatcher in
 * existence yet.
 */
export function seed(scenario: Scenario): SimState {
  return {
    tick: 0,
    car: { mode: 'idle', floor: scenario.start },
    pending: scenario.calls.map((call) => ({ floor: call.floor, tick: call.tick })),
    served: [],
  }
}

/**
 * Tick 0, a `moving` car at `scenario.start` aimed at `calls[0].floor` with the
 * direction that points at it, or an `idle` car for a scenario with no calls.
 *
 * This reads `calls[0]` straight out of the data: it computes no nearest floor
 * and no direction rule, so no part of session 2's policy is visible in session
 * 1's shipped code for a student to copy.
 */
export function manualStart(scenario: Scenario): SimState {
  const base = seed(scenario)
  const first = scenario.calls[0]
  if (first === undefined) return base
  const direction: Direction = first.floor < scenario.start ? 'down' : 'up'
  return { ...base, car: { mode: 'moving', floor: scenario.start, direction, target: first.floor } }
}
