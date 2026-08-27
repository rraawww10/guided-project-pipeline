import { NextResponse } from 'next/server'

import { findRecipe } from '@/lib/store'
import type { Recipe } from '@/lib/types'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/recipes/[id] -> Recipe, 200; or { error }, 404 when the store holds
 * no recipe with that id.
 */
export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params

  // TODO(cut-api-recipe-get): Reply with the recipe as JSON and status 200 when the store finds it, and with status 404 and a JSON body holding an error field when the store finds nothing.

  // the return stays outside the markers, so the skeleton still compiles
  return NextResponse.json({ error: 'not implemented' }, { status: 501 })
}
