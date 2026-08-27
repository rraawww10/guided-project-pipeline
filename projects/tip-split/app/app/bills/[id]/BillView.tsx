'use client'

import Link from 'next/link'
import { useState } from 'react'

import { formatRupees, splitPaise, tipPaise } from '@/lib/money'
import type { Bill } from '@/lib/types'

import styles from './bill.module.css'

export default function BillView({ bill }: { bill: Bill }) {
  const [people, setPeople] = useState<number>(bill.people)

  function setPeopleClamped(requested: number): void {
    // >>> CUT cut-bill-people
    setPeople(Math.min(20, Math.max(1, requested)))
    // <<< CUT cut-bill-people
  }

  const grandTotalPaise = bill.totalPaise + tipPaise(bill.totalPaise, bill.tipPercent)

  let shares: number[] = []

  // >>> CUT cut-bill-shares
  shares = splitPaise(grandTotalPaise, people)
  // <<< CUT cut-bill-shares

  return (
    <>
      <h1 className={styles.place} data-testid="bill-place">
        {bill.place}
      </h1>
      <p className={styles.date} data-testid="bill-date">
        {bill.date}
      </p>

      <div className={styles.figures}>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>Bill</span>
          <span data-testid="bill-total">{formatRupees(bill.totalPaise)}</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>Tip</span>
          <span data-testid="bill-tip-percent">{bill.tipPercent}%</span>
        </div>
        <div className={styles.figure}>
          <span className={styles.figureLabel}>Tip amount</span>
          <span data-testid="bill-tip-amount">{formatRupees(tipPaise(bill.totalPaise, bill.tipPercent))}</span>
        </div>
        <div className={`${styles.figure} ${styles.grandTotal}`}>
          <span className={styles.figureLabel}>Total with tip</span>
          <span data-testid="bill-grand-total">{formatRupees(grandTotalPaise)}</span>
        </div>
      </div>

      <p className={styles.savedPeople} data-testid="bill-saved-people">
        Split {bill.people} ways when saved
      </p>

      <div className={styles.stepper}>
        <button
          type="button"
          className={styles.stepperButton}
          aria-label="Fewer people"
          onClick={() => setPeopleClamped(people - 1)}
        >
          -
        </button>
        <span className={styles.peopleCount} data-testid="people-count">
          {people}
        </span>
        <button
          type="button"
          className={styles.stepperButton}
          aria-label="More people"
          onClick={() => setPeopleClamped(people + 1)}
        >
          +
        </button>
      </div>

      {shares.length > 0 && (
        <>
          <h2 className={styles.sharesHeading}>What each person owes</h2>
          <ul className={styles.shares}>
            {shares.map((share, index) => (
              <li className={styles.shareRow} data-testid="share-row" key={index}>
                Person {index + 1} {formatRupees(share)}
              </li>
            ))}
          </ul>
        </>
      )}

      <Link href="/" className={styles.back}>
        Back to saved bills
      </Link>
    </>
  )
}
