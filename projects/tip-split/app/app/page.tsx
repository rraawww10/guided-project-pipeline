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
    // >>> CUT cut-list-fetch
    fetch('/api/bills').then((response) => {
      if (response.status === 200) {
        response.json().then((data: Bill[]) => {
          setBills(data)
          setStatus('loaded')
        })
      }
    })
    // <<< CUT cut-list-fetch
  }, [])

  let cards: ReactNode[] = []

  // >>> CUT cut-list-cards
  cards = bills.map((bill) => (
    <Link
      key={bill.id}
      href={`/bills/${bill.id}`}
      className={styles.card}
      data-testid="bill-card"
    >
      <div className={styles.cardPlace} data-testid="card-place">
        {bill.place}
      </div>
      <div className={styles.cardDate} data-testid="card-date">
        {bill.date}
      </div>
      <div className={styles.cardTotal} data-testid="card-total">
        {formatRupees(bill.totalPaise)}
      </div>
      <div className={styles.cardPeople} data-testid="card-people">
        Split {bill.people} ways
      </div>
    </Link>
  ))
  // <<< CUT cut-list-cards

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
