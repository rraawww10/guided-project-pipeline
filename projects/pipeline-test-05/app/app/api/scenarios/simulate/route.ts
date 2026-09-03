import { runUntil } from '@/lib/run'
import type { Call, Scenario } from '@/lib/types'

export const dynamic = 'force-dynamic'

/**
 * ep-simulate. 200 with a `Trace`, or 400 with the one error body.
 *
 * spec.md, Endpoints: validation "is exactly one predicate with one message".
 * The 400 below is the answer when the body is not valid JSON, when it carries
 * no `scenario` object with numeric `floors` and `start` and an array `calls`,
 * or when a call names a floor outside 1 to `floors`. Nothing else is
 * validated: `start` is trusted, because no fixture sends a bad one and
 * `maxTicks` bounds the run either way.
 *
 * `maxTicks` defaults to 100 when the body omits it, which is more than any
 * seeded scenario needs. ambiguity.md W5 notes that a `maxTicks` that is not a
 * number would take the bound away from a run that relies on it, so the default
 * is also what a non-number reads as - that is a type guard, not a second
 * validation rule, and it answers 200 exactly as an omitted key does.
 *
 * Shipped written - c-2-5 declares no cut. The whole of session 2's learning is
 * in `lib/dispatch.ts` and `lib/run.ts`.
 */
const ERROR_BODY = { error: 'scenario must carry floors, start and calls' }
const DEFAULT_MAX_TICKS = 100

type ScenarioBody = { id?: string; name?: string; floors: number; start: number; calls: Call[] }

function isScenarioBody(value: unknown): value is ScenarioBody {
  if (typeof value !== 'object' || value === null) return false
  const body = value as { floors?: unknown; start?: unknown; calls?: unknown }
  if (typeof body.floors !== 'number' || typeof body.start !== 'number') return false
  if (!Array.isArray(body.calls)) return false
  return body.calls.every((entry) => {
    if (typeof entry !== 'object' || entry === null) return false
    const call = entry as { floor?: unknown; tick?: unknown }
    if (typeof call.floor !== 'number' || typeof call.tick !== 'number') return false
    return call.floor >= 1 && call.floor <= (body.floors as number)
  })
}

export async function POST(request: Request): Promise<Response> {
  let raw: unknown
  try {
    raw = await request.json()
  } catch {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  if (typeof raw !== 'object' || raw === null) {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const envelope = raw as { scenario?: unknown; maxTicks?: unknown }
  if (!isScenarioBody(envelope.scenario)) {
    return Response.json(ERROR_BODY, { status: 400 })
  }

  const body = envelope.scenario
  const scenario: Scenario = {
    id: body.id ?? '',
    name: body.name ?? '',
    floors: body.floors,
    start: body.start,
    calls: body.calls,
  }
  const maxTicks =
    typeof envelope.maxTicks === 'number' && Number.isFinite(envelope.maxTicks)
      ? envelope.maxTicks
      : DEFAULT_MAX_TICKS

  return Response.json(runUntil(scenario, maxTicks))
}
