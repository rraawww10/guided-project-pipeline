import { headers } from 'next/headers'

import type { Scenario } from '@/lib/types'

import Shaft from './Shaft'

export const dynamic = 'force-dynamic'

/**
 * sc-shaft at `/scenarios/[id]`.
 *
 * spec.md, Screens: "The page reads its scenario from `GET /api/scenarios` and
 * picks the matching `id`." That read happens here, on the server, before
 * anything renders, and the resolved `Scenario` is handed to the client
 * component that owns the `SimState`. ambiguity.md B1 (blocking, owner
 * test-runner) leaves the shape of this open between an effect in the client
 * component and a server resolve; the server resolve is taken, because it is
 * the only one of the three readings where the first paint already holds the
 * seeded state - so `car-floor` reads `2` on the first frame of
 * `/scenarios/above` and `no-scenario` renders only for an id the seed does not
 * hold. No loading state is reachable.
 *
 * The endpoint's own host is read off the request headers, so nothing here
 * hard-codes a port or an origin. All of this markup ships written; both of
 * session 1's cuts are in `lib/step.ts`.
 */
async function readScenarios(): Promise<Scenario[]> {
  const headerList = await headers()
  const host = headerList.get('host') ?? '127.0.0.1:3000'
  const protocol = headerList.get('x-forwarded-proto') ?? 'http'
  const response = await fetch(`${protocol}://${host}/api/scenarios`, { cache: 'no-store' })
  if (!response.ok) return []
  return (await response.json()) as Scenario[]
}

export default async function ScenarioPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const scenarios = await readScenarios()
  const scenario = scenarios.find((entry) => entry.id === id)

  if (scenario === undefined) {
    return (
      <main className="page">
        <h1>Lift</h1>
        <p className="missing" data-testid="no-scenario">{`No scenario with id ${id}`}</p>
      </main>
    )
  }

  return <Shaft scenario={scenario} />
}
