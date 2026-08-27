import { Suspense } from 'react'

import RecipeList from './RecipeList'

/**
 * A server component, because RecipeList is a client component that reads
 * useSearchParams and so must sit inside a Suspense boundary.
 */
export default function HomePage() {
  return (
    <Suspense fallback={<p>Loading recipes</p>}>
      <RecipeList />
    </Suspense>
  )
}
