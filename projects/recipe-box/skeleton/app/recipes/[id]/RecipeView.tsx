'use client'

import Link from 'next/link'
import { useState } from 'react'
import type { ReactNode } from 'react'

import { formatQuantity, scaleQuantity } from '@/lib/fractions'
import type { Ingredient, Recipe } from '@/lib/types'

import styles from './recipe.module.css'

export default function RecipeView({ recipe }: { recipe: Recipe }) {
  // starts on the recipe's own stored serves, and mounts only once the recipe
  // has arrived, so recipe is never null when this initial value is read
  const [servings, setServings] = useState<number>(recipe.serves)

  /** The two stepper controls call this with servings - 1 and servings + 1. */
  function setServingsClamped(next: number) {
    // TODO(cut-recipe-servings): Put the requested number into the servings state, holding it at 1 when it would drop below 1 and at 24 when it would climb above 24.
  }

  /**
   * Rebuilt from the fetched recipe on every render, so the quantity a row
   * starts from is always the stored one. Nothing writes back into
   * recipe.ingredients, which is why 4 -> 6 -> 4 lands back on the recipe as
   * it was written.
   */
  const rows: Ingredient[] = recipe.ingredients.map((ingredient) => {
    const row: Ingredient = { ...ingredient }

    // TODO(cut-recipe-scale-quantity): Replace the quantity of the row copy by calling `scaleQuantity` with that ingredient's stored quantity, the recipe's serves count and the servings count on screen.

    return row
  })

  let ingredientRows: ReactNode[] = []

  // TODO(cut-recipe-rows): Render one ingredient-row element for every entry in rows, its text reading `formatQuantity` of that row's quantity, then the unit when that ingredient has one, then the item name.

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>{recipe.title}</h1>
        <div className={styles.tags}>
          {recipe.tags.map((tag) => (
            <span key={tag} className={styles.tag}>
              {tag}
            </span>
          ))}
        </div>
        <p className={styles.meta}>
          <span>{recipe.minutes} min</span>
          <span>Written for {recipe.serves}</span>
        </p>
      </header>

      <section className={styles.section}>
        <h2 className={styles.sectionHeading}>Servings</h2>
        <div className={styles.stepper}>
          <span className={styles.stepperLabel}>Scale the ingredients</span>
          <button
            type="button"
            aria-label="Fewer servings"
            className={styles.stepButton}
            onClick={() => setServingsClamped(servings - 1)}
          >
            &minus;
          </button>
          <span className={styles.servingsCount} data-testid="servings-count">
            {servings}
          </span>
          <button
            type="button"
            aria-label="More servings"
            className={styles.stepButton}
            onClick={() => setServingsClamped(servings + 1)}
          >
            +
          </button>
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionHeading}>Ingredients</h2>
        <ul className={styles.ingredients}>{ingredientRows}</ul>
      </section>

      <section className={styles.section}>
        <h2 className={styles.sectionHeading}>Steps</h2>
        <ol className={styles.steps}>
          {recipe.steps.map((step, index) => (
            <li key={index} className={styles.step} data-testid="step">
              {`${index + 1}. ${step}`}
            </li>
          ))}
        </ol>
      </section>

      <Link href="/" className={styles.back}>
        Back to all recipes
      </Link>
    </main>
  )
}
