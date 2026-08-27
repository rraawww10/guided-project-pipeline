/**
 * The shapes data/recipes.json holds, shared by the route handlers and the
 * screens. Nothing here is written back to disk.
 */

/** A quantity as whole numbers, stored already reduced, with den >= 1. */
export type Quantity = {
  num: number
  den: number
}

export type Ingredient = {
  /** "olive oil" */
  item: string
  /** 2 tbsp is { num: 2, den: 1 } */
  quantity: Quantity
  /** "g", "tbsp", "tsp", "cup", "clove"; "" for a plain count */
  unit: string
}

export type Recipe = {
  /** kebab-case, and the URL segment: "lemon-garlic-pasta" */
  id: string
  title: string
  /** one or more of baking, one-pot, quick, spicy, vegetarian */
  tags: string[]
  minutes: number
  /** the servings the stored quantities are written for */
  serves: number
  ingredients: Ingredient[]
  steps: string[]
}
