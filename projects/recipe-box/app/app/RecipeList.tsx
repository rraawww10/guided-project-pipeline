'use client'

import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import type { Recipe } from '@/lib/types'

import styles from './page.module.css'

export default function RecipeList() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const qs = searchParams.toString()
  const activeTag = searchParams.get('tag') ?? ''

  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [status, setStatus] = useState<'loading' | 'loaded'>('loading')
  const [tags, setTags] = useState<string[]>([])

  /**
   * Ships written, outside every cut. The only thing that sets `tags`, and only
   * on a 200 reply, so the filter bar is empty until GET /api/tags answers.
   */
  useEffect(() => {
    let ignore = false

    fetch('/api/tags').then((response) => {
      if (response.status !== 200) {
        return
      }
      response.json().then((data: string[]) => {
        if (!ignore) {
          setTags(data)
        }
      })
    })

    return () => {
      ignore = true
    }
  }, [])

  /**
   * The URL drives the fetch: every change to `qs` refetches. Several replies
   * can be in flight at once, so the wrapper carries the stale-reply guard and
   * the block below writes to state only while `ignore` is still clear.
   */
  useEffect(() => {
    let ignore = false

    // >>> CUT cut-list-fetch
    fetch(`/api/recipes?${qs}`).then((response) => {
      if (response.status !== 200) {
        return
      }
      response.json().then((data: Recipe[]) => {
        if (ignore) {
          return
        }
        setRecipes(data)
        setStatus('loaded')
      })
    })
    // <<< CUT cut-list-fetch

    return () => {
      ignore = true
    }
  }, [qs])

  /** Ships written, outside every cut. Both URL cuts end by calling it. */
  function replaceQuery(params: URLSearchParams) {
    const s = params.toString()
    router.replace(s ? `/?${s}` : '/')
  }

  function onSearchChange(text: string) {
    // >>> CUT cut-list-search-url
    const next = new URLSearchParams(searchParams.toString())

    if (text === '') {
      next.delete('q')
    } else {
      next.set('q', text)
    }

    replaceQuery(next)
    // <<< CUT cut-list-search-url
  }

  function onTagClick(tag: string) {
    // >>> CUT cut-list-tag-toggle
    const next = new URLSearchParams(searchParams.toString())

    if (next.get('tag') === tag) {
      next.delete('tag')
    } else {
      next.set('tag', tag)
    }

    replaceQuery(next)
    // <<< CUT cut-list-tag-toggle
  }

  let cards: ReactNode[] = []

  // >>> CUT cut-list-cards
  cards = recipes.map((recipe) => (
    <Link
      key={recipe.id}
      href={`/recipes/${recipe.id}`}
      className={styles.card}
      data-testid="recipe-card"
    >
      <h2 className={styles.cardTitle}>{recipe.title}</h2>
      <div className={styles.cardTags}>
        {recipe.tags.map((tag) => (
          <span key={tag} className={styles.cardTag} data-testid="card-tag">
            {tag}
          </span>
        ))}
      </div>
      <div className={styles.cardMeta}>
        <span data-testid="card-minutes">{recipe.minutes} min</span>
        <span data-testid="card-serves">Serves {recipe.serves}</span>
      </div>
    </Link>
  ))
  // <<< CUT cut-list-cards

  return (
    <main className={styles.page}>
      <h1 className={styles.heading}>Recipe Box</h1>
      <p className={styles.tagline}>Eight recipes, filed by tag and re-scalable to any table.</p>

      <input
        type="text"
        className={styles.search}
        aria-label="Search recipes"
        placeholder="Search recipes"
        defaultValue={searchParams.get('q') ?? ''}
        onChange={(event) => onSearchChange(event.target.value)}
      />

      <div className={styles.filterBar}>
        {tags.map((tag) => (
          <button
            key={tag}
            type="button"
            data-testid="filter-tag"
            aria-pressed={tag === activeTag}
            className={tag === activeTag ? styles.filterTagActive : styles.filterTag}
            onClick={() => onTagClick(tag)}
          >
            {tag}
          </button>
        ))}
      </div>

      {status === 'loading' ? (
        <p className={styles.message}>Loading recipes</p>
      ) : recipes.length === 0 ? (
        <p className={styles.message}>No recipes match</p>
      ) : (
        <div className={styles.grid}>{cards}</div>
      )}
    </main>
  )
}
