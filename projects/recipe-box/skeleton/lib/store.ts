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

  // TODO(cut-store-read-all): Read the recipes JSON file from disk and return every recipe in it as an array of Recipe objects.

  return recipes
}

export function findRecipe(id: string): Recipe | null {
  const recipes = readAllRecipes()

  // the return stays outside the markers, so the skeleton still compiles
  let recipe: Recipe | null = null

  // TODO(cut-store-find-one): Return the recipe whose id matches the one asked for, or null when the store holds no recipe with that id.

  return recipe
}
