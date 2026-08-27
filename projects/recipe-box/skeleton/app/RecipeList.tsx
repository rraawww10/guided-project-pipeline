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

    // TODO(cut-list-fetch): Ask the recipes endpoint for the list, passing the page query string straight through, and when the reply is a 200 and the ignore flag the wrapper declares is still clear, put the array it answers with into the recipes state and set the status to loaded.

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
    // TODO(cut-list-search-url): Build the next query parameters from the ones the page already has, so the tag parameter is left as it is, then set q to the text of the search box, or drop q when the box is empty, and hand the result to replaceQuery.
  }

  function onTagClick(tag: string) {
    // TODO(cut-list-tag-toggle): Build the next query parameters from the ones the page already has, so the q parameter is left as it is, then set tag to the clicked tag, or drop tag when the chip clicked is the one already active, and hand the result to replaceQuery.
  }

  let cards: ReactNode[] = []

  // TODO(cut-list-cards): Turn the recipes array into one recipe-card element per recipe and assign them to `cards`, each element a link to that recipe's page at /recipes/ followed by its id, holding its title, a card-tag element per tag, its minutes in a card-minutes element and its serves count in a card-serves element.

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
