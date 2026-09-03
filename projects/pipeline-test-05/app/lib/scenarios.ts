import seeded from '@/data/scenarios.json'

import type { Scenario } from '@/lib/types'

/**
 * The seed - spec.md, "The seed - data/scenarios.json".
 *
 * Read-only. spec.md, Out of scope: "Persistence. Nothing is written at
 * runtime, so there is no live store", so this module is a typed read of the
 * JSON file and nothing else. Shipped written.
 *
 * Every array is copied on the way out, so nothing a caller does to a returned
 * `Scenario` reaches the module-level import. The five scenarios keep the
 * file's order, which is what c-1-1 reads, and each `calls` array keeps the
 * file's order too - spec.md: "**The `calls` column is deliberately not
 * registration order**", and that order is what grades `cut-calls-ahead`.
 */
function copy(scenario: Scenario): Scenario {
  return {
    id: scenario.id,
    name: scenario.name,
    floors: scenario.floors,
    start: scenario.start,
    calls: scenario.calls.map((call) => ({ floor: call.floor, tick: call.tick })),
  }
}

export function allScenarios(): Scenario[] {
  return (seeded as Scenario[]).map(copy)
}

export function findScenario(id: string): Scenario | undefined {
  const found = (seeded as Scenario[]).find((scenario) => scenario.id === id)
  return found === undefined ? undefined : copy(found)
}
