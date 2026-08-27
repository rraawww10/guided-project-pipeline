import fs from 'node:fs'
import path from 'node:path'

import type { Recipe } from './types'

/**
 * The store is read-only. Both functions read data/recipes.json on every call
 * and neither writes.
 */

export function readAllRecipes(): Recipe[] {
  // the return stays outside the markers, so the skeleton still compiles
  let recipes: Recipe[] = []

  // >>> CUT cut-store-read-all
  const filePath = path.join(process.cwd(), 'data', 'recipes.json')
  const contents = fs.readFileSync(filePath, 'utf8')
  recipes = JSON.parse(contents) as Recipe[]
  // <<< CUT cut-store-read-all

  return recipes
}

export function findRecipe(id: string): Recipe | null {
  const recipes = readAllRecipes()

  // the return stays outside the markers, so the skeleton still compiles
  let recipe: Recipe | null = null

  // >>> CUT cut-store-find-one
  recipe = recipes.find((candidate) => candidate.id === id) ?? null
  // <<< CUT cut-store-find-one

  return recipe
}
