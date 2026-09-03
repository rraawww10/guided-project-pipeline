import { allScenarios } from '@/lib/scenarios'

export const dynamic = 'force-dynamic'

/**
 * ep-scenarios. The five seeded scenarios in the seed's own order, each
 * carrying `id`, `name`, `floors`, `start` and `calls`. Always 200.
 *
 * Shipped written - c-1-1 declares no cut, so this route and `lib/scenarios.ts`
 * tell the student the scaffolding is intact. The `calls` arrays are answered
 * in the file's order, which spec.md pins deliberately.
 */
export async function GET(): Promise<Response> {
  return Response.json(allScenarios())
}
