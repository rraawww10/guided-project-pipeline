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

  // >>> CUT cut-api-recipes-filter
  const { searchParams } = new URL(request.url)
  const q = searchParams.get('q') ?? ''
  const tag = searchParams.get('tag') ?? ''

  shown = all.filter((recipe) => {
    const matchesQuery = q === '' || recipe.title.toLowerCase().includes(q.toLowerCase())
    const matchesTag = tag === '' || recipe.tags.includes(tag)
    return matchesQuery && matchesTag
  })
  // <<< CUT cut-api-recipes-filter

  return NextResponse.json(shown)
}
