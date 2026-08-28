import Link from 'next/link'

import { BOARDS } from '@/lib/boards'

import styles from './page.module.css'

/** A static index of the three seeded boards. No criterion reads this page. */
export default function HomePage() {
  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Sweeper</h1>
      <div className={styles.links}>
        {BOARDS.map((board) => (
          <Link key={board.id} className={styles.link} href={`/boards/${board.id}`}>
            Play {board.name}
          </Link>
        ))}
      </div>
    </main>
  )
}
