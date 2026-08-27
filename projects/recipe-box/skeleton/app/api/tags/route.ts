import { NextResponse } from 'next/server'

import { readAllRecipes } from '@/lib/store'
import type { Recipe } from '@/lib/types'

// the store is read on every request, so this handler is never prerendered
export const dynamic = 'force-dynamic'

/**
 * GET /api/tags -> string[], 200.
 *
 * Always every tag in the whole store, in alphabetical order. It never narrows
 * with the list's filter, so every chip stays on screen and stays clickable.
 */
export async function GET(): Promise<Response> {
  const all: Recipe[] = readAllRecipes()

  // TODO(cut-api-tags-list): Collect the tags of every recipe into one list without duplicates, sort it alphabetically and return it as a JSON array of strings.

  // the return stays outside the markers, so the skeleton still compiles
  return NextResponse.json({ error: 'not implemented' }, { status: 501 })
}
