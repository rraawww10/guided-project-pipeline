'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'

import type { Bill } from '@/lib/types'

import BillView from './BillView'
import styles from './bill.module.css'

export default function BillPage() {
  const { id } = useParams<{ id: string }>()
  const [bill, setBill] = useState<Bill | null>(null)
  const [status, setStatus] = useState<'loading' | 'loaded' | 'not-found'>('loading')

  useEffect(() => {
    // TODO(cut-bill-fetch): Ask the endpoint for the bill named in the route; on a 200 reply put the bill into state and move the status to loaded, and on a 404 reply move the status to not-found.
  }, [id])

  return (
    <main className={styles.page}>
      {status === 'loading' && <p className={styles.loading}>Loading bill</p>}
      {status === 'not-found' && (
        <>
          <p className={styles.notFound}>Bill not found</p>
          <Link href="/" className={styles.back}>
            Back to saved bills
          </Link>
        </>
      )}
      {status === 'loaded' && bill !== null && <BillView bill={bill} />}
    </main>
  )
}
