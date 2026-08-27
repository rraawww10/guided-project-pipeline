import { NextResponse } from 'next/server'

import { readAllRecipes } from '@/lib/store'
import type { Recipe } from '@/lib/types'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/recipes -> Recipe[], 200.
 *
 * Everything except the filter ships written, so this handler answers 200 from
 * session 1 onwards. With cut-api-recipes-filter open `shown` is still every
 * recipe the store gave back, which is what bare GET /api/recipes returns.
 */
export async function GET(request: Request): Promise<Response> {
  const all: Recipe[] = readAllRecipes()
  let shown: Recipe[] = all

  // TODO(cut-api-recipes-filter): Keep only the recipes whose title contains the q parameter, ignoring letter case, and whose tags include the tag parameter, and assign the result to `shown`; a parameter that is missing or empty narrows nothing.

  return NextResponse.json(shown)
}
