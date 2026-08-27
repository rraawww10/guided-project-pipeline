'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import { formatRupees } from '@/lib/money'
import type { Bill } from '@/lib/types'

import styles from './page.module.css'

export default function SavedBillsPage() {
  const [bills, setBills] = useState<Bill[]>([])
  const [status, setStatus] = useState<'loading' | 'loaded'>('loading')

  useEffect(() => {
    // TODO(cut-list-fetch): Ask the bills endpoint for the list, and when the reply is a 200 put the array it answers with into the bills state and move the status to loaded.
  }, [])

  let cards: ReactNode[] = []

  // TODO(cut-list-cards): Turn the bills array into one bill-card element per bill, in the order of the array, each one a link to that bill's page holding its place in a card-place element, its stored date string in a card-date element, its total formatted as rupees in a card-total element, and the word Split, its stored people count and the word ways in a card-people element; assign that array of card elements to the cards array declared above.

  return (
    <main className={styles.page}>
      <h1 className={styles.heading}>Saved bills</h1>
      {status === 'loading' ? (
        <p className={styles.loading}>Loading saved bills</p>
      ) : (
        <div className={styles.grid}>{cards}</div>
      )}
    </main>
  )
}
