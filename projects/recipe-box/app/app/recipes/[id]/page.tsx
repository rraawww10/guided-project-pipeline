'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

import type { Recipe } from '@/lib/types'

import RecipeView from './RecipeView'
import styles from './recipe.module.css'

export default function RecipePage() {
  const params = useParams<{ id: string }>()
  const id = params.id

  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [status, setStatus] = useState<'loading' | 'loaded' | 'not-found'>('loading')

  /**
   * The id comes from the route. A reply that is neither 200 nor 404 leaves
   * `status` on 'loading', so nothing but this block moves the screen off it.
   */
  useEffect(() => {
    // >>> CUT cut-recipe-fetch
    fetch(`/api/recipes/${id}`).then((response) => {
      if (response.status === 404) {
        setStatus('not-found')
        return
      }
      if (response.status !== 200) {
        return
      }
      response.json().then((data: Recipe) => {
        setRecipe(data)
        setStatus('loaded')
      })
    })
    // <<< CUT cut-recipe-fetch
  }, [id])

  if (status === 'loading') {
    return (
      <main className={styles.page}>
        <p className={styles.message}>Loading recipe</p>
      </main>
    )
  }

  if (status === 'not-found' || recipe === null) {
    return (
      <main className={styles.page}>
        <p className={styles.message}>Recipe not found</p>
        <Link href="/" className={styles.back}>
          Back to all recipes
        </Link>
      </main>
    )
  }

  return <RecipeView recipe={recipe} />
}
