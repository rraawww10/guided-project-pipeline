import { redirect } from 'next/navigation'

// there is no index page: a puzzle is reached by its id, and / opens on one
export default function HomePage() {
  redirect('/puzzles/boat')
}
